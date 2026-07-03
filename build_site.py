#!/usr/bin/env python3
"""THEORY.md・README.md・insights/articles/*.md・theory_score.py の出力から
静的サイト(docs/)を生成する。LLMは使わず、markdownライブラリでの変換と
テンプレート埋め込みのみの決定的な処理(無料)。

公開する場合は、リポジトリをpublicにしてGitHub Pagesのソースを
`main`ブランチの`/docs`に設定するだけでよい(README.md参照)。
"""
import datetime
from pathlib import Path

import markdown

from theory_score import alert_score, annual_scenario, format_daily

BASE = Path(__file__).resolve().parent
DOCS = BASE / "docs"
ARTICLES_DIR = BASE / "insights" / "articles"

CSS = """
:root { color-scheme: light dark; }
body {
  font-family: -apple-system, "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
  max-width: 780px;
  margin: 0 auto;
  padding: 1.5rem;
  line-height: 1.75;
  background: light-dark(#fafafa, #1a1a1a);
  color: light-dark(#1a1a1a, #eee);
}
nav { margin-bottom: 1.5rem; font-size: 0.9rem; }
nav a { margin-right: 1rem; }
pre {
  background: light-dark(#eee, #2a2a2a);
  padding: 1rem;
  overflow-x: auto;
  border-radius: 6px;
  white-space: pre-wrap;
}
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid light-dark(#ccc, #444); padding: 0.4rem 0.6rem; text-align: left; }
.disclaimer {
  margin-top: 2rem;
  padding: 1rem;
  border-left: 4px solid #a66;
  background: light-dark(#fff3f3, #2a1a1a);
  font-size: 0.9rem;
}
.article-list li { margin-bottom: 0.4rem; }
footer { margin-top: 2rem; font-size: 0.8rem; color: light-dark(#666, #999); }
"""

DISCLAIMER_HTML = """
<div class="disclaimer">
<strong>免責</strong><br>
本内容は特定の銘柄・金融商品・投資手法を推奨または勧誘するものではありません。
干支の五行・九星気学・西洋占星術を経済分析に絡めたエンタメ×経済分析のハイブリッドコンテンツであり、
単体で投資判断を行わないでください。市場データはyfinance(Yahoo Finance)経由の参考値であり、
遅延・欠損の可能性があります。本内容をもとに生じたいかなる損失についても責任を負いかねます。
</div>
"""

NAV_HTML = """<nav><a href="index.html">トップ</a><a href="theory.html">理論定義</a><a href="backtest.html">バックテスト</a></nav>"""


def page(title: str, body_html: str, nav: bool = True) -> str:
    nav_html = NAV_HTML if nav else ""
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
{nav_html}
{body_html}
<footer>自動生成サイト(GitHub Actions・LLM不使用)。ソース: theory_score.py / build_site.py</footer>
</body>
</html>"""


def render_markdown(text: str) -> str:
    return markdown.markdown(text, extensions=["tables", "fenced_code"])


def build_theory_page():
    text = (BASE / "THEORY.md").read_text(encoding="utf-8")
    html = render_markdown(text)
    (DOCS / "theory.html").write_text(page("理論定義 | 三層スピリチュアル・マーケット理論(3SM理論)", html), encoding="utf-8")


def build_backtest_page():
    path = BASE / "insights" / "backtest.md"
    text = path.read_text(encoding="utf-8") if path.exists() else "# バックテストレポート\n\nまだ生成されていません。"
    html = render_markdown(text)
    (DOCS / "backtest.html").write_text(page("バックテスト | 三層スピリチュアル・マーケット理論(3SM理論)", html), encoding="utf-8")


def build_article_pages() -> list[tuple[str, str]]:
    articles_out = DOCS / "articles"
    articles_out.mkdir(parents=True, exist_ok=True)
    entries = []
    if not ARTICLES_DIR.exists():
        return entries
    for md_path in sorted(ARTICLES_DIR.glob("*.md"), reverse=True):
        date = md_path.stem
        html = render_markdown(md_path.read_text(encoding="utf-8"))
        out_path = articles_out / f"{date}.html"
        out_path.write_text(page(f"{date}の記事 | 三層スピリチュアル・マーケット理論(3SM理論)", html), encoding="utf-8")
        entries.append((date, f"articles/{date}.html"))
    return entries


def build_index(articles: list[tuple[str, str]], today: datetime.date):
    daily_text = format_daily(alert_score(today.isoformat()))
    yearly_html = render_markdown(annual_scenario(today.year))
    score_html = f"<h2>本日の警戒レベル</h2>\n<pre>{daily_text}</pre>\n{yearly_html}"

    if articles:
        items = "\n".join(f'<li><a href="{href}">{date}</a></li>' for date, href in articles)
        articles_html = f'<h2>日次記事</h2>\n<ul class="article-list">\n{items}\n</ul>'
    else:
        articles_html = "<h2>日次記事</h2>\n<p>まだ記事がありません。</p>"

    body = f"""
<h1>三層スピリチュアル・マーケット理論(3SM理論)</h1>
<p>通称「宙読み相場」。干支五行・九星気学・西洋占星術を掛け合わせた相場理論の検証記録。
詳しい理論定義は<a href="theory.html">理論定義ページ(THEORY.md)</a>、
自動計算の仕組みは<a href="https://github.com/ham225/spirit-invest-theory">リポジトリのREADME</a>を参照。</p>
{score_html}
{articles_html}
{DISCLAIMER_HTML}
<p style="font-size:0.8rem;color:#888;">最終更新: {today.isoformat()}</p>
"""
    (DOCS / "index.html").write_text(page("三層スピリチュアル・マーケット理論(3SM理論)", body, nav=False), encoding="utf-8")


def main():
    DOCS.mkdir(exist_ok=True)
    today = datetime.date.today()
    build_theory_page()
    build_backtest_page()
    articles = build_article_pages()
    build_index(articles, today)
    print(f"{DOCS} にサイトを生成しました({len(articles)}件の記事)")


if __name__ == "__main__":
    main()
