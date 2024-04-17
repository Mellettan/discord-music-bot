from loguru import logger
import discord
from loader import bot, queue


@bot.tree.command()
async def skip(interaction: discord.Interaction):
    """
    Пропускает текущую песню.

    Parameters
    ----------
    interaction : discord.Interaction
        Объект взаимодействия.
    """
    try:
        voice_channel = interaction.guild.voice_client
        if voice_channel.is_playing():
            if queue:
                voice_channel.stop()
                logger.info(f"Пропуск песни.")
                await interaction.response.send_message("Песня пропущена.")
            else:
                voice_channel.stop()
                logger.info("Воспроизведение завершено.")
                await interaction.response.send_message("Воспроизведение завершено.")
        else:
            logger.info("Нечего пропускать")
            await interaction.response.send_message("Нечего скипать.")
    except Exception as e:
        logger.error(f"Что-то пошло не так: {e}")
        await interaction.response.send_message(f"Что-то пошло не так...")
