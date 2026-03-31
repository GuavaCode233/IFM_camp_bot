# 📈 理財大富翁機器人 (IFM Camp F-Pay Bot)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Nextcord](https://img.shields.io/badge/Nextcord-Discord_API-7289DA.svg)
![Pandas](https://img.shields.io/badge/Pandas-Data_Processing-150458.svg)
![JSON](https://img.shields.io/badge/JSON-Data_Storage-lightgrey.svg)
![PEP8](https://img.shields.io/badge/Code_Style-PEP_8-green.svg)

> **專為高中生資訊與財金營隊打造的互動式「數位貨幣與模擬股市」Discord 機器人。**

## 💡 專案背景與痛點解決 (Background)

在傳統的「理財大富翁」營隊活動中，通常依賴紙本假幣與實體卡片進行交易。這不僅造成大量紙張浪費（影印、裁剪成本），且活動進行時難以即時結算各隊伍的總資產，更無法呈現真實世界中「股市浮動」與「財報查閱」的體驗。

為此，本專案開發了 **「F-Pay 理財大富翁機器人」**，透過學生最熟悉的 Discord 平台作為前端 UI，達成以下核心目標：
1. **貨幣全面數位化**：實現無紙化，提供玩家與關主即時的 F-Pay 轉帳與資產結算功能。
2. **導入動態股市機制**：以預設時間線投報新聞稿（地球新聞台），並動態更動上市公司股價，讓玩家能以隊伍為單位模擬真實投資。
3. **低門檻的 UI 互動設計**：全面使用按鈕與下拉式選單（`nextcord.ui.View`），玩家**無需背誦及手動輸入繁瑣的指令**即可完成股票交易與財報查詢。

---

## ✨ 核心功能與展示 (Features & Demo)

### 1. 📊 模擬股市與即時交易 (Stock Market)
* **市場動態 (`#市場動態`)**：即時顯示各檔股票的成交價與本季漲跌幅。
> <img width="505" height="530" alt="image" src="https://github.com/user-attachments/assets/7590a9b7-8770-4756-a672-bd2c9e3578dc" />

* **無指令化交易 UI**：玩家點擊「股票交易」後，透過下拉式選單選擇標的與張數，防呆且直覺。
> <img width="595" height="707" alt="image" src="https://github.com/user-attachments/assets/f0e1e9f5-f1a0-4a91-8454-af4fec963b6a" />

* **財務報表查詢**：點擊按鈕即可自動帶出公開發行公司的財務報表（如：銷貨淨額、營業收入、EPS等），供玩家作為投資參考。
> <img width="555" height="592" alt="image" src="https://github.com/user-attachments/assets/37c1c242-b5a3-43c4-bcfc-fbbbd4f2a511" />

### 2. 💰 數位帳戶與資產管理 (Asset Management)
* **小隊資產總覽 (`#資產`)**：自動計算並顯示小隊的「存款餘額」、「股票庫存」、「未實現總損益」及「總收益」。
> <img width="551" height="559" alt="image" src="https://github.com/user-attachments/assets/56433db8-7e09-4b41-8b1d-fae854f261b4" />

* **即時帳務通知 (`#即時通知`)**：每當有 F-Pay 轉帳收入、消費扣款或股票買賣成交時，系統會推送專屬的即時入帳通知，確保帳務透明。
> <img width="547" height="913" alt="image" src="https://github.com/user-attachments/assets/6a0e847e-03ad-405d-8e6c-b0de20256580" />


### 3. 📰 地球新聞台與動態事件 (News Broadcasting)
* 配合營隊時間線，自動於 `#地球新聞台` 發送突發新聞。新聞內容與背後的 Pandas 股價變動資料連動，考驗玩家解讀市場資訊的能力。

---

## 🛠 系統架構與技術棧 (Architecture & Tech Stack)

本專案將運算邏輯部署於本地端，並透過 Discord 作為前端顯示與團隊權限管理介面。

* **開發語言**：Python (全面遵循 PEP 8 程式碼風格指南)
* **核心框架**：`nextcord` & `nextcord.ext.commands` (運用 Cogs 進行模組化與架構管理)
* **非同步處理**：`asyncio` (處理多人、多隊伍同時併發的交易請求與 I/O 操作)
* **資料處理**：`pandas` (讀取 Excel 中事先編排好的劇本、股價變動與新聞資料)
* **資料儲存**：`JSON` (輕量化存取小隊餘額、庫存等狀態資料)
* **型別標記**：`typing` (實作自訂資料類別 `utilities/datatypes.py`，確保開發期的型別安全與易讀性)

---

## 🚀 開發挑戰與解決方案 (Challenges & Solutions)

### 狀態殘留與 UI 鎖死問題 (State Management Issue)
**情境**：因為本系統大量依賴 Discord 的 UI 元件（如選單），當使用者未正常送出表單，而是直接點擊藍色字體「刪除這些訊息」關閉表單時，會在系統後台留下未清除的 Interaction State，導致後續點擊按鈕時顯示「已開啟選單」而無法動作。
**解決方案**：
1. **實作狀態清除指令**：開發 `/clear_user_record` 指令，讓隊輔能手動強制釋放卡住的 UI 狀態，確保活動流暢進行。
2. **編寫詳盡使用者手冊**：針對營隊隊輔製作了包含 20 頁圖文並茂的《F-Pay 使用手冊》，將此 Trouble-shooting 流程標準化，大幅降低活動進行時的技術支援成本。

---

## 📂 專案結構 (Directory Structure)
```text
IFM_camp_bot/
│
├── main.py                # 程式進入點與 Bot 啟動邏輯
├── cogs/                  # 模組化功能 (Cogs)
│   ├── stock_manager.py   # 股市與交易系統邏輯
│   ├── assets_manager.py  # 資產結算與 F-Pay 轉帳邏輯
│   └── discord_ui.py      # Discord介面UI元件
├── utilities/
│   ├── access_file.py     # 存取檔案方法
│   └── datatypes.py       # 自訂型別標記 (Typing)
├── Data/                  # 資料持久化與狀態管理 (State Management)
│   ├── game_config.json   # 遊戲全域設定與靜態參數
│   ├── game_state.json    # 當前活動進度與全域狀態追蹤
│   ├── team_assets.json   # 各小隊資金、股票庫存等動態資產紀錄
│   ├── alteration_log.json# 交易與資產異動歷史日誌 (Audit Log，確保交易可追溯)
│   ├── raw_stock_data.xlsx # 原始股價劇本 (供營隊企劃編輯，由程式讀取)
│   └── raw_news.xlsx      # 原始新聞稿劇本
└── README.md
