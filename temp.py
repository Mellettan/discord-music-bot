import discord
from loguru import logger

from loader import bot

logger.debug(bot.get_channel(1223275744730550275))
channel = discord.utils.get(bot.get_guild(1223275744008867972).text_channels, name='music_control')
try:
    logger.info("Команда /ping принята.")
    channel.send(f"Пинг: {round(bot.latency * 1000)} мc.")
except Exception as e:
    logger.error(f"Что-то пошло не так: {e}")
    channel.send(f"Что-то пошло не так...")

