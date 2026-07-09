#!/usr/bin/env python3
"""毎日の市場データ+理論シグナル(Layer1/2/3)を data/log.csv に追記する。

GitHub Actions から平日夕方(JST)に自動実行される想定。
LLMは使わず、yfinanceで無料取得できる範囲のデータのみを使う。
"""
import csv
import datetime
import sys
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))

import yfinance as yf

from theory_signals import (
    day_ganzhi,
    five_element_relation,
    get_astro_flags,
    get_venus_sign,
    is_jippougure,
    year_center_star,
    year_ganzhi_element,
)

BASE = Path(__file__).resolve().parent
LOG = BASE / "data" / "log.csv"

# Layer1の五行資産マッピングの代表銘柄(日本語コメントは README 参照)
TICKERS = {
    "nikkei225": "^N225",       # 市場全体
    "tokyo_electron": "8035.T",  # 火=AI・半導体モメンタム系の代表
    "usdjpy": "JPY=X",          # 水=為替・流動性
    "gold": "GC=F",             # 金=資源・有事の金
}

FIELDS = [
    "date",
    "nikkei225_close", "nikkei225_chg_pct",
    "tokyo_electron_close", "tokyo_electron_chg_pct",
    "usdjpy_close", "usdjpy_chg_pct",
    "gold_close", "gold_chg_pct",
    "year_ganzhi", "year_element",
    "center_star", "center_star_element",
    "layer2_relation",
    "mercury_retrograde", "mercury_retrograde_name",
    "saturn_neptune_days_from_exact",
    "day_ganzhi", "jippougure",
    "venus_sign", "venus_bias",
]


def fetch_market_data() -> dict:
    row = {}
    for key, symbol in TICKERS.items():
        try:
            hist = yf.Ticker(symbol).history(period="5d")
            closes = hist["Close"].dropna()
            if len(closes) < 2:
                raise ValueError("十分な履歴データが取得できませんでした")
            last = float(closes.iloc[-1])
            prev = float(closes.iloc[-2])
            row[f"{key}_close"] = round(last, 3)
            row[f"{key}_chg_pct"] = round((last - prev) / prev * 100, 3)
        except Exception as e:  # noqa: BLE001 - 1銘柄の失敗で全体を止めない
            print(f"[warn] {key}({symbol}) の取得に失敗: {e}", file=sys.stderr)
            row[f"{key}_close"] = ""
            row[f"{key}_chg_pct"] = ""
    return row


def already_logged(today: str) -> bool:
    if not LOG.exists():
        return False
    with open(LOG, encoding="utf-8") as f:
        return any(line.startswith(today + ",") for line in f)


def main():
    now_jst = datetime.datetime.now(JST).date()
    today = now_jst.isoformat()
    year = now_jst.year

    if already_logged(today):
        print(f"{today} は記録済みのためスキップします")
        return

    row = {"date": today}
    row.update(fetch_market_data())

    _, _, element, ganzhi = year_ganzhi_element(year)
    _, star_name, star_element = year_center_star(year)
    relation = five_element_relation(element, star_element)

    row["year_ganzhi"] = ganzhi
    row["year_element"] = element
    row["center_star"] = star_name
    row["center_star_element"] = star_element
    row["layer2_relation"] = relation

    astro = get_astro_flags(today, year)
    row["mercury_retrograde"] = astro["mercury_retrograde"]
    row["mercury_retrograde_name"] = astro["mercury_retrograde_name"]
    row["saturn_neptune_days_from_exact"] = astro["saturn_neptune_days_from_exact"]

    row["day_ganzhi"] = day_ganzhi(now_jst)
    row["jippougure"] = is_jippougure(now_jst)

    venus = get_venus_sign(today, year)
    row["venus_sign"] = venus["sign"]
    row["venus_bias"] = venus["bias"]

    LOG.parent.mkdir(parents=True, exist_ok=True)
    write_header = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    print(f"{today} のデータを記録しました:")
    for k, v in row.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
