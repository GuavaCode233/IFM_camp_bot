from nextcord.ext import commands, tasks

from .utilities import access_file
from .utilities.datatypes import Config, GameState

import os


class StartupSequence(commands.Cog):
    
    __slots__ = ("bot", "CONFIG")

    CHECKING_FREQUENCY: float = 10.0    # 檢查Cogs運行狀態頻率(秒)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Config = access_file.read_file("game_config")
        self.game_state: GameState = access_file.read_file("game_state")

    def set_game_config(self):
        """如果正式開始遊戲(非維護模式)，需將初始常數設為對應的值。

        正式狀態的常數值:
            - NEW_GAME
                開始設為`True`直到所有Cogs初始化變回False。
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

        self.CONFIG['NEW_GAME'] = True
        self.CONFIG['RESET_UI'] = True
        self.CONFIG['CLEAR_LOG'] = True
        self.CONFIG['UPDATE_ASSET'] = True
        self.CONFIG['RELEASE_NEWS'] = True
        self.CONFIG['STARTER_CASH'] = 10_000

        access_file.save_to("game_config", self.CONFIG)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Startup sequence started")
        IS_MAINTENANCE = self.CONFIG['MAINTENANCE']
        print(f"Maintenence Mode: {IS_MAINTENANCE}")

        if(not IS_MAINTENANCE):
            self.set_game_config()

        self.check_cogs_state_loop.start()
        for file_name in os.listdir(".\\Cogs"):     # load Cogs
            if(file_name.endswith(".py")):
                self.bot.load_extension(f"Cogs.{file_name[:-3]}")
    
    @tasks.loop(seconds=CHECKING_FREQUENCY)
    async def check_cogs_state_loop(self):
        pass

    @check_cogs_state_loop.before_loop
    async def before_check_cogs_state_loop(self):
        print("Waiting for Cogs to load...")
        await self.bot.wait_until_ready()




def setup(bot: commands.Bot):
    bot.add_cog(StartupSequence(bot))