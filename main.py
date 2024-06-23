from nextcord.ext import commands
import nextcord as ntd

import os

# Globals
bot = commands.Bot(
    command_prefix=";",
    intents=ntd.Intents.all()
)

@bot.event
async def on_ready():
    print("Bot running!")
    bot_status = ntd.Activity(
        name="理財大富翁",
        type=ntd.ActivityType.playing,
    )
    await bot.change_presence(activity=bot_status)  


bot.load_extension(f"Cogs.startup_sequence")    # Startup


if(__name__ == "__main__"):
    bot.run(os.environ.get("TOKEN"))
