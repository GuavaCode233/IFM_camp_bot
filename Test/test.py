import pandas as pd
import json
from pprint import pprint
from typing import Dict, List, Any

# 讀取 Excel 檔案並轉換為 DataFrame
df = pd.read_excel(".\\Data\\stock_data.xlsx", sheet_name="Q4")
# print(df)
# 將 DataFrame 轉換為 JSON 格式
json_data: List[Dict[str, Any]] = json.loads(df.to_json(orient="records"))


temp_dict = {}
for d in json_data:
    d["symbol"] = d["symbol"].lstrip("n")
    symbol_key: str = d.pop("symbol")
    temp_dict[symbol_key] = d


# 將 JSON 寫入檔案
with open(".\\Test\\test_output.json", 'w', encoding="utf-8") as f:
    json.dump(temp_dict, f, ensure_ascii=False, indent=4)
