import asyncio
import urllib.parse
import discord
import requests
import yt_dlp as youtube_dl
from loguru import logger
from logger_hider import LoggerHider
from loader import bot, queue
from yandex_music import Client
import os
from dotenv import load_dotenv

load_dotenv()
YANDEX_TOKEN = os.getenv('YANDEX_TOKEN')
client = Client(YANDEX_TOKEN).init()


async def check_queue(interaction: discord.Interaction):
    """
    Функция для проверки очереди.
    """
    logger.info("Запуск функции проверки очереди.")
    if len(queue) > 0:
        voice_channel = interaction.guild.voice_client
        if not voice_channel.is_playing():
            source, name = queue.pop(0)
            await play_music(interaction, source, name)


async def play_music(interaction: discord.Interaction, source: str, name: str):
    """
    Функция для воспроизведения музыки в голосовом канале Discord.

    :param interaction: Объект взаимодействия.
    :param source: Источник музыки.
    :param name: Название музыки.
    """

    logger.info(f"Запуск функции проигрывания {name}")

    try:
        voice_channel = interaction.guild.voice_client
        voice_channel.play(
            discord.FFmpegPCMAudio(source,
                                   before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                                   options='-vn -bufsize 1024k'),
            after=lambda i: asyncio.run_coroutine_threadsafe(check_queue(interaction), bot.loop))
        await interaction.guild.get_channel(interaction.channel.id).send(f"Воспроизведение: {name}", silent=True)
    except Exception as e:
        logger.error(f"Ошибка при проигрывании аудио: {e}")


def get_source_and_name(url: str, playlist_index: int = None) -> tuple[str, str]:
    """
    Функция для получения источника и названия музыки из URL.

    :param playlist_index: Номер песни в плейлисте.
    :param url: Ссылка на музыку.
    :return: Источник и название музыки.
    """
    logger.info(f"Запуск функции конвертации: {url}")
    if 'yandex' in url:
        if 'playlists' in url and 'users' in url:
            try:
                if playlist_index:
                    parsed_url = urllib.parse.urlparse(url)
                    path_parts = parsed_url.path.split("/")
                    user_id = path_parts[2]
                    kind = path_parts[4]
                    playlist = client.users_playlists(kind=kind, user_id=user_id)
                    track = playlist.tracks[playlist_index - 1].fetch_track()
                    track_info = track.get_download_info(get_direct_links=True)
                    audio_url, audio_name = track_info[0]['direct_link'], track['artists'][0]['name'] + ' - ' + track['title']
                else:
                    parsed_url = urllib.parse.urlparse(url)
                    path_parts = parsed_url.path.split("/")
                    user_id = path_parts[2]
                    kind = path_parts[4]
                    playlist = client.users_playlists(kind=kind, user_id=user_id)
                    track = playlist.tracks[0].fetch_track()
                    track_info = track.get_download_info(get_direct_links=True)
                    audio_url, audio_name = track_info[0]['direct_link'], track['artists'][0]['name'] + ' - ' + track['title']
            except IndexError as e:
                raise IndexError
            except Exception as e:
                logger.error(f"Ошибка при конвертировании URL яндекс плейлиста: {e}")
        elif 'album' in url and 'track' not in url:
            try:
                if playlist_index:
                    parsed_url = urllib.parse.urlparse(url)
                    path_parts = parsed_url.path.split("/")
                    album_id = path_parts[2]
                    album = client.albums_with_tracks(album_id)
                    track = album.volumes[0][playlist_index - 1]
                    track_info = track.get_download_info(get_direct_links=True)
                    audio_url, audio_name = track_info[0]['direct_link'], track['artists'][0]['name'] + ' - ' + track['title']
                else:
                    parsed_url = urllib.parse.urlparse(url)
                    path_parts = parsed_url.path.split("/")
                    album_id = path_parts[2]
                    album = client.albums_with_tracks(album_id)
                    track = album.volumes[0][0]
                    track_info = track.get_download_info(get_direct_links=True)
                    audio_url, audio_name = track_info[0]['direct_link'], track['artists'][0]['name'] + ' - ' + track['title']
            except Exception as e:
                logger.error(f"Ошибка при конвертировании URL яндекс альбома: {e}")
        else:
            try:
                parsed_url = urllib.parse.urlparse(url)
                path_parts = parsed_url.path.split("/")
                track_id = path_parts[4]
                track = client.tracks(track_id)[0]
                track_info = track.get_download_info(get_direct_links=True)
                audio_url, audio_name = track_info[0]['direct_link'], track['artists'][0]['name'] + ' - ' + track['title']
            except Exception as e:
                logger.error(f"Ошибка при конвертировании URL яндекс трека: {e}")
    else:
        try:
            if playlist_index:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'playlist_items': str(playlist_index),
                    'logger': LoggerHider()
                }
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    audio_url = info['entries'][0]['url']
                    audio_name = info['entries'][0]['fulltitle']
            else:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'logger': LoggerHider()
                }
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    audio_url = info['url']
                    audio_name = info['fulltitle']
        except Exception as e:
            logger.error(f"Ошибка при конвертировании URL ютуб: {e}")

    return audio_url, audio_name  # noqa


async def append_playlist_to_queue(interaction: discord.Interaction, url: str) -> None:
    """
    Функция для добавления плейлиста в очередь, начиная со второй песни

    :param interaction: Объект взаимодействия.
    :param url: Ссылка на плейлист.
    """
    logger.info(f"Запуск функции добавления плейлиста в очередь, начиная со второй песни: {url}")
    for i in range(2, 61):
        try:
            source, name = await asyncio.get_event_loop().run_in_executor(None, lambda: get_source_and_name(url, i))
            logger.info(f"Добавление в очередь {name}")
            queue.append([source, name])
            await interaction.guild.get_channel(interaction.channel.id).send(f"Добавление в очередь: {name}",
                                                                             silent=True)
        except IndexError:
            logger.warning(f"Недостаточно песен в плейлисте: {url}. Прерывание.")
            break
        except Exception as e:
            logger.error(f"Ошибка при добавлении {i}-й песни в очередь: {e}")


async def handle_playing_one_song(interaction: discord.Interaction, url: str) -> None:
    """
    Функция для обработки воспроизведения одной песни.

    :param interaction: Объект взаимодействия.
    :param url: Ссылка на музыку.
    """
    logger.info(f"Запуск функции обработки воспроизведения одной песни: {url}")
    voice_channel = interaction.guild.voice_client
    if voice_channel.is_playing():
        source, name = get_source_and_name(url)
        logger.info(f"Добавление в очередь {name}")
        queue.append([source, name])
        await interaction.guild.get_channel(interaction.channel.id).send(f"Песня '{name}' добавлена в очередь.",
                                                                         silent=True)
    else:
        source, name = get_source_and_name(url)
        await interaction.guild.get_channel(interaction.channel.id).send(f"Песня '{name}' добавлена в очередь.",
                                                                         silent=True)
        await play_music(interaction, source, name)


async def search_video_by_title(title: str):
    search_query = urllib.parse.urlencode({'search_query': title})
    url = f"https://www.youtube.com/results?{search_query}"
    response = requests.get(url)
    if response.status_code == 200:
        # Находим первую ссылку на видео из результатов поиска
        start = response.text.find('/watch?v=')
        end = response.text.find('"', start)
        video_id = response.text[start:end]
        return f"https://www.youtube.com{video_id}".replace("\\u0026", "&")
    else:
        return None


@bot.tree.command()
async def play(interaction: discord.Interaction, item: str) -> None:
    """
    Добавляет музыку в очередь. Если очередь пустая, то запускает воспроизведение.

    Parameters
    ----------
    interaction : discord.Interaction
        Объект взаимодействия.
    item : str
        Ссылка или название песни.
    """
    logger.info(f"Команда /play принята")
    try:
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
            if '&list=' in item or 'yandex' in item and 'track' not in item:
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
            try:
                url = await search_video_by_title(item)
                await interaction.response.send_message("Песня принята!")
                await handle_playing_one_song(interaction, url)
            except Exception as e:
                logger.error(f"Произошла ошибка при поиске видео по названию: {e}")
                await interaction.response.send_message(f"Произошла ошибка при поиске видео по названию: {e[:23]}...")
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        await interaction.response.send_message(f"Что-то пошло не так...")
