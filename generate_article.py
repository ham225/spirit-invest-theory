#!/usr/bin/env python3
"""data/log.csv の最新行から、note投稿用の記事本文を生成する。

LLMは使わず、theory_signals.py で計算済みの値をテンプレートに埋め込むだけの
決定的な処理(無料・同じ入力なら毎回同じ出力)。個別銘柄の売買を推奨する表現は
使わず、理論の説明とその日のシグナル提示に徹する(金融商品取引法の
無登録投資助言業規制を避けるため)。
"""
from pathlib import Path

from backtest import load_rows, to_float

BASE = Path(__file__).resolve().parent
OUT_DIR = BASE / "insights" / "articles"

ASSET_LABELS = {
    "nikkei225": "日経平均",
    "tokyo_electron": "東京エレクトロン(火=AI半導体の代表)",
    "usdjpy": "ドル円(水=為替・流動性の代表)",
    "gold": "金(資源の代表)",
}

ELEMENT_HINT = {
    "火": "AI・半導体・グロース株などモメンタム系",
    "水": "金融・流動性・為替",
    "金": "貴金属・資源",
    "木": "新興国・成長",
    "土": "不動産・インフラ",
}

DISCLAIMER = """---

## 免責
本内容は特定の銘柄・金融商品・投資手法を推奨または勧誘するものではありません。
干支の五行・九星気学・西洋占星術を経済分析に絡めたエンタメ×経済分析のハイブリッドコンテンツであり、
単体で投資判断を行わないでください。市場データはyfinance(Yahoo Finance)経由の参考値であり、
遅延・欠損の可能性があります。本内容をもとに生じたいかなる損失についても責任を負いかねます。
"""


def market_snapshot(row: dict) -> str:
    lines = ["| 銘柄 | 終値 | 前日比 |", "|---|---|---|"]
    for key, label in ASSET_LABELS.items():
        close = row.get(f"{key}_close") or "-"
        chg = to_float(row.get(f"{key}_chg_pct"))
        chg_str = f"{chg:+.2f}%" if chg is not None else "-"
        lines.append(f"| {label} | {close} | {chg_str} |")
    return "\n".join(lines)


def layer3_text(row: dict) -> str:
    retro = row.get("mercury_retrograde") == "True"
    retro_name = row.get("mercury_retrograde_name") or ""
    days_raw = to_float(row.get("saturn_neptune_days_from_exact"))

    parts = []
    if retro:
        parts.append(f"本日は水星逆行期間中({retro_name})。短期的な見誤り・訂正が起きやすい警戒ウィンドウにあたります。")
    else:
        parts.append("本日は水星逆行期間外です。")

    if days_raw is not None:
        if abs(days_raw) <= 14:
            parts.append(f"土星海王星の合(exact)まで{int(days_raw)}日。前後14日の警戒ウィンドウ内にあります。")
        else:
            parts.append(f"土星海王星の合(exact)まで{int(days_raw)}日。警戒ウィンドウ外です。")
    return " ".join(parts)


def build_article(row: dict) -> str:
    date = row["date"]
    ganzhi = row.get("year_ganzhi", "")
    element = row.get("year_element", "")
    star = row.get("center_star", "")
    star_element = row.get("center_star_element", "")
    relation = row.get("layer2_relation", "")
    hint = ELEMENT_HINT.get(element, "")

    return f"""# {date}の宙読み相場理論(仮)

## 今日のマーケットスナップショット

{market_snapshot(row)}

## Layer1: 干支五行トレンド

{date[:4]}年は{ganzhi}({element}の年)。{element}の属性は{hint}に紐づくとされ、
この属性が重なる年は関連資産のトレンドが増幅されやすい、という仮説です。

## Layer2: 九星気学・中宮レイヤー(隠れリスク層)

本日の中宮は{star}({star_element})。年の五行({element})との関係は「{relation}」。
表面的なトレンドの裏に隠れているリスクの強弱を示す警戒フラグであり、方向(上げ下げ)は決めません。

## Layer3: 西洋占星術トランジットレイヤー(タイミング層)

{layer3_text(row)}

{DISCLAIMER}"""


def main():
    rows = load_rows()
    if not rows:
        print("data/log.csv にデータがありません。先に fetch_data.py を実行してください。")
        return

    row = rows[-1]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{row['date']}.md"
    out_path.write_text(build_article(row), encoding="utf-8")
    print(f"{out_path} を書き出しました")


if __name__ == "__main__":
    main()
