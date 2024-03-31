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

# Load cog (owner only)
@bot.command()
@commands.is_owner()
async def load(ctx: commands.Context, extension: str):
    bot.load_extension(f"Cogs.{extension}")
    await ctx.send(f"Loaded **{extension}**!")

# Unload cog (owner only)
@bot.command()
@commands.is_owner()
async def unload(ctx: commands.Context, extension: str):
    bot.unload_extension(f"Cogs.{extension}")
    await ctx.send(f"Unloaded **{extension}**!")

# Reload cog (owner only)
@bot.command()
@commands.is_owner()
async def reload(ctx: commands.Context, extension: str):
    bot.reload_extension(f"Cogs.{extension}")   
    await ctx.send(f"Reloaded **{extension}**!")


for file_name in os.listdir(".\\Cogs"):     # load Cogs
    if(file_name.endswith(".py") and not
       file_name.startswith("mod")):
        bot.load_extension(f"Cogs.{file_name[:-3]}")

if(__name__ == "__main__"):
    bot.run(os.environ.get("TOKEN"))