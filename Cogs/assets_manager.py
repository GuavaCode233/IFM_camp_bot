from nextcord.ext import commands, application_checks
import nextcord as ntd

from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime
from pprint import pprint

from .utilities import access_file
from .utilities.datatypes import Config, AssetsData, StockDict, InitialStockData


@dataclass(kw_only=True, slots=True)
class TeamAssets:
    """儲存小隊資產。
    包括「小隊編號」、「資產總額」、「存款總額」。
    """

    team_number: str
    deposit: int
    stock_inv: Dict[str, List[int]] = field(default_factory=dict)
    revenue: int = 0


class AssetsManager(commands.Cog):
    """資產控制。
    """
    
    __slots__ = (
        "bot",
        "CONFIG",
        "team_assets"
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Config = access_file.read_file("game_config")
        self.team_assets: List[TeamAssets] = []    # 儲存各小隊資產

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
        elif(not self.team_assets): # 資料不對等
            self.fetch_assets()
        
        print("Loaded asset_manager")
        
    def reset_asset_data(self):
        """清除所有資產資料，重創銀行帳戶。
        """
        
        dict_ = {
            str(t): {
                "deposit": self.CONFIG["STARTER_CASH"],
                "stock_inv": {},
                "revenue": 0
            }
            for t in range(1, self.CONFIG["NUMBER_OF_TEAMS"]+2) # +1 (Testing team)
        }
        access_file.save_to("team_assets", dict_)
        self.fetch_assets()
        
    def fetch_assets(self):
        """從`team_assets.json`中抓取資料並初始化:class:`TeamAssets`。
        """

        asset: AssetsData = access_file.read_file("team_assets")
        self.team_assets = [
            TeamAssets(
                team_number=str(t),
                deposit=asset[str(t)]["deposit"],
                stock_inv=asset[str(t)]["stock_inv"],
                revenue=asset[str(t)]["revenue"]
            )
            for t in range(1, self.CONFIG["NUMBER_OF_TEAMS"]+2) # +1 (Testing team)
        ]
        
    def save_assets(self, team_number: str | int | None = None):
        """儲存所有或指定小隊資產資料至`team_assets.json`。
        """

        if(team_number is None):    # 儲存所有小隊資料
            dict_ = {}
            for t, asset in enumerate(self.team_assets, start=1):
                dict_.update(
                    {
                        str(t):{
                            "deposit": asset.deposit,
                            "stock_inv": asset.stock_inv,
                            "revenue": asset.revenue
                        }
                    }
                )
        else:   #　儲存指定小隊資料
            dict_: AssetsData = access_file.read_file("team_assets")
            asset = self.team_assets[int(team_number)-1]
            dict_.update(
                {
                    str(team_number):{
                        "deposit": asset.deposit,
                        "stock_inv": asset.stock_inv,
                        "revenue": asset.revenue
                    }
                }
            )

        access_file.save_to("team_assets", dict_)
        pprint(dict_)
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
        access_file.log(
            type_="AssetUpdate",
            time=datetime.now(),
            user=user,
            team=str(team),
            original=original,
            updated=self.team_assets[team-1].deposit
        )
        # 儲存資料
        self.save_assets(team)
        
    async def stock_trade(
            self,
            *,
            team: int,
            trade_type: str,
            stock: int, 
            quantity: int,
            user: str
    ) -> int:
        """買賣股票處理，紀錄log。

        Parameters
        ----------
        team: `int`
            小隊編號。
        trade_type: `str`
            交易別 "buy" or "sell"。
        stock: `int`
            所選擇股票的 index
        quantity: `int`
            交易數量。
        
        Returns
        -------
        display_value: `int`
            買進: 購入成本；賣出: 投資損益
        """

        # 該股市場資料
        stock_dict: StockDict = access_file.read_file("market_data")[stock]
        # 該股當前價值
        value: int = int(round(stock_dict["price"], 2) * 1000) # 該股當前成本價
        # 該小隊持有股票及原始成本
        stock_inv = self.team_assets[team-1].stock_inv
        if(trade_type == "買進"):
            # 新增股票index為key
            if(stock_inv.get(f"{stock}") is None):
                stock_inv[f"{stock}"] = []
            #將成本價新增至TeamAssets資料
            stock_inv[f"{stock}"].extend([value] * quantity)
            # 扣錢
            self.team_assets[team-1].deposit -= value * quantity
            # 計算金額 買進->市價*張數 
            display_value = value * quantity
        elif(trade_type == "賣出"):
            # 計算金額 賣出->投資損益
            display_value = (value * quantity) - sum(stock_inv[f"{stock}"][:quantity])
            # 以股票當前市場價歸還此小隊，從先買的股票賣。
            self.team_assets[team-1].stock_inv[f"{stock}"] = stock_inv[f"{stock}"][quantity:]
            self.team_assets[team-1].deposit += value * quantity
            # 刪除空的資料
            if(not self.team_assets[team-1].stock_inv.get(f"{stock}")):
                self.team_assets[team-1].stock_inv.pop(f"{stock}")
        
        initail_stock_data: InitialStockData = access_file.read_file("raw_stock_data")["initial_data"][stock]
        stock_name_symbol = f"{initail_stock_data["name"]} {initail_stock_data["symbol"]}"
        access_file.log(
            type_="StockChange",
            time=datetime.now(),
            user=user,
            team=str(team),
            trade_type=trade_type,
            stock=stock_name_symbol,
            quantity=quantity
        )

        self.save_assets(team)
        return display_value

    @ntd.slash_command(
        name="change_deposit",
        description="🛅針對指定小隊改變存款額。",
        guild_ids=[1218130958536937492]
    )
    @application_checks.is_owner()
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
    
    @ntd.slash_command(
        name="change_stock",
        description="🛅針對指定小隊改變股票庫存。",
        guild_ids=[1218130958536937492]
    )
    @application_checks.is_owner()
    async def change_stock(
        self,
        interaction: ntd.Interaction,
        team: int = ntd.SlashOption(
            name="小隊",
            description="輸入小隊阿拉伯數字",
            choices={str(t):t for t in range(1, 9)}
        ),
        trade_type: str = ntd.SlashOption(
            name="交易別",
            description="選擇交易別",
            choices=["買進", "賣出"]
        ),
        stock: int = ntd.SlashOption(
            name="股票index",
            description="輸入股票index阿拉伯數字",
            choices={str(t):t for t in range(10)}
        ),
        quantity: int = 1
    ):
        """用指令改變指定小隊存款額。
        """
        
        await self.stock_trade(
            team=team,
            trade_type=trade_type,
            stock=stock,
            quantity=quantity,
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
    