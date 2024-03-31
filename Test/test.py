import json
from typing import Dict, Any

with open(".\\Test\\test.json", "r", encoding="utf-8") as temp_file:  # access
    d: Dict[str, Dict[str, Any]] = json.load(temp_file)

d.update({"1":{"cash": 0, "stock_cost": 0, "stocks": [], "revenue": 0}})  
d.pop("hello", None)   # remove key from dictionary, default: None


with open(".\\Test\\test.json",
          mode="w",
          encoding="utf-8",) as json_file:  # dump new data
    json.dump(d, json_file, ensure_ascii=False, indent=4)
    
