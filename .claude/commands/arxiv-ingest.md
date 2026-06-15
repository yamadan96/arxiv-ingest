# /arxiv-ingest

arXivから論文を収集し、research-wikiへ自動取り込みするワークフロー。

## 実行ステップ

### Step 1: 論文を収集する

```bash
cd ~/workspace/arxiv-ingest
uv run python scripts/fetch.py
```

`data/fetched.json` に論文リストが保存される。

### Step 2: スケルトンファイルを生成する

```bash
uv run python scripts/generate.py
```

`research-wiki/sources/{Category}/{slug}.md`（メタデータ）と
`research-wiki/evidence/{Category}/{slug}.md`（空のテンプレート）と
`research-wiki/wiki/papers/{Category}/{slug}.md`（空のテンプレート）が作成される。

### Step 3: 各論文の evidence と wiki を Claude が記入する

`data/fetched.json` を読み込み、各論文について以下を実行する：

1. 論文のアブストラクト（`data/fetched.json` の `abstract` フィールド）を読む
2. PDF URL（`pdf_url` フィールド）から論文を取得して内容を把握する（可能な場合）
3. `research-wiki/evidence/{Category}/{slug}.md` を更新する：
   - 主要な主張（3〜5点）
   - 主要な貢献
   - 制限・注意点
   - ベンチマーク結果（記載があれば）
4. `research-wiki/wiki/papers/{Category}/{slug}.md` を更新する：
   - ソースからの事実（evidence の要点）
   - 現時点の解釈（手法の意義・他研究との関係）
   - 関連ページ（既存の wiki ページへのリンク）
   - 未解決の問い

### Step 4: インデックスを更新する

`research-wiki/wiki/index.md` と `research-wiki/index/recent.md` に追加した論文を記録する。

`research-wiki/log.md` に以下の形式で追記する：

```
## {今日の日付}

- **論文追加**: {タイトル} ({著者第一著者} et al., {年})
  - `sources/{Category}/{slug}.md` 作成
  - `evidence/{Category}/{slug}.md` 作成
  - `wiki/papers/{Category}/{slug}.md` 作成
```

## 設定変更

キーワードや出力先は `~/workspace/arxiv-ingest/config.yaml` を編集する。

## 注意

- `evidence/` と `wiki/` のテンプレートに `（Claude Code が論文を読んで記入）` と書いてある箇所をすべて実際の内容に書き換えること
- アブストラクトだけで十分に理解できる論文は PDF 取得を省略してよい
- 既存のファイルが存在する場合は上書きせず、差分を確認してから更新する
