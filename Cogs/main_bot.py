"""主要功能，包含所有application commands
"""
from nextcord.ext import commands, application_checks
from nextcord.interactions import Interaction
from nextcord.ui import View, Button
from nextcord import ApplicationCheckFailure, SlashOption
import nextcord as ntd

from typing import List, Dict, Any
import os
import json
import asyncio
from pprint import pprint


# class TeamDepositView(View):
#     """小隊收支按鈕
#     """

#     @ntd.ui.button(label="加錢", style=ntd.ButtonStyle.green, emoji="➕")
#     async def deposit_button_callback(self, button: Button, interaction: Interaction):
#         await interaction.response.send_message("加錢啦", ephemeral=True, delete_after=3)

#     @ntd.ui.button(label="扣錢", style=ntd.ButtonStyle.red, emoji="➖")
#     async def withdraw_button_callback(self, button: Button, interaction: Interaction):
#         await interaction.response.send_message("扣錢啦", ephemeral=True, delete_after=3)

#     @ntd.ui.button(label="更改餘額", style=ntd.ButtonStyle.gray, emoji="🔑")
#     async def change_button_callback(self, button: Button, interaction: Interaction):
#         await interaction.response.send_message("改餘額", ephemeral=True, delete_after=3)
"""
update content
json.dump(json_object, file)
"""

class AccessFile:
    """存取檔案用之母類別。
    """
    @classmethod
    def acc_game_config(cls) -> Dict[str, Any]:
        with open(".\\Data\\game_config.json", "r") as temp_file:
            return json.load(temp_file)

    @classmethod
    def acc_team_assets(cls) -> Dict[str, Dict[str, Any]]:
        with open(".\\Data\\team_assets.json", "r") as temp_file:
            return json.load(temp_file)

    @classmethod
    def save_to(cls, file_name: str, dict_: Dict):
        """開啟指定檔名的檔案並將dict_寫入。

        如果未找到檔案則 raise `FileNotFoundError`。
        """

        file_path = f".\\Data\\{file_name}.json"
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File: '{file_name}' not found.")
        
        with open(
            file_path,
            mode="w",
            encoding="utf-8"
        ) as json_file:
            json.dump(
                dict_, json_file,
                ensure_ascii=False,
                indent=4
            )


class Stock:
    pass


class TeamAssets:
    """儲存小隊資產。
    包括「小隊編號」、「資產總額」、「存款總額」。
    """

    __slots__ = (
        "team_number",
        "deposit",
        "stock_cost",
        "stocks",
        "revenue",
        "total_asset"
    )

    def __init__(
            self,
            team_number: str,
            deposit: int,
            stock_cost: int = None,
            stocks: Dict[str, int] = None,
            revenue: int = 0,
    ):
        self.team_number = team_number
        self.deposit = deposit
        self.stock_cost = stock_cost
        self.stocks = stocks
        self.revenue = revenue
        self.total_asset = deposit


class AssetsManager(commands.Cog, AccessFile):
    """資產控制
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG = self.acc_game_config()
        self.team_assets: List[TeamAssets] = None    # 儲存各小隊資產

    @commands.Cog.listener()
    async def on_ready(self):
        """進行資料檢查。
        
        如果要開啟新遊戲，重整資料。
        如果資料有損失，重新抓取資料。
        """

        NEW_GAME: bool = self.CONFIG["NEW_GAME"]
        if(NEW_GAME):   # 開新遊戲
            self.reset_all_assets()
        elif(self.team_assets is None): # 資料不對等
            self.fetch_assets()
        
    def reset_all_assets(self):
        """清除所有資產資料，重創銀行帳戶。
        """
        
        d = {
            str(t): {
                "deposit": self.CONFIG["STARTER_CASH"],
                "stock_cost": 0,
                "stocks": None,
                "revenue": 0
            }
            for t in range(1, 9)
        }
        self.save_to("team_assets", d)
        self.fetch_assets()
        
    def fetch_assets(self):
        """從team_assets.json中抓取資料並初始化TeamAssets。
        """

        asset = self.acc_team_assets()
        self.team_assets = [
            TeamAssets(
                team_number=str(t),
                deposit=asset[str(t)]["deposit"],
                stock_cost=asset[str(t)]["stock_cost"],
                stocks=asset[str(t)]["stocks"],
                revenue=asset[str(t)]["revenue"]
            )
            for t in range(1, 9)
        ]
        
    def save_asset(self, team_number: str | int | None = None):
        """儲存所有或指定小隊資產資料至json。
        """

        if(team_number is None):    # 儲存所有小隊資料
            d = {}
            for t, asset in enumerate(self.team_assets, start=1):
                d.update(
                    {
                        str(t):{
                            "deposit": asset.deposit,
                            "stock_cost": asset.stock_cost,
                            "stocks": asset.stocks,
                            "revenue": asset.revenue
                        }
                    }
                )
        else:   #　儲存指定小隊資料
            d = self.acc_team_assets()
            asset = self.team_assets[int(team_number)-1]
            d.update(
                {
                    str(team_number):{
                        "deposit": asset.deposit,
                        "stock_cost": asset.stock_cost,
                        "stocks": asset.stocks,
                        "revenue": asset.revenue
                    }
                }
            )

        self.save_to("team_assets", d)
        pprint(d)
        print()

    @ntd.slash_command(
        name="change_deposit",
        description="🛅針對指定小隊改變存款額。",
    )
    @application_checks.has_any_role(
        1218179373522358313,    # 最強大腦活動組
        1218184965435691019     # 大神等級幹部組
    )
    async def change_deposit(
        self,
        interaction: Interaction,
        team: int = SlashOption(
            name="小隊",
            description="輸入小隊阿拉伯數字",
            choices={str(t):t for t in range(1, 9)}
        ),
        amount: int = SlashOption(
            name="改變金額",
            description="輸入金額阿拉伯數字(可為負數)",
        )
    ):
        """用指令改變指定小隊存款額。
        """
        
        self.team_assets[team-1].deposit += amount
        self.save_asset(team)
        # update_asset_ui 更新資產ui顯示
        await interaction.response.send_message(
            "改變成功!!!",
            delete_after=3,
            ephemeral=True
        )

class DiscordUI(commands.Cog, AccessFile):
    """控制Discord端的UI介面
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 連結Cog方法
    # @commands.command()
    # async def inter_com(self, ctx: commands.Context):
    #     assets: AssetsManager = self.bot.get_cog("AssetsManager") # return type: <class 'Cogs.main_bot.AssetsManager'>
    #     print(assets.team_assets[0].deposit)  # 可提示子class方便撰寫

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

class MainBot(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("main_bot Ready!")

    @ntd.slash_command(name="ping", description="Replies Pong!")
    @application_checks.has_any_role(
        1218179373522358313,    # 最強大腦活動組
        1218184965435691019     # 大神等級幹部組
    )
    async def ping(self, interaction: Interaction):
        """Replies Pong!
        """
        await interaction.response.send_message("Pong!")
        # await original_message.edit("ahahah")

    @ntd.slash_command(name="test", description="For general testing.")
    @application_checks.is_owner()
    async def test(
        self,
        interaction: Interaction,
        ):
        """Slash command for general testing.
        """
        await interaction.response.send_message("great!")


    @ping.error
    @test.error
    async def application_command_error_handler(
        self,
        interaction: Interaction,
        error: Exception
    ):
        """Application command error handler.
        """
        if(isinstance(error, ApplicationCheckFailure)):
            await interaction.response.send_message(
                "**你沒有權限使用這個指令!!!**",
                delete_after=3,
                ephemeral=True
            )

    

def setup(bot: commands.Bot):
    bot.add_cog(MainBot(bot))
    bot.add_cog(AssetsManager(bot))
    bot.add_cog(DiscordUI(bot))