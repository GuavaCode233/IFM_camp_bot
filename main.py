from nextcord.ext import commands
import nextcord as ntd

from Cogs.utilities import access_file
from Cogs.utilities.datatypes import Config

import os


bot = commands.Bot(
    command_prefix=";",
    intents=ntd.Intents.all()
)
CONFIG: Config = access_file.read_file("game_config")
IS_MAINTENANCE: bool = CONFIG["MAINTENANCE"]


def set_game_config():
        """如果正式開始遊戲(非維護模式)，需將初始常數設為對應的值。

        正式狀態的常數值:
        - RESET_ALL
            開始設為`True`直到所有Cogs初始化變回`False`。
        - RESET_UI
            `True`。
        - CLEAR_LOG
            開始設為`True`直到清除所有資料變回False。
        - UPDATE_ASSET
            `True`
        - RELEASE_NEWS
            `True`
        - STARTER_CASH
            `10_000`
        """

        CONFIG["RESET_ALL"] = False if CONFIG["IN_GAME"] else True
        CONFIG["RESET_UI"] = True
        CONFIG["CLEAR_LOG"] = True
        CONFIG["UPDATE_ASSET"] = True
        CONFIG["RELEASE_NEWS"] = True
        CONFIG["STARTER_CASH"] = 10_000

        access_file.save_to("game_config", CONFIG)


@bot.event
async def on_ready():
    print("Bot running.")
    print(f"Maintenance Mode: {IS_MAINTENANCE}")
    print("Waiting for Cogs to load...")
    if(IS_MAINTENANCE):
        bot_status = ntd.Activity(
            name="歐給維護模式",
            type=ntd.ActivityType.playing,
        )
    else:
        bot_status = ntd.Activity(
            name="理財大富翁",
            type=ntd.ActivityType.playing,
        )
    await bot.change_presence(activity=bot_status)  


def main():
    
    if(IS_MAINTENANCE):
        CONFIG["IN_GAME"] = False
        CONFIG["RESET_ALL"] = True
        CONFIG["CLEAR_LOG"] = True
    else:
        set_game_config()
        CONFIG["IN_GAME"] = True

    for file_name in os.listdir(".\\Cogs"):     # Load Cogs
        if(file_name.endswith(".py")):
            bot.load_extension(f"Cogs.{file_name[:-3]}")

    if(CONFIG["IN_GAME"]):
        # 正式開始遊戲
        # 將`CLEAR_LOG`設為`False`，`IN_GAME`設為`True`
        CONFIG["CLEAR_LOG"] = False
        CONFIG["RESET_ALL"] = False
    
    access_file.save_to("game_config", CONFIG)

    bot.run(os.environ.get("TOKEN"))

if(__name__ == "__main__"):
    main()
