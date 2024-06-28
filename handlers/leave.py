from loguru import logger
import discord
from loader import bot, queue


@bot.tree.command()
async def leave(interaction: discord.Interaction) -> None:
    """
    Отключает бота от голосового канала.

    Parameters
    ----------
    interaction : discord.Interaction
        Объект взаимодействия.
    """
    try:
        voice_channel = interaction.guild.voice_client
        if voice_channel:
            voice_channel.stop()
            queue.clear()
            await voice_channel.disconnect()
            logger.info("Воспроизведение завершено.")
            logger.info("Очередь очищена.")
            await interaction.response.send_message("Я ливаю...")
        else:
            logger.info("Бот не в голосовом канале.")
            await interaction.response.send_message("Я итак не в голосовом канале.")
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        await interaction.response.send_message(f"Что-то пошло не так...")
