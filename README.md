# arxiv-ingest

**arXiv の新着論文を毎日自動収集し、構造化された研究ノートに変換する CLI + GitHub Actions テンプレート。**

Claude Code と組み合わせることで、論文の要約・クレーム抽出・wiki ページの生成まで自動化できます。

## 特徴

- **キーワードベース収集** — `config.yaml` にキーワードを書くだけ
- **3層構造の出力** — `sources/`（メタ）・`evidence/`（クレーム抽出）・`wiki/`（要約）を分離して生成
- **Claude Code 連携** — `/arxiv-ingest` スキルで LLM による evidence・wiki の自動記入
- **GitHub Actions 対応** — 月〜金 JST 10:00 に自動実行、`workflow_dispatch` で手動実行も可
- **任意の wiki に出力** — `output_dir` を変更するだけで出力先を切り替え可能

## クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/yamadan96/arxiv-ingest
cd arxiv-ingest

# 2. 依存関係をインストール
uv sync

# 3. キーワードを設定
cp config.yaml.example config.yaml
vim config.yaml

# 4. 論文を取得してスケルトンを生成
uv run python scripts/fetch.py
uv run python scripts/generate.py
```

## 設定（config.yaml）

```yaml
output_dir: "../research-wiki"  # 出力先ディレクトリ
max_results: 20                 # キーワードあたりの最大取得件数
days_back: 7                    # 何日前までの論文を取得するか

keywords:
  - "Vision-Language Model"
  - "LoRA fine-tuning"
  - "LLM reasoning"

# arXiv カテゴリ → wiki カテゴリのマッピング
category_map:
  cs.CV: "Multimodal"
  cs.CL: "Post_Training"
  cs.LG: "Architecture"
  cs.AI: "Reasoning"
  cs.RO: "Physical_AI"
  stat.ML: "Pretraining"
```

## Claude Code スキルとして使う

`.claude/commands/arxiv-ingest.md` をあなたの Claude Code 設定にコピーすると、
`/arxiv-ingest` コマンドで論文収集から wiki 記入まで一括実行できます。

```bash
cp .claude/commands/arxiv-ingest.md ~/.claude/commands/
# または プロジェクトの .claude/commands/ にコピー
```

実行後、Claude が各論文の PDF を読んで `evidence/` と `wiki/` を自動記入します。

## GitHub Actions で毎日自動実行

### セットアップ

1. このリポジトリを fork または テンプレートとして使用
2. GitHub で Fine-grained PAT を作成（wiki リポジトリへの Write 権限）
3. リポジトリの Settings → Secrets and variables → Actions に以下を登録：

   | 種別 | 名前 | 値 |
   |---|---|---|
   | Secret | `GH_PAT` | 作成した PAT |
   | Variable | `WIKI_REPO` | `your-name/research-wiki` |

4. Actions タブ → `Daily arXiv Ingest` → `Run workflow` で動作確認

### スケジュール

- **自動実行**: 月〜金 JST 10:00（`cron: '0 1 * * 1-5'`）
- **手動実行**: `workflow_dispatch` で `days_back` を指定して実行

## 出力フォーマット

[research-wiki](https://github.com/yamadan96/research-wiki) の SCHEMA に準拠した Markdown ファイルを生成します。

```
output_dir/
├── sources/{Category}/{slug}.md   # メタデータ（不変）
├── evidence/{Category}/{slug}.md  # クレーム・数値の抽出
└── wiki/papers/{Category}/{slug}.md  # 要約・解釈
```

## 動作要件

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Claude Code（`/arxiv-ingest` スキルを使う場合）

## ライセンス

MIT
