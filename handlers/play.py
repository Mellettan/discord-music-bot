import asyncio
import urllib.parse
from typing import Optional

import discord
import requests
import yt_dlp as youtube_dl
from loguru import logger
from loader import bot, queue
from yandex_music import Client
import os
from dotenv import load_dotenv

from logger_hider import LoggerHider

load_dotenv()
YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')
client = Client(YANDEX_TOKEN).init()


async def check_queue(interaction: discord.Interaction):
    """
    Проверка очереди и воспроизведение следующей песни.
    """
    logger.info("Запуск функции проверки очереди.")
    if queue:
        voice_channel = interaction.guild.voice_client
        if not voice_channel.is_playing():
            source, name = queue.pop(0)
            await play_music(interaction, source, name)


async def play_music(interaction: discord.Interaction, source: str, name: str):
    """
    Воспроизведение музыки в голосовом канале Discord.
    """
    logger.info(f"Запуск функции проигрывания {name}")

    try:
        voice_channel = interaction.guild.voice_client
        voice_channel.play(
            discord.FFmpegPCMAudio(source,
                                   before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                   options='-vn -bufsize 1024k'),
            after=lambda _: asyncio.run_coroutine_threadsafe(check_queue(interaction), bot.loop)
        )
        await interaction.channel.send(f"Воспроизведение: {name}", silent=True)
    except Exception as e:
        logger.error(f"Ошибка при проигрывании аудио: {e}")


def get_source_and_name(url: str, playlist_index: int = None) -> Optional[tuple[str, str]]:
    """
    Получение источника и названия музыки из URL.
    """
    logger.info(f"Запуск функции конвертации: {url}, песня №{playlist_index if playlist_index else 1}")

    def get_yandex_track_info(track):
        track_info = track.get_download_info(get_direct_links=True)
        return track_info[0]['direct_link'], f"{track['artists'][0]['name']} - {track['title']}"

    try:
        if 'yandex' in url:
            parsed_url = urllib.parse.urlparse(url)
            path_parts = parsed_url.path.split("/")

            if 'playlists' in url:
                user_id, kind = path_parts[2], path_parts[4]
                playlist = client.users_playlists(kind=kind, user_id=user_id)
                track = playlist.tracks[playlist_index - 1 if playlist_index else 0].fetch_track()
                return get_yandex_track_info(track)
            elif 'album' in url:
                album_id = path_parts[2]
                album = client.albums_with_tracks(album_id)
                track = album.volumes[0][playlist_index - 1 if playlist_index else 0]
                return get_yandex_track_info(track)
            else:
                track_id = path_parts[4]
                track = client.tracks(track_id)[0]
                return get_yandex_track_info(track)
        else:
            ydl_opts = {'format': 'bestaudio/best', 'logger': LoggerHider()}
            if playlist_index:
                ydl_opts['playlist_items'] = str(playlist_index)

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                entry = info if 'entries' not in info else info['entries'][0]
                return entry['url'], entry['fulltitle']
    except Exception as e:
        logger.error(f"Ошибка при конвертировании URL: {e}")
        return None


async def append_playlist_to_queue(interaction: discord.Interaction, url: str) -> None:
    """
    Добавление плейлиста в очередь.
    """
    logger.info(f"Запуск функции добавления плейлиста в очередь: {url}")
    for i in range(2, 31):
        try:
            source, name = await asyncio.to_thread(get_source_and_name, url, i)
            if source and name:
                logger.info(f"Добавление в очередь {name}")
                queue.append([source, name])
                await interaction.channel.send(f"Добавление в очередь: {name}", silent=True)
            else:
                break
        except Exception as e:
            logger.error(f"Ошибка при добавлении {i}-й песни в очередь: {e}")
            break


async def handle_playing_one_song(interaction: discord.Interaction, url: str) -> None:
    """
    Обработка воспроизведения одной песни.
    """
    logger.info(f"Запуск функции обработки воспроизведения одной песни: {url}")
    voice_channel = interaction.guild.voice_client
    source, name = get_source_and_name(url)

    if voice_channel.is_playing():
        logger.info(f"Добавление в очередь {name}")
        queue.append([source, name])
    else:
        await play_music(interaction, source, name)

    await interaction.channel.send(f"Песня '{name}' добавлена в очередь.", silent=True)


async def search_video_by_title(title: str):  # Корутина с блокирующим вызовом, однако её параллельное выполнение не подразумевается
    """
    Поиск видео на YouTube по названию.
    """
    search_query = urllib.parse.urlencode({'search_query': title})
    url = f"https://www.youtube.com/results?{search_query}"
    response = requests.get(url)

    if response.status_code == 200:
        start = response.text.find('/watch?v=')
        end = response.text.find('"', start)
        video_id = response.text[start:end]
        return f"https://www.youtube.com{video_id}".replace("\\u0026", "&")
    else:
        return None


@bot.tree.command()
async def play(interaction: discord.Interaction, item: str) -> None:
    """
    Добавление музыки в очередь и запуск воспроизведения.
    """
    logger.info(f"Команда /play принята")

    try:
        channel = interaction.user.voice.channel
    except AttributeError:
        logger.warning("Запуск бота не в голосовом канале.")
        await interaction.response.send_message("Вы должны быть в голосовом канале!")
        return

    voice_channel = interaction.guild.voice_client
    if not voice_channel:
        await channel.connect()
        logger.info(f"Подключение к голосовому каналу: {channel}")
    elif voice_channel.channel != channel:
        logger.warning("Бот уже находится в другом голосовом канале.")
        await interaction.response.send_message("Я уже в другом голосовом канале!")
        return

    if item.startswith("https://") or item.startswith("http://"):
        if '&list=' in item or ('yandex' in item and 'track' not in item):
            logger.info(f"Подача на вход плейлиста: {item}")
            await interaction.response.send_message("Плейлист принят!")
            if 'yandex' in item:
                await handle_playing_one_song(interaction, item)
            else:
                await handle_playing_one_song(interaction, item[:item.index('&list=')])
            await append_playlist_to_queue(interaction, item)
        else:
            logger.info(f"Подача на вход песни: {item}")
            await interaction.response.send_message("Песня принята!")
            await handle_playing_one_song(interaction, item)
    else:
        logger.info(f"Подача на вход названия песни: {item}")
        url = await search_video_by_title(item)
        if url:
            await interaction.response.send_message("Песня принята!")
            await handle_playing_one_song(interaction, url)
        else:
            await interaction.response.send_message("Произошла ошибка при поиске видео по названию.")
