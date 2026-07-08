#!/usr/bin/env python3
"""Layer2(星が年を剋す=隠れリスク顕在化型)の過去検証。

1985〜2025年の日経平均(yfinance ^N225)について、
- 年間リターン(前年末終値→当年末終値)
- 年中最大ドローダウン(年初からの高値→その後の安値の最大下落率)
- 日次変化率の平均絶対値(年間ボラティリティの簡易指標)
を全年分計算し、Layer2該当年と非該当年で比較した結果を
insights/layer2_history.md に書き出す。

決定的な記述統計のみ(LLM・乱数なし)。事件の後付け選択を排除するのが目的。
GitHub Actions上での実行を想定(ローカル環境によってはYahoo Financeに接続不可)。
"""
import datetime
from pathlib import Path

import yfinance as yf

from theory_signals import CONTROLS, year_center_star, year_ganzhi_element

BASE = Path(__file__).resolve().parent
OUT = BASE / "insights" / "layer2_history.md"

START_YEAR = 1985
END_YEAR = 2025


def is_hit(year: int) -> bool:
    """Layer2「星が年を剋す(隠れリスク顕在化型)」該当年か。"""
    _, _, element, _ = year_ganzhi_element(year)
    _, _, star_element = year_center_star(year)
    return CONTROLS[star_element] == element


def year_stats(closes) -> dict:
    """1年分の終値系列(前年末終値を先頭に含む)から統計を出す。"""
    prev_end = closes[0]
    year_closes = closes[1:]
    annual_return = (year_closes[-1] - prev_end) / prev_end * 100

    peak = year_closes[0]
    max_dd = 0.0
    for c in year_closes:
        peak = max(peak, c)
        max_dd = min(max_dd, (c - peak) / peak * 100)

    abs_changes = [
        abs((year_closes[i] - year_closes[i - 1]) / year_closes[i - 1] * 100)
        for i in range(1, len(year_closes))
    ]
    mean_abs = sum(abs_changes) / len(abs_changes)

    return {
        "annual_return": round(annual_return, 1),
        "max_drawdown": round(max_dd, 1),
        "mean_abs_change": round(mean_abs, 2),
    }


def median(values):
    s = sorted(values)
    n = len(s)
    mid = n // 2
    return round(s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2, 2)


def group_summary(rows):
    return {
        "n": len(rows),
        "med_return": median([r["annual_return"] for r in rows]),
        "med_dd": median([r["max_drawdown"] for r in rows]),
        "med_abs": median([r["mean_abs_change"] for r in rows]),
        "dd_over_15": sum(1 for r in rows if r["max_drawdown"] <= -15),
    }


def main():
    hist = yf.Ticker("^N225").history(
        start=f"{START_YEAR - 1}-12-01", end=f"{END_YEAR + 1}-01-10"
    )
    closes = hist["Close"].dropna()

    results = []
    for year in range(START_YEAR, END_YEAR + 1):
        prev = closes[closes.index.year == year - 1]
        cur = closes[closes.index.year == year]
        if len(prev) == 0 or len(cur) < 100:
            continue
        series = [float(prev.iloc[-1])] + [float(v) for v in cur]
        stats = year_stats(series)
        _, _, element, ganzhi = year_ganzhi_element(year)
        _, star_name, _ = year_center_star(year)
        results.append(
            {"year": year, "ganzhi": ganzhi, "element": element,
             "star": star_name, "hit": is_hit(year), **stats}
        )

    hits = [r for r in results if r["hit"]]
    misses = [r for r in results if not r["hit"]]
    h, m = group_summary(hits), group_summary(misses)

    lines = [
        "# Layer2 過去検証(日経平均・機械集計)",
        "",
        f"生成日: {datetime.date.today().isoformat()} / 対象: {START_YEAR}〜{END_YEAR}年"
        f"(データが揃った{len(results)}年分) / データ: yfinance ^N225",
        "",
        "「星が年を剋す(隠れリスク顕在化型)」該当年と非該当年の比較。",
        "事件の後付け選択を避けるため、指標はすべて機械計算のみ。",
        "",
        "## グループ比較(中央値)",
        "",
        "| 指標 | 該当年 | 非該当年 |",
        "|---|---|---|",
        f"| 年数 | {h['n']} | {m['n']} |",
        f"| 年間リターン(%) | {h['med_return']} | {m['med_return']} |",
        f"| 年中最大ドローダウン(%) | {h['med_dd']} | {m['med_dd']} |",
        f"| 日次変化率の平均絶対値(%) | {h['med_abs']} | {m['med_abs']} |",
        f"| 最大DDが-15%超の年の割合 | {h['dd_over_15']}/{h['n']} | {m['dd_over_15']}/{m['n']} |",
        "",
        "## 年別データ",
        "",
        "| 年 | 干支 | 中宮 | 該当 | 年間リターン(%) | 最大DD(%) | 平均絶対変化率(%) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        mark = "**◯**" if r["hit"] else ""
        lines.append(
            f"| {r['year']} | {r['ganzhi']}({r['element']}) | {r['star']} | {mark} "
            f"| {r['annual_return']} | {r['max_drawdown']} | {r['mean_abs_change']} |"
        )
    lines += [
        "",
        "> 注: 記述統計のみで有意差検定は行っていない。サンプル数(該当年約10)は",
        "> 統計的結論を出すには少なく、参考値である。投資助言ではない(THEORY.md参照)。",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"layer2_history.md を書き出しました({len(results)}年分、該当{h['n']}年)")


if __name__ == "__main__":
    main()
