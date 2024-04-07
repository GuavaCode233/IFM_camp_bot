import pandas as pd
import json
from pprint import pprint
from typing import Dict, List, Any

# 讀取 Excel 檔案並轉換為 DataFrame
df = pd.read_excel(".\\Test\\test_data.xlsx", sheet_name="Q4")
# print(df)
# 將 DataFrame 轉換為 JSON 格式
json_data: List[Dict[str, Any]] = json.loads(df.to_json(orient="records"))

# pprint(json_data)
for d in json_data:
    d["symbol"] = d["symbol"].lstrip("n")


# 將 JSON 寫入檔案
with open(".\\Test\\test_output.json", 'w', encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)
