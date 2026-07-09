#!/usr/bin/env python3
"""3SM理論(三層スピリチュアル・マーケット理論)のスコアリングモジュール。

THEORY.md §2〜§4 の計算式をそのまま実装した決定的な計算のみ(LLM・乱数なし)。
- Layer1: 年次増幅スコア A(1〜3)
- Layer2: 隠れリスク指数 R(0〜2)
- Layer3: タイミング係数 T(0〜2、日次)
- 統合:   日次警戒レベル S = 10*A*R + 20*T(0〜100)

使い方:
  python theory_score.py                # 今日の警戒レベル
  python theory_score.py 2026-11-01     # 指定日の警戒レベル
  python theory_score.py --year 2026    # 年間シナリオ(警戒カレンダー)
"""
import datetime
import json
import sys
from pathlib import Path

from theory_signals import (
    BRANCH_ELEMENT,
    CONTROLS,
    GENERATES,
    STEM_ELEMENT,
    day_ganzhi,
    get_astro_flags,
    get_venus_sign,
    is_jippougure,
    year_center_star,
    year_ganzhi_element,
)

BASE = Path(__file__).resolve().parent

# トランジットexact前後の警戒ウィンドウ(backtest.py の ORB_DAYS と同値に保つこと)
ORB_DAYS = 14

# (下限スコア, 判定名)。上から順に評価する
ALERT_BANDS = [
    (70, "厳戒"),
    (40, "警戒"),
    (20, "注意"),
    (0, "平常"),
]


def alert_band(score: int) -> str:
    for threshold, name in ALERT_BANDS:
        if score >= threshold:
            return name
    return "平常"


def layer1_amplification(year: int):
    """A: 年次増幅スコア(1〜3)と加点理由を返す。"""
    stem, branch, element, ganzhi = year_ganzhi_element(year)
    score = 1
    reasons = [f"基礎点+1({ganzhi}年・代表五行={element})"]
    if STEM_ELEMENT[stem] == BRANCH_ELEMENT[branch]:
        score += 1
        reasons.append(f"干支比和+1(十干{stem}・十二支{branch}がともに{element})")
    _, star_name, star_element = year_center_star(year)
    if star_element == element:
        score += 1
        reasons.append(f"九星比和+1(中宮{star_name}も{element})")
    return score, reasons


def layer2_risk(year: int):
    """R: 隠れリスク指数(0〜2)と判定理由を返す。"""
    _, _, element, _ = year_ganzhi_element(year)
    _, star_name, star_element = year_center_star(year)
    star = f"中宮{star_name}({star_element})"
    if CONTROLS[star_element] == element:
        return 2, f"相剋+2({star}が年({element})を剋す=隠れリスク顕在化型)"
    if CONTROLS[element] == star_element:
        return 1, f"相剋+1(年({element})が{star}を剋す=反動リスク型)"
    if GENERATES[element] == star_element:
        return 1, f"相生+1(年({element})が{star}を生む=消耗型)"
    if GENERATES[star_element] == element:
        return 0, f"相生+0({star}が年({element})を生む=後押し型)"
    return 0, f"比和+0(年({element})と{star}が同気=増幅はLayer1で加点済み)"


def layer3_timing(date_str: str):
    """T: タイミング係数(0〜3、v1.1で十方暮を追加)と判定理由を返す。"""
    date = datetime.date.fromisoformat(date_str)
    year = date.year
    astro = get_astro_flags(date_str, year)
    score = 0
    reasons = []
    if astro["mercury_retrograde"]:
        score += 1
        reasons.append(f"水星逆行中+1({astro['mercury_retrograde_name']})")
    days = astro["saturn_neptune_days_from_exact"]
    if days != "" and abs(days) <= ORB_DAYS:
        score += 1
        reasons.append(f"主要トランジットexactまで{days}日+1(±{ORB_DAYS}日以内)")
    if is_jippougure(date):
        score += 1
        reasons.append(f"十方暮期間中+1(本日={day_ganzhi(date)}、東洋暦の凶日期間)")
    if not reasons:
        if astro["mercury_retrograde_name"] == "astroデータ未整備の年":
            reasons.append(f"+0(astro_events_{year}.json が未整備のため T=0 扱い)")
        else:
            reasons.append("+0(逆行・トランジット・十方暮いずれの警戒ウィンドウ外)")
    return score, reasons


def alert_score(date_str: str) -> dict:
    """指定日の警戒レベル S と内訳を返す(THEORY.md §3)。"""
    year = datetime.date.fromisoformat(date_str).year
    a, a_reasons = layer1_amplification(year)
    r, r_reason = layer2_risk(year)
    t, t_reasons = layer3_timing(date_str)
    score = 10 * a * r + 20 * t
    return {
        "date": date_str,
        "A": a,
        "R": r,
        "T": t,
        "score": score,
        "band": alert_band(score),
        "a_reasons": a_reasons,
        "r_reason": r_reason,
        "t_reasons": t_reasons,
    }


def annual_scenario(year: int) -> str:
    """年間シナリオ(警戒カレンダー)をテキストで返す(THEORY.md §4)。"""
    a, a_reasons = layer1_amplification(year)
    r, r_reason = layer2_risk(year)
    base = 10 * a * r
    lines = [
        f"# {year}年の3SM理論 年間シナリオ",
        "",
        f"Layer1 A={a}: " + " / ".join(a_reasons),
        f"Layer2 R={r}: {r_reason}",
        f"ベース警戒レベル 10AR = {base}({alert_band(base)})",
        "",
    ]

    if not (BASE / f"astro_events_{year}.json").exists():
        lines.append(
            f"astro_events_{year}.json が未整備のため、Layer3の日次ウィンドウは算出できません。"
        )
        return "\n".join(lines)

    # 1年を日ごとに走査し、Sが同じ日をウィンドウとしてまとめる
    windows = []
    day = datetime.date(year, 1, 1)
    end = datetime.date(year, 12, 31)
    while day <= end:
        t, _ = layer3_timing(day.isoformat())
        s = base + 20 * t
        if windows and windows[-1]["score"] == s:
            windows[-1]["end"] = day
        else:
            windows.append({"start": day, "end": day, "t": t, "score": s})
        day += datetime.timedelta(days=1)

    lines.append("| 期間 | T | S | 判定 |")
    lines.append("|---|---|---|---|")
    for w in windows:
        period = f"{w['start'].month}/{w['start'].day}〜{w['end'].month}/{w['end'].day}"
        lines.append(f"| {period} | {w['t']} | {w['score']} | {alert_band(w['score'])} |")
    return "\n".join(lines)


def format_daily(result: dict) -> str:
    detail = "、".join(result["a_reasons"] + [result["r_reason"]] + result["t_reasons"])
    return (
        f"{result['date']} の警戒レベル S={result['score']}({result['band']})\n"
        f"  内訳: A={result['A']} × R={result['R']} → {10 * result['A'] * result['R']}点"
        f" + T={result['T']} → {20 * result['T']}点\n"
        f"  根拠: {detail}"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--year":
        print(annual_scenario(int(args[1])))
    else:
        date_str = args[0] if args else datetime.date.today().isoformat()
        print(format_daily(alert_score(date_str)))
