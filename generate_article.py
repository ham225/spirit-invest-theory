#!/usr/bin/env python3
"""data/log.csv の最新行から、note投稿用の記事本文を生成する。

LLMは使わず、theory_signals.py で計算済みの値をテンプレートに埋め込むだけの
決定的な処理(無料・同じ入力なら毎回同じ出力)。個別銘柄の売買を推奨する表現は
使わず、理論の説明とその日のシグナル提示に徹する(金融商品取引法の
無登録投資助言業規制を避けるため)。
"""
from pathlib import Path

from backtest import load_rows, to_float
from theory_score import alert_score

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

    ganzhi = row.get("day_ganzhi") or ""
    if row.get("jippougure") == "True":
        parts.append(f"本日は十方暮期間中(本日={ganzhi})。天地の氣が調和しにくいとされる東洋暦の凶日期間で、一時的なポジティブな値動きが大引けにかけて反転する可能性に注意したい時期です。")
    else:
        parts.append("十方暮の期間外です。")
    return " ".join(parts)


def venus_text(row: dict) -> str:
    sign = row.get("venus_sign") or ""
    bias = row.get("venus_bias") or ""
    if not sign:
        return ""
    return (
        f"\n## 補助情報: 金星サインによる資金ローテーション観測(v1.1、Sスコア対象外)\n\n"
        f"金星は現在{sign}に滞在中です({bias})。この観測はSスコアの計算には含めていない参考コメントです。\n"
    )


def build_article(row: dict) -> str:
    date = row["date"]
    ganzhi = row.get("year_ganzhi", "")
    element = row.get("year_element", "")
    star = row.get("center_star", "")
    star_element = row.get("center_star_element", "")
    relation = row.get("layer2_relation", "")
    hint = ELEMENT_HINT.get(element, "")

    score = alert_score(date)
    reasons = "\n".join(
        f"- {r}" for r in score["a_reasons"] + [score["r_reason"]] + score["t_reasons"]
    )

    return f"""# {date}の宙読み相場|3SM理論デイリーシグナル

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
{venus_text(row)}
## 統合: 今日の警戒レベル(3SM理論)

**S = {score["score"]}({score["band"]})** = 年次成分 10×A×R = {10 * score["A"] * score["R"]}点 + 日次成分 20×T = {20 * score["T"]}点

{reasons}

警戒レベルは「いつリスク管理を強化すべきか」の強度であり、上げ下げの方向を示すものではありません。
計算式の定義は理論の正式文書(THEORY.md)を参照してください。

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
