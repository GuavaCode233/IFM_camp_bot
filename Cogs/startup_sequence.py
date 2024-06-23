from nextcord.ext import commands, tasks

from typing import Dict

from .utilities import access_file
from .utilities.datatypes import Config, GameState

import os


class StartupSequence(commands.Cog):
    
    __slots__ = ("bot", "CONFIG", "IS_MAINTENANCE", "cogs_state")

    CHECKING_FREQUENCY: float = 10.0    # 檢查Cogs運行狀態頻率(秒)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Config = access_file.read_file("game_config")
        self.IS_MAINTENANCE = self.CONFIG['MAINTENANCE']
        self.cogs_state: Dict[str, bool] = { # 各Cog運行狀態表
            "AssetsManager": False,
            "StockManager": False,
            "DiscordUI": False
        }

    

    @commands.Cog.listener()
    async def on_ready(self):
        print("Startup sequence started")
        print(f"Maintenence Mode: {self.IS_MAINTENANCE}")

        if(not self.IS_MAINTENANCE):
            self.set_game_config()
        
        self.check_cogs_state_loop.start()
        print("Waiting for Cogs to load...")
        for file_name in os.listdir(".\\Cogs"):     # load Cogs
            if(file_name.endswith(".py") and (file_name != "startup_sequence.py")):
                self.bot.load_extension(f"Cogs.{file_name[:-3]}")
                print("hi")

    
    @tasks.loop(seconds=CHECKING_FREQUENCY)
    async def check_cogs_state_loop(self):
        """檢查所有Cogs都在運行。
        """

        if(not all(self.cogs_state.values())):
            return
        
        if(not self.IS_MAINTENANCE):
            # 將`NEW_GAME`及`CLEAR_LOG`設為`False`
            self.CONFIG["NEW_GAME"] = False
            self.CONFIG["CLEAR_LOG"] = False
        
        print("All Cogs loaded \n Startup sequence finished")
        self.check_cogs_state_loop.stop()
        self.bot.unload_extension("startup_sequence")

def setup(bot: commands.Bot):
    bot.add_cog(StartupSequence(bot))