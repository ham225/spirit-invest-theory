#!/usr/bin/env python3
"""data/log.csv を集計し、insights/backtest.md にレポートを書き出す。

LLMは使わない単純な記述統計のみ(無料・決定的・毎回再現可能)。
理論(Layer3:水星逆行・土星海王星の合)の"当たり外れ"の傾向を、
データが貯まるごとに更新していく。
"""
import csv
import statistics
from pathlib import Path

from theory_score import ALERT_BANDS, alert_score

BASE = Path(__file__).resolve().parent
LOG = BASE / "data" / "log.csv"
OUT = BASE / "insights" / "backtest.md"

ASSETS = ["nikkei225", "tokyo_electron", "usdjpy", "gold"]
MIN_ROWS = 20
ORB_DAYS = 14


def load_rows():
    if not LOG.exists():
        return []
    with open(LOG, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def mean_abs(values):
    values = [abs(v) for v in values if v is not None]
    return round(statistics.mean(values), 3) if values else None


def build_table(rows, split_fn):
    """split_fn(row) -> True/False/None でグループ分けし、資産別の平均絶対変化率を表にする。"""
    lines = ["| 資産 | 該当期間 | 通常時 | 差 | サンプル数(該当/通常) |", "|---|---|---|---|---|"]
    for asset in ASSETS:
        in_vals, out_vals = [], []
        for r in rows:
            chg = to_float(r.get(f"{asset}_chg_pct"))
            if chg is None:
                continue
            flag = split_fn(r)
            if flag is None:
                continue
            (in_vals if flag else out_vals).append(chg)
        in_avg = mean_abs(in_vals)
        out_avg = mean_abs(out_vals)
        diff = round(in_avg - out_avg, 3) if (in_avg is not None and out_avg is not None) else None
        lines.append(f"| {asset} | {in_avg} | {out_avg} | {diff} | {len(in_vals)}/{len(out_vals)} |")
    return "\n".join(lines)


def build_band_table(rows):
    """3SM理論の警戒レベル(平常〜厳戒)別に、資産別の平均絶対変化率を表にする。"""
    bands = [name for _, name in reversed(ALERT_BANDS)]
    by_band = {}
    for r in rows:
        band = alert_score(r["date"])["band"]
        by_band.setdefault(band, []).append(r)
    lines = ["| 資産 | " + " | ".join(bands) + " |", "|---|" + "---|" * len(bands)]
    for asset in ASSETS:
        cells = []
        for band in bands:
            vals = [to_float(r.get(f"{asset}_chg_pct")) for r in by_band.get(band, [])]
            cells.append(str(mean_abs(vals)))
        lines.append(f"| {asset} | " + " | ".join(cells) + " |")
    counts = [str(len(by_band.get(band, []))) for band in bands]
    lines.append("| (サンプル日数) | " + " | ".join(counts) + " |")
    return "\n".join(lines)


def main():
    rows = load_rows()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    if len(rows) < MIN_ROWS:
        OUT.write_text(
            "# バックテストレポート\n\n"
            f"データがまだ{len(rows)}日分しかありません(最低{MIN_ROWS}日分たまると自動生成されます)。\n",
            encoding="utf-8",
        )
        print(f"データ不足({len(rows)}/{MIN_ROWS})のためプレースホルダーのみ出力しました")
        return

    retro_table = build_table(
        rows, lambda r: r.get("mercury_retrograde") == "True"
    )

    def orb_flag(r):
        days = to_float(r.get("saturn_neptune_days_from_exact"))
        if days is None:
            return None
        return abs(days) <= ORB_DAYS

    orb_table = build_table(rows, orb_flag)
    band_table = build_band_table(rows)

    content = f"""# バックテストレポート

集計対象: {len(rows)}日分(このレポートは毎回自動で作り直されます)

## Layer3: 水星逆行中 vs 通常時の平均絶対変化率(%)

{retro_table}

## Layer3: 土星海王星の合(前後{ORB_DAYS}日)vs 通常時の平均絶対変化率(%)

{orb_table}

## 統合: 3SM理論の警戒レベル別・平均絶対変化率(%)

{band_table}

> 反証判定(THEORY.md §6): 250営業日以上たまった時点で「厳戒・警戒」の日の
> 平均絶対変化率が「注意・平常」の日と同等以下なら、Layer3のタイミング仮説は
> 支持されない(理論を守るための後付け修正はしない)。

---

> 注: 単純な記述統計であり、統計的検定(有意差検定)は行っていません。
> サンプル数が少ないうちは偶然のばらつきの影響が大きいので、
> 「差」の数値だけで理論の正しさを判断しないでください。
> データが増えるほど参考値としての精度が上がっていきます。
"""
    OUT.write_text(content, encoding="utf-8")
    print(f"backtest.md を更新しました({len(rows)}日分)")


if __name__ == "__main__":
    main()
