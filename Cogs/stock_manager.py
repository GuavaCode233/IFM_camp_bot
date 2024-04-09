from nextcord.ext import commands
import nextcord as ntd

from .utilities import AccessFile


class StockManager(commands.Cog):
    """控制股票。
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    def on_ready(self):
        print("Loaded stock_manager.py")


def setup(bot: commands.Bot):
    bot.add_cog(StockManager(bot))