# import json
# from typing import Dict, Any
from pprint import pprint

# with open(".\\Test\\test.json", "r", encoding="utf-8") as temp_file:  # access
#     d: Dict[str, Dict[str, Any]] = json.load(temp_file)

# d.update({"1":{"cash": 0, "stock_cost": 0, "stocks": [], "revenue": 0}})  
# d.pop("hello", None)   # remove key from dictionary, default: None


# with open(".\\Test\\test.json",
#           mode="w",
#           encoding="utf-8",) as json_file:  # dump new data
#     json.dump(d, json_file, ensure_ascii=False, indent=4)
    
d = {
    "2": [
        {
            "type": "AssetUpdate",
            "time": "05/04 10:54AM",
            "user": "guava.png",
            "original": 10000,
            "serial": 1,
            "updated": 8500
        },
        {
            "type": "AssetUpdate",
            "time": "05/04 10:54AM",
            "user": "guava.png",
            "serial": 2,
            "original": 8500,
            "updated": 68500
        }
    ],
    "8": [
        {
            "type": "AssetUpdate",
            "time": "05/04 10:55AM",
            "user": "guava.png",
            "serial": 3,
            "original": 10000,
            "updated": 6667
        }
    ]
}

t_list = [] # 輸出的list
for r in d.values():
    t_list += r

t_list.sort(key=lambda x: x["serial"])

pprint(t_list)