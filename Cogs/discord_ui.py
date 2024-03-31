from nextcord.ext import commands

from .utilities import AccessFile
from .assets_manager import AssetsManager


class DiscordUI(commands.Cog, AccessFile):
    """控制Discord端的UI介面
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #連結Cog方法
    @commands.command()
    async def inter_com(self, ctx: commands.Context):
        assets: AssetsManager = self.bot.get_cog("AssetsManager") # return type: <class 'Cogs.main_bot.AssetsManager'>
        print(assets.team_assets[0].deposit)  # 可提示子class方便撰寫

    async def resend_assets_ui(self):
        """|coro|

        刪除舊的資產訊息並重新發送。
        """
        pass
    
    async def update_assets(self):
        """|coro|

        任一操作改變資產時更新所有小隊資產訊息。
        """
        pass


def setup(bot: commands.Bot):
    bot.add_cog(DiscordUI(bot))