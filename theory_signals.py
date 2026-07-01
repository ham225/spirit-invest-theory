"""干支・五行・九星気学・西洋占星術のシグナルを計算するモジュール。

干支(十干十二支)と九星気学の年家九星は計算式で毎年自動的に求める。
西洋占星術のトランジット(水星逆行・土星海王星の合など)は年ごとに暦を
調べて手入力する必要があるため astro_events_<year>.json に記録する。
対応する年のファイルが無い場合は「データ未整備」として扱う。
"""
import datetime
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
STEM_ELEMENT = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
BRANCH_ELEMENT = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

STAR_NAMES = {
    1: "一白水星", 2: "二黒土星", 3: "三碧木星", 4: "四緑木星",
    5: "五黄土星", 6: "六白金星", 7: "七赤金星", 8: "八白土星", 9: "九紫火星",
}
STAR_ELEMENT = {
    1: "水", 2: "土", 3: "木", 4: "木",
    5: "土", 6: "金", 7: "金", 8: "土", 9: "火",
}

GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

# 2026年=一白水星(基準年)。九星気学の年家九星は9年周期で1→9へ降順循環する。
REF_YEAR = 2026
REF_STAR = 1


def year_ganzhi_element(year: int):
    """(十干, 十二支, 年の代表五行, 干支表記)を返す。
    十干・十二支それぞれに五行があるが、体感・季節に近い十二支側を
    「年の代表五行」として採用する(丙午年は十干十二支とも火で一致)。
    """
    stem = STEMS[(year - 4) % 10]
    branch = BRANCHES[(year - 4) % 12]
    element = BRANCH_ELEMENT[branch]
    return stem, branch, element, f"{stem}{branch}"


def year_center_star(year: int):
    """九星気学の年家九星(中宮)を返す。
    立春を年境とする厳密な暦ではなく、1/1基準の簡易計算。
    """
    delta = year - REF_YEAR
    star_num = ((REF_STAR - 1 - delta) % 9) + 1
    return star_num, STAR_NAMES[star_num], STAR_ELEMENT[star_num]


def five_element_relation(year_element: str, star_element: str) -> str:
    """年の五行と中宮九星の五行の関係(Layer2:隠れリスク層)を判定する。"""
    if year_element == star_element:
        return "比和(同気が重なり、その属性が増幅されやすい)"
    if GENERATES[year_element] == star_element:
        return "相生:年が星を生む(年のエネルギーが発散・消耗しやすい)"
    if GENERATES[star_element] == year_element:
        return "相生:星が年を生む(年のエネルギーが後押しされやすい)"
    if CONTROLS[year_element] == star_element:
        return "相剋:年が星を剋す(年の勢いが場を抑え込む)"
    if CONTROLS[star_element] == year_element:
        return "相剋:星が年を剋す(隠れたリスクが顕在化しやすい)"
    return "不明"


def get_astro_flags(date_str: str, year: int) -> dict:
    """Layer3(西洋占星術タイミング層)の当日フラグを返す。"""
    path = BASE / f"astro_events_{year}.json"
    result = {
        "mercury_retrograde": False,
        "mercury_retrograde_name": "",
        "saturn_neptune_days_from_exact": "",
    }
    if not path.exists():
        result["mercury_retrograde_name"] = "astroデータ未整備の年"
        return result

    data = json.loads(path.read_text(encoding="utf-8"))
    today = datetime.date.fromisoformat(date_str)

    for period in data.get("mercury_retrograde", []):
        start = datetime.date.fromisoformat(period["start"])
        end = datetime.date.fromisoformat(period["end"])
        if start <= today <= end:
            result["mercury_retrograde"] = True
            result["mercury_retrograde_name"] = period["name"]
            break

    transits = data.get("major_transits", [])
    if transits:
        diffs = [
            (today - datetime.date.fromisoformat(t["exact_date"])).days
            for t in transits
        ]
        result["saturn_neptune_days_from_exact"] = min(diffs, key=abs)

    return result


if __name__ == "__main__":
    import sys

    year = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today().year
    stem, branch, elem, ganzhi = year_ganzhi_element(year)
    star_num, star_name, star_elem = year_center_star(year)
    relation = five_element_relation(elem, star_elem)
    print(f"{year}年: {ganzhi}({elem}) / 中宮={star_name}({star_elem}) / {relation}")
