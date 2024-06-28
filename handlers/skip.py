from loguru import logger
import discord
from loader import bot, queue


@bot.tree.command()
async def skip(interaction: discord.Interaction, amount: int = 1) -> None:
    """
    Пропускает текущую песню.

    Parameters
    ----------
    interaction : discord.Interaction
        Объект взаимодействия.

    amount: int
        Количество пропускаемых песен.
    """
    try:
        voice_channel = interaction.guild.voice_client
        if not voice_channel.is_playing():
            logger.info("Нечего пропускать")
            await interaction.response.send_message("Нечего скипать.")
            return

        if queue:
            skipped_songs = []
            for _ in range(amount - 1):  # Сама остановка песни уже пропускает её, так что счетчик уменьшаем на 1
                if queue:
                    skipped_songs.append(queue.pop(0))
                else:
                    break
            voice_channel.stop()
            logger.info(f"Пропущено {len(skipped_songs) + 1} песен.")
            await interaction.response.send_message(f"Пропущено {len(skipped_songs) + 1} песен.")
        else:
            voice_channel.stop()
            logger.info("Воспроизведение завершено.")
            await interaction.response.send_message("Воспроизведение завершено.")
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        await interaction.response.send_message(f"Что-то пошло не так...")
