# arxiv-ingest

[![Tests](https://github.com/yamadan96/arxiv-ingest/actions/workflows/tests.yml/badge.svg)](https://github.com/yamadan96/arxiv-ingest/actions/workflows/tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/arxiv-ingest)](https://pypi.org/project/arxiv-ingest/)
[![Python 3.11+](https://img.shields.io/pypi/pyversions/arxiv-ingest)](https://pypi.org/project/arxiv-ingest/)

**キーワードで arXiv 論文を自動収集し、構造化されたリサーチノートにスキャフォールドするCLIツール。**

スタンドアローンな CLI として動作し、Claude Code と連携した LLM 自動要約、GitHub Actions による毎日の自動収集にも対応。

> English README: [README.md](README.md)

## 特徴

- **キーワード収集** — `config.yaml` にトピックを書くだけ、コード不要
- **3層 wiki 構造** — `sources/`（メタデータ）· `evidence/`（エビデンス）· `wiki/`（統合解釈）
- **安全な再実行** — 手動編集済みファイルは絶対に上書きしない
- **LLM 自動要約** — `--summarize` で Claude API が各セクションを自動記入
- **日付フィルタ** — `--since=YYYY-MM-DD` で特定期間のみ収集
- **閲覧ツール** — `list`, `status`, `search` でコーパス管理
- **エクスポート** — GitHub Issues・BibTeX・CSV 形式に対応
- **Webhook 通知** — Slack / Discord に新着論文サマリを投稿
- **Obsidian 統合** — `[[wikilinks]]` とグラフビュー連携
- **Quartz 統合** — [Quartz v4](https://quartz.jzhao.xyz/) 静的サイトに直接公開
- **インデックス自動更新** — 実行のたびに `index/recent.md`・`log.md`・`index/peer-review.md` を追記
- **GitHub Actions テンプレート** — 平日毎朝自動実行、手動 `workflow_dispatch` にも対応

## クイックスタート

```bash
pip install arxiv-ingest

# wiki ディレクトリと設定ファイルを作成
arxiv-ingest init              # config.yaml + research-wiki/ を生成

# config.yaml のキーワードを編集してから:
arxiv-ingest run               # fetch + generate を一括実行
```

ソースから使う場合:

```bash
git clone https://github.com/yamadan96/arxiv-ingest
cd arxiv-ingest
uv sync
arxiv-ingest init
```

## 設定 (`config.yaml`)

```yaml
output_dir: "../research-wiki"   # wiki ディレクトリへのパス
max_results: 20                  # キーワードあたりの最大論文数
days_back: 7                     # 何日前まで遡るか

keywords:
  - "Vision-Language Model transformer"
  - "LoRA PEFT fine-tuning language model"
  - "LLM reasoning chain-of-thought"

# 許可する arXiv カテゴリ:
allowed_arxiv_categories: [cs.CV, cs.CL, cs.LG, cs.AI, cs.RO, stat.ML]

# プライマリカテゴリの制限（トピックずれを防ぐ）:
require_primary_in: [cs.CV, cs.CL, cs.AI, cs.RO, stat.ML]

# arXiv カテゴリ → wiki フォルダ名 のマッピング:
category_map:
  cs.CV: "Multimodal"
  cs.CL: "Post_Training"
  cs.AI: "Reasoning"
  cs.RO: "Physical_AI"
  stat.ML: "Pretraining"

# 任意: Slack / Discord に新着論文を通知
# webhook_url: "https://hooks.slack.com/services/..."
```

全オプションは `config.yaml.example` を参照。

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `init [wiki-dir]` | `config.yaml` と wiki ディレクトリを作成 |
| `fetch` | arXiv から論文を収集 → `data/fetched.json` |
| `generate` | `fetched.json` からスケルトンファイルを生成 |
| `run` | `fetch` + `generate` を一括実行 |
| `list` | `fetched.json` の論文一覧を表示 |
| `status` | evidence・wiki の記入進捗を表示 |
| `search <term>` | ローカル wiki ファイルの全文検索 |
| `embed` | セマンティック検索用の埋め込みベクトルを生成（`[semantic]` が必要） |
| `export` | GitHub Issues・BibTeX・CSV にエクスポート |
| `open <id\|slug>` | 論文の arXiv ページをブラウザで開く |
| `version` | インストール済みバージョンを表示 |

### 主要フラグ

```bash
arxiv-ingest fetch --since=2025-01-01   # 特定日以降の論文を収集
arxiv-ingest fetch --dry-run            # 書き込みなしでプレビュー

arxiv-ingest generate --obsidian        # [[wikilinks]] モード（Obsidian 向け）
arxiv-ingest generate --quartz          # Quartz 互換ファイルを出力
arxiv-ingest generate --summarize       # Claude API で自動要約
arxiv-ingest generate --dry-run         # 書き込みなしでプレビュー
arxiv-ingest generate --limit=5         # 最大5件の論文のみ生成

arxiv-ingest list --category=Multimodal # カテゴリでフィルタ
arxiv-ingest list --unfilled            # 未記入の論文のみ表示
arxiv-ingest list --limit=10            # 最大10件表示
arxiv-ingest list --json                # JSON 出力（jq にパイプ可能）

arxiv-ingest search attention --json    # 検索結果を JSON で出力

arxiv-ingest embed                          # セマンティック検索用の埋め込みを生成
arxiv-ingest search --semantic "vision transformer"  # セマンティック類似検索
arxiv-ingest search --semantic "LoRA" --limit=5      # 上位5件のセマンティック検索

arxiv-ingest export --format=bibtex           # BibTeX 出力（gh 不要）
arxiv-ingest export --format=bibtex --limit=5 # 上位5件を BibTeX で出力
arxiv-ingest export --format=csv              # CSV 出力
arxiv-ingest export --repo=owner/repo          # GitHub Issues: 対象リポジトリ指定
arxiv-ingest export --dry-run                  # GitHub Issues: 作成せずプレビュー

arxiv-ingest open 2501.00001v1          # arXiv ID でブラウザ起動
arxiv-ingest open attention-is-all      # wiki スラッグでブラウザ起動
```

## 出力ディレクトリ構造（デフォルト）

```
output_dir/
├── SCHEMA.md                         # wiki 運用規約
├── log.md                            # 変更ログ（実行のたびに自動追記）
├── sources/{Category}/{slug}.md      # メタデータ — 一度書いたら上書きなし
├── evidence/{Category}/{slug}.md     # エビデンス・ベンチマーク — 手動記入
├── wiki/
│   ├── index.md                      # トピックカタログ（手動管理）
│   └── papers/{Category}/{slug}.md   # 統合解釈・関連ページ
├── figures/{Category}/{slug}/        # 論文図表（手動配置）
├── decisions/                        # 採用・棄却の判断ログ
├── presentations/                    # 勉強会発表資料
└── index/
    ├── recent.md                     # 最近の追加（実行のたびに自動追記）
    ├── peer-review.md                # 査読状況一覧（実行のたびに自動追記）
    ├── topics.md                     # トピック索引（手動管理）
    ├── models.md                     # モデル索引（手動管理）
    └── open-questions.md             # 未解決の問い（手動管理）
```

`evidence/` と `wiki/` のファイルは、未入力テンプレートの sentinel が含まれる場合のみ再生成されます。手動編集済みのファイルは再実行しても安全です。

## Obsidian 連携

[Obsidian](https://obsidian.md/) ユーザーは wiki ディレクトリを vault として開くことで、論文間のグラフビュー連携が使えます。

```bash
# 初回セットアップ: .obsidian/app.json を作成（wikilinks 有効化）
arxiv-ingest init --obsidian my-research-wiki

# 日常使用: Markdown リンクの代わりに [[wikilinks]] を生成
arxiv-ingest run --obsidian
```

`--obsidian` が変えること:
- `wiki/papers/` ページが `[source](path/to/file.md)` の代わりに `[[slug]]` を使用
- `evidence/` ページに `> Source paper: [[slug]]` バックリンクを追加

## Quartz 連携

[Quartz v4](https://quartz.jzhao.xyz/) ユーザーは、グラフビュー・バックリンク・タグページ付きの静的サイトに論文を直接公開できます。

```bash
# 初回セットアップ: content/papers/ と content/templates/ を作成
arxiv-ingest init --quartz my-quartz-site

# 日常使用: content/papers/{YYYY}/{slug}.md を生成
arxiv-ingest run --quartz

# LLM 自動記入付き（全セクションを日本語で自動入力）
arxiv-ingest run --quartz --summarize
```

生成されるファイル例（`content/papers/2025/attention-is-all-you-need.md`）:

```yaml
---
title: "Attention Is All You Need"
authors: "Vaswani, Ashish, Shazeer, Noam, ..."
venue: "arXiv:2501.00001"        # journal_ref があれば "ICLR 2022 / arXiv:..." 形式
year: 2025
url: "https://arxiv.org/abs/2501.00001"
code: ""
read_date: 2026-06-16
status: reading
tags:
  - Post_Training
  - transformer
---
```

セクション: TL;DR · 背景・問題設定 · 手法 · 実験 · 強み · 弱み・未解決の問い · 関連研究とのつながり · 自分の研究・実装への示唆

## LLM 自動要約

オプションの `anthropic` 依存関係をインストールし、API キーを設定します:

```bash
pip install 'arxiv-ingest[summarize]'
export ANTHROPIC_API_KEY=sk-ant-...

arxiv-ingest generate --summarize          # evidence/ を自動記入（デフォルトモード）
arxiv-ingest generate --quartz --summarize # Quartz セクションを日本語で自動記入
```

Claude が各論文のアブストラクトを読んでファイルを事前入力します。手動編集済みのファイルは上書きされません。

## Webhook 通知

`config.yaml` に `webhook_url` を追加すると、Slack または Discord に新着論文サマリが届きます:

```yaml
webhook_url: "https://hooks.slack.com/services/T.../B.../..."
# Discord の場合:
# webhook_url: "https://discord.com/api/webhooks/..."
```

Webhook は non-fatal です — 失敗しても実行は継続されます。

## Claude Code との連携

コマンドファイルをコピーして `/arxiv-ingest` スラッシュコマンドを有効化:

```bash
cp .claude/commands/arxiv-ingest.md ~/.claude/commands/
```

`arxiv-ingest run` 実行後に Claude Code で `/arxiv-ingest` を呼ぶと、Claude が各論文のアブストラクト（PDF が利用可能な場合は本文も）を読んで `evidence/` と `wiki/` ファイルを自動記入します。

## GitHub Actions: 毎日の自動収集

### セットアップ

1. このリポジトリを fork またはテンプレートとして使用
2. wiki リポジトリへの **Write** アクセスを持つ GitHub Fine-grained PAT を作成
3. **Settings → Secrets and variables → Actions** に追加:

   | 種別 | 名前 | 値 |
   |------|------|-----|
   | Secret | `GH_PAT` | 作成した PAT（wiki/paper-survey リポジトリへの Write 権限が必要） |
   | Variable | `WIKI_REPO` | `your-name/research-wiki`（3層 wiki モード用） |
   | Variable | `PAPER_SURVEY_REPO` | `your-name/paper-survey`（Quartz モード用、任意） |

4. **Actions → Daily arXiv Ingest → Run workflow** で動作確認

### スケジュール

- **自動**: 平日 UTC 01:00（JST 10:00） — `cron: '0 1 * * 1-5'`
- **手動**: `workflow_dispatch`（`days_back`・`summarize`・`quartz` を指定可能）

### Quartz サイトへの自動デプロイ

`workflow_dispatch` で `quartz: true` にすると、Quartz サイトに直接 push できます:

```
Actions → Daily arXiv Ingest → Run workflow → quartz: ✓
```

`PAPER_SURVEY_REPO` の `content/papers/{YYYY}/{slug}.md` にコミットされ、
Quartz の deploy ワークフローが自動的にサイトをリビルドします。

## 動作要件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)（推奨）または pip

## ライセンス

MIT
