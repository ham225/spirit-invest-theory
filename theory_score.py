"""三層スピリチュアル・マーケット理論(仮)のLayer1/2をスコア化し、
Layer3の警戒ウィンドウと合わせて年単位のスコアカードを出力するモジュール。

スコアリングのロジックはTHEORY.md「スコアリング(定量化)」に対応する。
Layer1・Layer2は五行の関係(比和・相生・相剋)を1〜5の数値に変換し、
Layer3は数値化せず、その年の水星逆行期間・主要トランジットの日程と
実行日時点での警戒ウィンドウ該当有無を提示する。
"""
import argparse
import datetime

from theory_signals import (
    BRANCH_ELEMENT,
    CONTROLS,
    GENERATES,
    STEM_ELEMENT,
    get_astro_flags,
    year_center_star,
    year_ganzhi_element,
)

# 比和/相生/相剋の関係の種類 → (Layer1スコア, Layer2スコア)
RELATION_SCORE = {
    "比和": (5, 2),
    "a_generates_b": (4, 3),
    "b_generates_a": (3, 2),
    "a_controls_b": (2, 3),
    "b_controls_a": (2, 5),
    "不明": (3, 3),
}


def relation_kind(a_element: str, b_element: str) -> str:
    if a_element == b_element:
        return "比和"
    if GENERATES[a_element] == b_element:
        return "a_generates_b"
    if GENERATES[b_element] == a_element:
        return "b_generates_a"
    if CONTROLS[a_element] == b_element:
        return "a_controls_b"
    if CONTROLS[b_element] == a_element:
        return "b_controls_a"
    return "不明"


def describe_relation(kind: str, a_label: str, b_label: str, hidden_risk_note: str = "") -> str:
    if kind == "比和":
        return f"比和(同気が重なり、その属性が増幅されやすい)"
    if kind == "a_generates_b":
        return f"相生:{a_label}が{b_label}を生む(エネルギーが発散・消耗しやすい)"
    if kind == "b_generates_a":
        return f"相生:{b_label}が{a_label}を生む(エネルギーが後押しされやすい)"
    if kind == "a_controls_b":
        return f"相剋:{a_label}が{b_label}を剋す(勢いが場を抑え込む)"
    if kind == "b_controls_a":
        return f"相剋:{b_label}が{a_label}を剋す{hidden_risk_note}"
    return "不明"


def layer1_score(year: int) -> dict:
    stem, branch, year_element, ganzhi = year_ganzhi_element(year)
    stem_element = STEM_ELEMENT[stem]
    kind = relation_kind(stem_element, year_element)
    score, _ = RELATION_SCORE[kind]
    relation = describe_relation(kind, "十干", "十二支")
    return {
        "ganzhi": ganzhi,
        "stem_element": stem_element,
        "branch_element": year_element,
        "relation": relation,
        "score": score,
    }


def layer2_score(year: int) -> dict:
    _, _, year_element, _ = year_ganzhi_element(year)
    star_num, star_name, star_element = year_center_star(year)
    kind = relation_kind(year_element, star_element)
    _, score = RELATION_SCORE[kind]
    relation = describe_relation(kind, "年の五行", "中宮九星", "(隠れたリスクが顕在化しやすい)")
    return {
        "center_star": star_name,
        "star_element": star_element,
        "year_element": year_element,
        "relation": relation,
        "score": score,
    }


def layer3_windows(year: int, on_date: datetime.date | None) -> dict:
    path_flags = None
    result = {"available": False, "mercury_retrograde": [], "major_transits": [], "today": None}
    try:
        import json
        from pathlib import Path

        data = json.loads((Path(__file__).resolve().parent / f"astro_events_{year}.json").read_text(encoding="utf-8"))
        result["available"] = True
        result["mercury_retrograde"] = data.get("mercury_retrograde", [])
        result["major_transits"] = data.get("major_transits", [])
    except FileNotFoundError:
        return result

    if on_date is not None and on_date.year == year:
        result["today"] = get_astro_flags(on_date.isoformat(), year)
    return result


def format_report(year: int, on_date: datetime.date | None) -> str:
    l1 = layer1_score(year)
    l2 = layer2_score(year)
    l3 = layer3_windows(year, on_date)

    lines = [f"=== {year}年 理論スコアカード(三層スピリチュアル・マーケット理論・仮) ===", ""]

    lines.append("[Layer1] 干支五行トレンド(方向・強度)")
    lines.append(f"  干支: {l1['ganzhi']} / 十干の属性={l1['stem_element']} / 十二支の属性(年代表)={l1['branch_element']}")
    lines.append(f"  関係: {l1['relation']}")
    lines.append(f"  スコア: {l1['score']}/5")
    lines.append("")

    lines.append("[Layer2] 九星気学・中宮(隠れリスク層)")
    lines.append(f"  中宮: {l2['center_star']}({l2['star_element']}) / 年代表の属性: {l2['year_element']}")
    lines.append(f"  関係: {l2['relation']}")
    lines.append(f"  スコア: {l2['score']}/5")
    lines.append("")

    lines.append("[Layer3] 西洋占星術トランジット(タイミング層・数値化なし)")
    if not l3["available"]:
        lines.append(f"  astro_events_{year}.json が未整備のため、暦データを追加してください。")
    else:
        for period in l3["mercury_retrograde"]:
            lines.append(f"  水星逆行: {period['name']} {period['start']}〜{period['end']}")
        for transit in l3["major_transits"]:
            lines.append(f"  主要トランジット: {transit['name']} exact={transit['exact_date']}")
        if l3["today"] is not None:
            flags = l3["today"]
            retro = "警戒ウィンドウ内(水星逆行中: " + flags["mercury_retrograde_name"] + ")" if flags["mercury_retrograde"] else "警戒ウィンドウ外"
            lines.append(f"  本日({on_date.isoformat()})時点: {retro}")
            days = flags["saturn_neptune_days_from_exact"]
            if days != "":
                lines.append(f"  土星海王星の合(exact)まで{int(days)}日")
    lines.append("")

    total = round((l1["score"] + l2["score"]) / 2, 1)
    lines.append(f"[統合] 総合スコア(Layer1+Layer2の平均): {total}/5")
    lines.append("  ※Layer3の警戒ウィンドウ(上記)と重なる時期ほど、リスク管理を強化すべきという運用シナリオになる。")
    lines.append("")
    lines.append("※本内容は投資助言ではありません。エンタメ×経済分析のハイブリッドコンテンツです(詳細はTHEORY.md参照)。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="理論スコアカードを出力する")
    parser.add_argument("--year", type=int, default=datetime.date.today().year)
    args = parser.parse_args()

    on_date = datetime.date.today()
    print(format_report(args.year, on_date))


if __name__ == "__main__":
    main()
