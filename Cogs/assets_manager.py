from nextcord.ext import commands, application_checks
import nextcord as ntd

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from pprint import pprint

from .utilities import AccessFile


@dataclass(kw_only=True, slots=True)
class TeamAssets:
    """儲存小隊資產。
    包括「小隊編號」、「資產總額」、「存款總額」。
    """

    team_number: str
    deposit: int
    stock_cost: int
    stocks: Dict[str, str] = field(default_factory=dict)
    revenue: int = 0


class AssetsManager(commands.Cog, AccessFile):
    """資產控制。
    """
    
    __slots__ = (
        "bot",
        "CONFIG",
        "team_assets"
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Dict[str, Any] = self.read_file("game_config")
        self.team_assets: List[TeamAssets] = None    # 儲存各小隊資產

    @commands.Cog.listener()
    async def on_ready(self):
        """AssetManager啟動程序。
        
        `NEW_GAME`
        清除全部小隊資產資料並重創銀行帳戶，
        如果資料有遺失，重新抓取資產資料。
        """

        NEW_GAME: bool = self.CONFIG["NEW_GAME"]
        if(NEW_GAME):   # 開新遊戲
            self.reset_asset_data()
        elif(self.team_assets is None): # 資料不對等
            self.fetch_assets()
        
        print("Loaded asset_manager")
        
    def reset_asset_data(self):
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

        asset: Dict[str, Dict[str, Any]] = self.read_file("team_assets")
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
            d: Dict[str, Dict[str, Any]] = self.read_file("team_assets")
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
    
    def update_deposit(
            self,
            *,
            team: int,
            mode: str,  # "1": deposit, "2": withdraw, "3": change
            amount: int,
            user: str
    ):
        """更新小隊存款額並記錄log。
        """
        
        original = self.team_assets[team-1].deposit # 原餘額

        if(mode == "1"):
            self.team_assets[team-1].deposit += amount
        elif(mode == "2"):
            self.team_assets[team-1].deposit -= amount
        elif(mode == "3"):
            self.team_assets[team-1].deposit = amount
        
        # 儲存紀錄
        self.log(
            type_="AssetUpdate",
            time=datetime.now(),
            user=user,
            team=str(team),
            original=original,
            updated=self.team_assets[team-1].deposit
        )
        # 儲存資料
        self.save_asset(team)
        

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
        interaction: ntd.Interaction,
        team: int = ntd.SlashOption(
            name="小隊",
            description="輸入小隊阿拉伯數字",
            choices={str(t):t for t in range(1, 9)}
        ),
        amount: int = ntd.SlashOption(
            name="改變金額",
            description="輸入金額阿拉伯數字(可為負數)",
        )
    ):
        """用指令改變指定小隊存款額。
        """
        
        self.update_deposit(
            team=team,
            mode="1",
            amount=amount,
            user=interaction.user.display_name
        )
        # update_asset_ui 更新資產ui顯示
        await interaction.response.send_message(
            "**改變成功!!!**",
            delete_after=3,
            ephemeral=True
        )


def setup(bot: commands.Bot):
    bot.add_cog(AssetsManager(bot))