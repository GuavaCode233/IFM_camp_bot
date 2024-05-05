import pandas as pd
import json

df: pd.DataFrame = pd.read_excel(
    ".\\Data\\raw_news.xlsx", "Q2"
)
json_data = json.loads(
    df.to_json(orient="records")
)

with open(
    ".\\Test\\test.json",
    mode="w",
    encoding="utf-8"
) as jf:
    json.dump(
        json_data, jf,
        ensure_ascii=False,
        indent=4
    )