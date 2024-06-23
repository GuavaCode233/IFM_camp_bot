from nextcord.ext import commands
import nextcord as ntd

import os

# Globals
bot = commands.Bot(
    command_prefix=";",
    intents=ntd.Intents.all()
)

# def set_game_config(self):
#         """如果正式開始遊戲(非維護模式)，需將初始常數設為對應的值。

#         正式狀態的常數值:
#             - NEW_GAME
#                 開始設為`True`直到所有Cogs初始化變回False。
#             - RESET_UI
#                 `True`。
#             - CLEAR_LOG
#                 開始設為`True`直到清除所有資料變回False。
#             - UPDATE_ASSET
#                 `True`
#             - RELEASE_NEWS
#                 `True`
#             - STARTER_CASH
#                 `10_000`
#         """

#         self.CONFIG['NEW_GAME'] = True
#         self.CONFIG['RESET_UI'] = True
#         self.CONFIG['CLEAR_LOG'] = True
#         self.CONFIG['UPDATE_ASSET'] = True
#         self.CONFIG['RELEASE_NEWS'] = True
#         self.CONFIG['STARTER_CASH'] = 10_000

#         access_file.save_to("game_config", self.CONFIG)


@bot.event
async def on_ready():
    print("Bot running!")
    bot_status = ntd.Activity(
        name="理財大富翁",
        type=ntd.ActivityType.playing,
    )
    await bot.change_presence(activity=bot_status)  


for file_name in os.listdir(".\\Cogs"):     # load Cogs
    if(file_name.endswith(".py")):
        bot.load_extension(f"Cogs.{file_name[:-3]}")

if(__name__ == "__main__"):
    bot.run(os.environ.get("TOKEN"))
