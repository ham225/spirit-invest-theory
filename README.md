# スピリチュアル投資理論(仮)プロジェクト

新規収益化企画候補 兼 自分の投資判断の参考メモ。
理論そのものの定義・根拠・参考文献は [THEORY.md](THEORY.md) を参照。このファイルは自動化の仕組み・サイトの説明。

**2026-07-02: 毎日データを取りながら理論を検証・改善していく仕組みを構築した(GitHub Actions、Private repo)。**
**2026-07-03: スコアリングを定量化する `theory_score.py` と、日次記事+スコアを表示する自動更新サイト(`build_site.py` → `docs/`)を追加した。公開方法(Pages公開/現状維持)は未確定のため、当面はリポジトリ内に静的サイトを生成するだけに留めている。**

---

## 毎日のデータ収集+バックテスト+サイト更新の仕組み

平日 日本時間18:30 に GitHub Actions が自動で動き、市場データと理論シグナル(Layer1/2/3)を
`data/log.csv` に1日1行ずつ記録し、日次記事とサイトを再生成する。LLMは使わず、無料のデータ取得(yfinance)と
決定的な計算のみなので運用コストは¥0。

| ファイル | 役割 |
|---|---|
| `theory_signals.py` | 干支・五行・九星気学(Layer1/2)を計算式で自動算出。西洋占星術(Layer3)は年ごとの暦データを参照 |
| `theory_score.py` | Layer1/Layer2を1〜5のスコアに定量化し、Layer3の警戒ウィンドウと合わせて年単位のスコアカードを出力(`--year YYYY`)。ロジックは [THEORY.md](THEORY.md#スコアリング定量化) 参照 |
| `astro_events_<year>.json` | その年の水星逆行期間・主要トランジット日程(手入力。**新しい年になったら追加が必要**) |
| `fetch_data.py` | 日経平均・東京エレクトロン(火=AI半導体の代表)・ドル円(水)・金(資源)の値動き+その日の理論シグナルを取得し `data/log.csv` に追記 |
| `backtest.py` | `data/log.csv` を集計し、水星逆行中/通常時・土星海王星の合の前後/通常時で値動きの大きさを比較した `insights/backtest.md` を再生成(データが20日分たまるまではプレースホルダー) |
| `generate_article.py` | 最新日のデータから note投稿用の日次記事を `insights/articles/YYYY-MM-DD.md` に生成 |
| `build_site.py` | `THEORY.md`・`README.md`・`insights/articles/*.md`・`theory_score.py --year <実行年>` の出力をまとめた静的サイトを `docs/` に生成 |
| `.github/workflows/daily.yml` | 平日18:30(JST)に上記スクリプトを自動実行し、結果をリポジトリにコミット・プッシュ |
| `data/log.csv` | 日次ログ(自動・追記のみ) |
| `insights/backtest.md` | 集計レポート(自動・毎回上書き) |
| `insights/articles/*.md` | 日次記事(自動・追記) |
| `docs/` | 自動生成される静的サイト本体(`index.html` 他) |

### 使い方
- 今日のデータ・理論との照合結果を見たい: `insights/backtest.md` を開く(データが貯まるほど中身が充実する、株初動ピックアップの「法則性.md」と同じ考え方)
- 年単位のスコアカードを見たい: `python theory_score.py --year 2026`
- サイトをローカルで見たい: `python build_site.py` 実行後、`docs/index.html` をブラウザで開く
- 手動で今すぐ全体を実行したい: GitHubリポジトリの Actions タブ → 「毎日データ収集+バックテスト更新」→ Run workflow
- 来年以降も使う場合: `astro_events_2027.json` のように新しい年のトランジット暦を追加すること(自動計算できるのはLayer1・Layer2まで)

### 自動更新サイトの公開について(未確定)
現状、`docs/` はリポジトリ内に生成されるだけで外部には公開していない(GitHub Pagesの無料枠はpublicリポジトリのみ対応のため、privateのまま公開するには別途Cloudflare Pages連携などが必要)。
公開する場合の最短ルート: このリポジトリをpublicにし、GitHub Settings → Pages → Source を `main` ブランチの `/docs` に設定するだけで良い(暮らしガイドと同じ方式)。投資判断メモとしての性質上、公開はユーザー判断が必要なため保留中。

### 免責
市場データはyfinance(Yahoo Finance)経由の参考値であり、遅延・欠損の可能性があります。
このリポジトリの内容は投資助言ではありません(詳細は [THEORY.md](THEORY.md) 末尾の免責条項を参照)。

## 次の検討事項(未決定)
- 公開形式: このままprivateで保留 / リポジトリをpublicにしてGitHub Pagesで公開 / note等での手動記事 / 株初動ピックアップへの追加シグナル
- 理論名の最終決定(候補は [THEORY.md](THEORY.md#理論名の候補) 参照)
