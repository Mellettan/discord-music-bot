from loguru import logger
import discord
from loader import bot, queue


@bot.tree.command()
async def stop(interaction: discord.Interaction) -> None:
    """
    Останавливает воспроизведение музыки и очищает очередь.

    Parameters
    ----------
    interaction : discord.Interaction
        Объект взаимодействия.
    """
    try:
        voice_channel = interaction.guild.voice_client
        if voice_channel and voice_channel.is_playing():
            queue.clear()
            voice_channel.stop()
            logger.info("Воспроизведение завершено.")
            logger.info("Очередь очищена.")
            await interaction.response.send_message("Воспроизведение завершено. Очередь очищена.")
        else:
            queue.clear()
            logger.info("Воспроизведение не запущено.")
            logger.info("Очередь очищена.")
            await interaction.response.send_message("Ничего не проигрывается. Очередь очищена.")
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        await interaction.response.send_message(f"Что-то пошло не так...")
