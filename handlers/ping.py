from loguru import logger
import discord
from loader import bot


@bot.tree.command()
async def ping(interaction: discord.Interaction) -> None:
    """
    Проверка соединения с сервером.

    Parameters
    ----------
    interaction : discord.Interaction
        Объект взаимодействия.
    """
    try:
        logger.info("Команда /ping принята.")
        channels = bot.voice_clients[0].channel
        logger.debug(channels)
        await interaction.response.send_message(f"Пинг: {round(bot.latency * 1000)} мc.")
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        await interaction.response.send_message(f"Что-то пошло не так...")

