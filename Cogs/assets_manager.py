from nextcord.ext import commands

from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from datetime import datetime
import json

from .utilities import access_file
from .utilities.datatypes import (
    AssetsData,
    ChangeMode,
    Config,
    InitialStockData,
    LogData,
    LogType,
    StockDict,
    TradeType
)


def log(
    *,
    log_type: LogType,
    user: str,
    team: str | Tuple[str, str],
    original_deposit: int | Tuple[int, int] | None = None,
    changed_deposit : int | Tuple[int, int] | None = None,
    trade_type: TradeType | None = None,
    stock: str | None = None,
    quantity: int | None = None
):
    """收支紀錄(各小隊)。
    """

    with open(
        ".\\Data\\alteration_log.json",
        mode="r",
        encoding="utf-8"
    ) as json_file:
        dict_: Dict[str, int | List[LogData]] = json.load(json_file)

    time = datetime.now().strftime("%m/%d %I:%M%p")
    
    if(log_type == "Transfer"):
        transfer_team = team[0]
        if(dict_.get(transfer_team, None) is None):
            dict_[transfer_team] = []
        dict_[transfer_team].append(
            {
                "log_type": log_type,
                "time": time,
                "user": user,
                "serial": dict_["serial"],
                "team": team,
                "original_deposit": original_deposit,
                "changed_deposit": changed_deposit
            }
        )
    elif(dict_.get(team, None) is None):
        dict_[team] = []

    if(log_type == "DepositChange"):
        dict_[team].append(
            {
                "log_type": log_type,
                "time": time,
                "user": user,
                "serial": dict_["serial"],
                "team": team,
                "original_deposit": original_deposit,
                "changed_deposit": changed_deposit 
            }
        )
    elif(log_type == "StockChange"):
        dict_[team].append(
            {
                "log_type": log_type,
                "time": time,
                "user": user,
                "serial": dict_["serial"],
                "team": team,
                "trade_type": trade_type,
                "stock": stock,
                "quantity": quantity
            }
        )

    dict_["serial"] += 1

    with open(
        ".\\Data\\alteration_log.json",
        mode="w",
        encoding="utf-8"
    ) as json_file:
        json.dump(
            dict_, json_file,
            ensure_ascii=False,
            indent=4
        )


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
        
        `RESET_ALL`
        清除全部小隊資產資料並重創銀行帳戶，
        如果資料有遺失，重新抓取資產資料。
        """

        RESET_ALL: bool = self.CONFIG["RESET_ALL"]
        if(RESET_ALL):   # 開新遊戲
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
        
    def save_assets(self, team_number: int| str | None = None):
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
    
    def change_deposit(
            self,
            *,
            team: int,
            change_mode: ChangeMode,
            amount: int,
            user: str,
            liquidation: bool = False
    ):
        """改變小隊存款額並記錄log。

        Parameters
        ----------
        team: `int`
            要更新存款的小隊。
        change_mode: `ChangeMode`
            變更模式
            - Deposit: 增加存款
            - Withdraw: 減少存款
            - Change: 更改存款餘額

        amount: `int`
            變更量。
        user: `str`
            變更者。
        liquidation: `Optional[bool]` = False
            是否為清算所獲收入，是則不計入總收入。
        """
        
        original_deposit = self.team_assets[team-1].deposit # 原餘額     

    
        if(change_mode == "Deposit"):
            self.team_assets[team-1].deposit += amount
            if(not liquidation):
                self.increment_revenue(team, amount)
        elif(change_mode == "Withdraw"):
            self.team_assets[team-1].deposit -= amount
        elif(change_mode == "Change"):
            self.team_assets[team-1].deposit = amount
            if(amount > original_deposit):  # 更改存款大於原存款時，差額補上總收益
                self.increment_revenue(team, amount-original_deposit)
            elif(amount < original_deposit):    # 更改存款大於原存款時，總收益減掉差額
                self.decreese_revenue(team, original_deposit-amount)
                
        # 儲存紀錄
        log(
            log_type="DepositChange",
            user=user,
            team=str(team),
            original_deposit=original_deposit,
            changed_deposit=self.team_assets[team-1].deposit
        )
        # 儲存資料
        self.save_assets(team)

    def transfer(
            self,
            *,
            transfer_deposit_teams: Tuple[str, str],
            amount: int,
            user: str
    ):
        """轉帳並記錄log。

        Parameters
        ----------
        transfer_deposit_teams: `Tuple[int, int]` = `None`
            轉出與轉入小隊 (transfer_team, deposit_team)。
        amount: `int`
            轉帳額度。
        user: `str`
            操作轉帳者。
        """

        transfer_team, deposit_team = (int(t) for t in transfer_deposit_teams)
        original_deposits = (
            self.team_assets[transfer_team-1].deposit,
            self.team_assets[deposit_team-1].deposit
        )
        self.team_assets[transfer_team-1].deposit -= amount
        self.team_assets[deposit_team-1].deposit += amount

        log(
            log_type="Transfer",
            user=user,
            team=transfer_deposit_teams,
            original_deposit=original_deposits,
            changed_deposit=(
                self.team_assets[transfer_team-1].deposit,
                self.team_assets[deposit_team-1].deposit
            )
        )

        self.save_assets(transfer_team)
        self.save_assets(deposit_team)
        
    def stock_trade(
            self,
            *,
            team: int,
            trade_type: TradeType,
            stock_index: int, 
            quantity: int,
            user: str
    ) -> int:
        """買賣股票處理，紀錄log。

        Parameters
        ----------
        team: `int`
            小隊編號。
        trade_type: `TradeType`
            交易別 "買進" or "賣出"。
        stock: `int`
            所選擇股票的 index
        quantity: `int`
            交易數量。
        user: `str`
            執行交易的使用者。
        
        Returns
        -------
        display_value: `int`
            買進: 購入成本；賣出: 投資損益
        """

        # 該股市場資料
        stock_dict: StockDict = access_file.read_file("market_data")[stock_index]
        # 該股當前價值
        value: int = int(round(stock_dict["price"], 2) * 1000) # 該股當前成本價
        # 該小隊持有股票及原始成本
        stock_inv = self.team_assets[team-1].stock_inv
        if(trade_type == "買進"):
            # 新增股票index為key
            if(stock_inv.get(f"{stock_index}") is None):
                stock_inv[f"{stock_index}"] = []
            #將成本價新增至TeamAssets資料
            stock_inv[f"{stock_index}"].extend([value] * quantity)
            # 扣錢
            self.team_assets[team-1].deposit -= value * quantity
            # 計算金額 買進->市價*張數 
            display_value = value * quantity
        elif(trade_type == "賣出"):
            # 計算金額 賣出->投資損益
            display_value = (value * quantity) - sum(stock_inv[f"{stock_index}"][:quantity])
            if(display_value > 0):  # 若有資本利得則算入總收益
                self.increment_revenue(team, display_value)
            # 以股票當前市場價歸還此小隊，從先買的股票賣。
            self.team_assets[team-1].stock_inv[f"{stock_index}"] = stock_inv[f"{stock_index}"][quantity:]
            self.team_assets[team-1].deposit += value * quantity
            # 刪除空的資料
            if(not self.team_assets[team-1].stock_inv.get(f"{stock_index}")):
                self.team_assets[team-1].stock_inv.pop(f"{stock_index}")
        
        initail_stock_data: InitialStockData = access_file.read_file("raw_stock_data")["initial_data"][stock_index]
        stock_name_symbol = f"{initail_stock_data["name"]} {initail_stock_data["symbol"]}"
        log(
            log_type="StockChange",
            user=user,
            team=str(team),
            trade_type=trade_type,
            stock=stock_name_symbol,
            quantity=quantity
        )

        self.save_assets(team)
        return display_value
    
    def increment_revenue(self, team: int, amount: int):
        """增加小隊的總收入。
        """

        self.team_assets[team-1].revenue += amount
        self.save_assets(team)

    def decreese_revenue(self, team: int, amount: int):
        """減少小隊的總收入(通常只有在存款記錯更改後才會用到)。
        """

        self.team_assets[team-1].revenue -= amount
        self.save_assets(team)


def setup(bot: commands.Bot):
    bot.add_cog(AssetsManager(bot))
