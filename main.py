import discord
from loguru import logger
from loader import bot
import handlers # noqa - устанавливает команды
import os
from dotenv import load_dotenv


@bot.event
async def on_ready() -> None:
    """
    Срабатывает при запуске бота. Синхронизирует команды бота с сервером.
    """
    logger.info("Бот запущен.")
    logger.debug(f"ID сервера: {bot.guilds[0].id}")
    logger.debug("Список команд: " + ', '.join([command.name for command in bot.tree.get_commands()]))
    bot.tree.copy_global_to(guild=discord.Object(id=1223275744008867972))
    await bot.tree.sync(guild=discord.Object(id=1223275744008867972))

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')
    bot.run(TOKEN, log_handler=None)
