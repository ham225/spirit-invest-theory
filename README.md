# 三層スピリチュアル・マーケット理論(3SM理論)プロジェクト

通称「宙読み相場」。新規収益化企画候補 兼 自分の投資判断の参考メモ。
理論そのものの定義・根拠・参考文献は [THEORY.md](THEORY.md) を参照。このファイルは自動化の仕組み・サイトの説明。

**2026-07-04: 日次記事+年間スコアカードを表示する自動更新サイト(`build_site.py` → `docs/`)を追加し、リポジトリをpublicにしてGitHub Pagesで公開した。**

**2026-07-03: 理論を v1.0 として確立([THEORY.md](THEORY.md))。理論名を決定し、Layer1〜3のスコアリングを定量化(警戒レベル S = 10AR + 20T)、バックテスト・日次記事に統合した。**

**2026-07-02: 毎日データを取りながら理論を検証・改善していく仕組みを構築した(GitHub Actions)。**

---

## 毎日のデータ収集+バックテスト+サイト更新の仕組み

平日 日本時間18:30 に GitHub Actions が自動で動き、市場データと理論シグナル(Layer1/2/3)を
`data/log.csv` に1日1行ずつ記録し、日次記事とサイトを再生成する。LLMは使わず、無料のデータ取得(yfinance)と
決定的な計算のみなので運用コストは¥0。

| ファイル | 役割 |
|---|---|
| `THEORY.md` | **理論の正式文書(v1.0)**。仮説・スコア定義・統合ロジック・年間シナリオ生成手順・反証条件 |
| `theory_signals.py` | 干支・五行・九星気学(Layer1/2)を計算式で自動算出。西洋占星術(Layer3)は年ごとの暦データを参照 |
| `theory_score.py` | THEORY.mdの計算式の実装。日次警戒レベル(`python theory_score.py 2026-11-01`)と年間シナリオ(`python theory_score.py --year 2026`)を出力 |
| `astro_events_<year>.json` | その年の水星逆行期間・主要トランジット日程(手入力。**新しい年になったら追加が必要**) |
| `fetch_data.py` | 日経平均・東京エレクトロン(火=AI半導体の代表)・ドル円(水)・金(資源)の値動き+その日の理論シグナルを取得し `data/log.csv` に追記 |
| `backtest.py` | `data/log.csv` を集計し、水星逆行中/通常時・土星海王星の合の前後/通常時で値動きの大きさを比較した `insights/backtest.md` を再生成(データが20日分たまるまではプレースホルダー) |
| `generate_article.py` | 最新日のデータから note投稿用の日次記事を `insights/articles/YYYY-MM-DD.md` に生成 |
| `build_site.py` | `THEORY.md`・`insights/articles/*.md`・`insights/backtest.md`・`theory_score.py --year <実行年>` の出力をまとめた静的サイトを `docs/` に生成 |
| `.github/workflows/daily.yml` | 平日18:30(JST)に上記スクリプトを自動実行し、結果をリポジトリにコミット・プッシュ |
| `data/log.csv` | 日次ログ(自動・追記のみ) |
| `insights/backtest.md` | 集計レポート(自動・毎回上書き) |
| `insights/articles/*.md` | 日次記事(自動・追記) |
| `docs/` | 自動生成される静的サイト本体(`index.html` 他、GitHub Pagesで公開中) |

### 使い方
- 今日のデータ・理論との照合結果を見たい: `insights/backtest.md` を開く(データが貯まるほど中身が充実する、株初動ピックアップの「法則性.md」と同じ考え方)
- 特定日の警戒レベルを見たい: `python theory_score.py 2026-11-01`
- 年間シナリオ(警戒カレンダー)を見たい: `python theory_score.py --year 2026`
- サイトをローカルで見たい: `python build_site.py` 実行後、`docs/index.html` をブラウザで開く
- 手動で今すぐ全体を実行したい: GitHubリポジトリの Actions タブ → 「毎日データ収集+バックテスト更新」→ Run workflow
- 来年以降も使う場合: `astro_events_2027.json` のように新しい年のトランジット暦を追加すること(自動計算できるのはLayer1・Layer2まで)

### 自動更新サイトの公開
リポジトリをpublicにし、GitHub Settings → Pages → Source を `main` ブランチの `/docs` に設定して公開している(暮らしガイドと同じ方式)。投資判断メモとしての性質があるため、内容はすべて「エンタメ×経済分析のハイブリッドコンテンツ」であり投資助言ではない旨の免責を明記している([THEORY.md](THEORY.md#7-免責)参照)。

### 免責
市場データはyfinance(Yahoo Finance)経由の参考値であり、遅延・欠損の可能性があります。
このリポジトリの内容は投資助言ではありません(詳細は [THEORY.md](THEORY.md) 末尾の免責条項を参照)。

## 次の検討事項(未決定)
- ~~公開形式~~ → **済**(2026-07-04、リポジトリをpublic化しGitHub Pagesで公開)
- ~~Layer1〜3のスコアリングの定量化~~ → **済**(2026-07-03、THEORY.md §2〜3。S = 10AR + 20T)
- ~~理論名の最終決定~~ → **済**(2026-07-03、3SM理論/宙読み相場)
- note等での手動記事化、株初動ピックアップへの追加シグナル化は未着手
