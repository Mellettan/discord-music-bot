import discord
from discord.ext import commands
from loguru import logger

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
logger.info("Бот создан.")
queue: list[list] = []