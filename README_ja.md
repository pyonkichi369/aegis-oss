[English](README.md) | [日本語](README_ja.md)

<div align="center">

# AEGIS

### ガバナンスファーストのAIエージェントフレームワーク

**あなたのAIエージェントには、監督が必要です。**<br>
構造化されたボードルーム討論。必須のレッドチーム。実際に機能するガバナンスガードレール。

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-32_passed-brightgreen.svg)]()
[![PyPI](https://img.shields.io/badge/PyPI-aegis--gov-orange.svg)](https://pypi.org/project/aegis-gov/)

[クイックスタート](#クイックスタート) · [なぜAEGIS？](#なぜaegis) · [CLI](#cli) · [GitHub Action](#github-action) · [API](#api) · [コントリビュート](CONTRIBUTING.md)

</div>

---

## 60秒デモ

```bash
pip install aegis-gov
export ANTHROPIC_API_KEY=sk-...

# 任意の意思決定に対してガバナンスレビューを実行
aegis convene "Should we mass-email all users about the new feature?" --category TACTICAL

# ガバナンスルールに対してアクションを検証（LLM不要）
aegis check DevOps deploy --context environment=production tests_passed=true review_approved=false
# → ESCALATE_TO_HUMAN: Production deployment requires passing tests and review approval
```

```python
from aegis_gov import Boardroom

boardroom = Boardroom()
result = boardroom.convene(
    topic="Should we migrate to microservices?",
    category="STRATEGIC",
    context={"team_size": 5, "current_arch": "monolith"},
)

print(result.synthesis)       # CEOの最終判断
print(result.vote_summary)    # {"approve": 7, "conditional": 2, "reject": 0, "abstain": 0}
print(result.confidence)      # 0.85
```

## なぜAEGIS？

他のマルチエージェントフレームワークは、AIエージェントが **何かを実行する** ことを支援します。AEGISは、それを **実行すべきかどうか** を判断します。

| | AEGIS | CrewAI | AutoGen | LangGraph | MetaGPT |
|---|:---:|:---:|:---:|:---:|:---:|
| ガバナンスルールエンジン | **対応** | 非対応 | 非対応 | 非対応 | 非対応 |
| 必須レッドチームレビュー | **対応** | 非対応 | 非対応 | 非対応 | 非対応 |
| 憲法的マニフェスト | **対応** | 非対応 | 非対応 | 非対応 | 非対応 |
| 意思決定監査証跡 | **対応** | 一部対応 | 非対応 | 非対応 | 一部対応 |
| 判定の強制執行（BLOCK/HALT） | **対応** | 非対応 | 非対応 | 非対応 | 非対応 |
| ヒューマンエスカレーションゲート | **対応** | 手動 | 手動 | 手動 | 手動 |
| LLM非依存 | **対応** | 対応 | 対応 | 対応 | 非対応 |

**AEGISはこれらのフレームワークの代替ではありません。** 既存のフレームワークの上に追加するガバナンスレイヤーです。

### 対象ユーザー

- AIエージェントを本番環境にデプロイし、**説明責任と監査証跡** が必要なチーム
- **EU AI Act、NIST AI RMF、ISO 42001** などのコンプライアンス対応を準備している組織
- AIエージェントに不可逆な意思決定を無監視で行わせたくない **すべての開発者**

## 機能

### ボードルームミーティング（6フェーズ）

17のAIエージェントがそれぞれ異なる役割で、すべての意思決定を議論します：

| フェーズ | 内容 |
|---------|------|
| 1. CEO開会 | トピックの分類（CRITICAL/STRATEGIC/TACTICAL/OPERATIONAL）、フォーマットの設定 |
| 2. 経営会議 | 7名のCレベル視点（CEO、CTO、CFO、CRO、CMO、CPO、CDO） |
| 3. アドバイザリー | 8名のスペシャリストがドメイン専門知識を提供 |
| 4. クリティカルレビュー | **レッドチーム + レビュアーがコンセンサスに異議を唱える** |
| 5. オープンディベート | エージェント間の横断的議論 |
| 6. CEO総括 | 投票集計、信頼度スコア、アクションアイテムを含む最終判断 |

### レッドチーム（省略不可）

すべての意思決定はストレステストを受けます。デフォルト設定では、レッドチームを **無効化することはできません**。

- **DevilsAdvocate** -- 前提を疑い、証拠を要求し、隠れたリスクを発見します
- **Skeptic** -- 代替案を探り、プレモーテム分析を行い、集団思考を検知します

### ルールエンジン（5つの組み込みルール）

助言ではなく **強制執行** するガバナンスガードレール：

```python
from aegis_gov import RuleEngine

engine = RuleEngine()

# セルフレビュー → BLOCK（エージェントは自身の作業をレビューできない）
engine.evaluate("Agent", "review", {"author": "Agent"})

# 低信頼度 → FLAG
engine.evaluate("CTO", "approve", {"confidence": 0.3})

# レビュー未承認の本番デプロイ → ESCALATE_TO_HUMAN
engine.evaluate("DevOps", "deploy", {
    "environment": "production",
    "tests_passed": True,
    "review_approved": False,
})
```

| 判定 | アクション |
|------|-----------|
| `PASS` | 通常通り実行 |
| `FLAG` | 警告をログに記録し、注意の上で続行 |
| `BLOCK` | アクションを完全にブロック |
| `ESCALATE_TO_HUMAN` | 人間の承認が必要 |
| `HALT` | すべてのプロセスを即座に停止 |

### ガバナンスマニフェスト

バージョン管理・監査可能な憲法的フレームワーク：
- 人間の主権性 -- 人間が常に最終的な権限を持つ
- 意思決定カテゴリのTTLとレビュー要件
- 役割分離 -- 意思決定者、実装者、レビュアーは別のエンティティ
- すべての意思決定に信頼度スコアの付与が必須

## クイックスタート

### 方法1: pip install（推奨）

```bash
pip install aegis-gov[anthropic]   # または aegis-gov[openai]、aegis-gov[all]
export ANTHROPIC_API_KEY=sk-...

# スターター設定を生成（カスタマイズ可能なルール + エージェント）
aegis init

# 最初のボードルームミーティングを実行
aegis convene "Should we mass-email all users?" --category TACTICAL
```

### 方法2: Docker

```bash
git clone https://github.com/pyonkichi369/aegis-oss.git
cd aegis-oss
cp .env.example .env  # ANTHROPIC_API_KEYを追加
docker compose up
# API: http://localhost:8000/docs
```

### 方法3: ソースから

```bash
git clone https://github.com/pyonkichi369/aegis-oss.git
cd aegis-oss
pip install -e ".[dev]"
aegis convene "Test topic" --category OPERATIONAL
```

## CLI

```
aegis convene "topic"    ボードルームミーティングを実行
aegis review "artifact"  スタンドアロンのレッドチームレビュー
aegis check AGENT ACTION ルールに対してアクションを評価
aegis agents             エージェント一覧を表示
aegis rules              ガバナンスルール一覧を表示
aegis init               スターター設定を生成
aegis version            バージョンを表示
```

`convene` のオプション：
```
--category    OPERATIONAL | TACTICAL | STRATEGIC | CRITICAL（デフォルト: TACTICAL）
--model       LLMモデル（デフォルト: claude-sonnet-4-20250514）
--provider    anthropic | openai（デフォルト: anthropic）
--rounds      ディベートラウンド数（デフォルト: 2）
--output      json | text（デフォルト: text）
```

## GitHub Action

プルリクエストにAIガバナンスレビューを追加できます：

```yaml
# .github/workflows/aegis-review.yml
name: AEGIS Governance Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: pyonkichi369/aegis-oss@v1
        with:
          api-key: ${{ secrets.ANTHROPIC_API_KEY }}
          category: TACTICAL
          fail-on: BLOCK  # BLOCK | ESCALATE | FLAG | never
```

このActionは、PRのdiffに対してボードルームレビューを実行し、判定結果をチェック結果として投稿します。

## API

サーバーの起動: `uvicorn aegis_gov.api:app --reload`

| エンドポイント | メソッド | 説明 |
|--------------|---------|------|
| `/health` | GET | ヘルスチェック（公開） |
| `/api/v1/boardroom` | POST | ボードルームミーティングを実行 |
| `/api/v1/review` | POST | スタンドアロンのレッドチームレビュー |
| `/api/v1/rules/check` | POST | ルールに対してアクションを評価 |
| `/api/v1/rules` | GET | 有効なガバナンスルール一覧 |
| `/api/v1/agents` | GET | カウンシルエージェント一覧 |

認証: `X-API-Key` ヘッダー（環境変数 `AEGIS_API_KEY` で設定）。開発モードでは認証なしでアクセス可能です。

APIドキュメント: `http://localhost:8000/docs`

## カスタマイズ

### ドメイン固有エージェントの追加

```python
from aegis_gov import Boardroom, BoardroomConfig, AgentRole

config = BoardroomConfig(
    custom_agents=[
        AgentRole("HIPAAOfficer", "Compliance", "HIPAA, PHI, healthcare data", "reviewer"),
        AgentRole("MLEngineer", "ML Systems", "Model deployment, A/B testing", "specialist"),
    ],
)
boardroom = Boardroom(config)
```

### カスタムルールの追加（Python）

ルールは `condition` 式を使用し、`agent`、`action`、`context`、`rule` 変数で評価されます：

```python
from aegis_gov import RuleEngine

engine = RuleEngine()
engine.add_rule("budget_gate", {
    "name": "Budget Approval",
    "condition": "context.get('amount', 0) > 10000",
    "verdict": "ESCALATE_TO_HUMAN",
    "message": "Spending over $10K needs CFO approval",
})

# カスタムルールがトリガーされる
result = engine.evaluate("Agent", "purchase", {"amount": 50000})
print(result.final_verdict)  # ESCALATE_TO_HUMAN
```

### YAMLによるカスタムルール

```yaml
# my_rules.yaml
rules:
  - id: pii_gate
    name: PII Access Gate
    condition: "context.get('data_type') == 'PII'"
    verdict: ESCALATE_TO_HUMAN
    message: Accessing PII requires privacy review

  - id: after_hours_block
    name: After Hours Deploy Block
    condition: "action == 'deploy' and context.get('hour', 12) >= 22"
    verdict: BLOCK
    message: No deployments after 10pm
```

```python
engine = RuleEngine(rules_path="my_rules.yaml")
```

### `aegis init` によるセットアップ

```bash
aegis init                    # サンプル付きの aegis.yaml を生成
aegis init --output custom.yaml  # 出力先を指定
# 生成されたファイルを編集後、以下のように使用:
# engine = RuleEngine(rules_path="aegis.yaml")
```

### 任意のLLMとの連携

```python
# OpenAI
boardroom = Boardroom(BoardroomConfig(provider="openai", model="gpt-4o"))

# Ollama（ローカル）
boardroom = Boardroom(BoardroomConfig(
    provider="openai",
    base_url="http://localhost:11434/v1",
    model="llama3",
))
```

## アーキテクチャ

```
aegis-oss/
├── aegis_gov/
│   ├── council/
│   │   ├── boardroom.py      # 6フェーズミーティングエンジン
│   │   ├── rule_engine.py    # 5段階判定のガバナンスルール
│   │   ├── schemas.py        # 型安全なデータモデル
│   │   ├── agents.py         # デフォルト9名 + スペシャリスト8名
│   │   ├── security.py       # 入力サニタイゼーション & プロンプトインジェクション防御
│   │   └── prompts/          # エージェントのシステムプロンプト + マニフェスト
│   ├── api.py                # FastAPI REST（認証、CORS）
│   └── cli.py                # CLIツール（aegis コマンド）
├── action.yml                # GitHub Action定義
├── examples/                 # quick_start, custom_agents, rule_engine_demo
├── tests/                    # 32テスト
├── pyproject.toml            # パッケージ設定（aegis-gov）
└── docker/                   # コンテナ設定
```

## サンプルコード

| サンプル | 内容 |
|---------|------|
| [`quick_start.py`](examples/quick_start.py) | 10行で最初のボードルームミーティング |
| [`custom_agents.py`](examples/custom_agents.py) | ヘルスケアコンプライアンスエージェントの追加 |
| [`rule_engine_demo.py`](examples/rule_engine_demo.py) | 4つのガバナンスシナリオ |

## コンプライアンスと標準規格

AEGISは以下の標準規格への対応を支援するツールを提供します：
- **EU AI Act**（第14条：高リスクAIに対するヒューマンオーバーサイト）
- **NIST AI Risk Management Framework**（AI RMF 1.0）
- **ISO/IEC 42001**（AI管理システム）

監査証跡、意思決定の分類、ヒューマンエスカレーションゲートは、これらの標準規格の要件に直接マッピングされます。

## コントリビュート

コントリビューションを歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。

**Good first issues:**
- 新しいドメイン向けエージェントプロンプトの追加（金融、医療、法務）
- 特定のコンプライアンスフレームワーク向けガバナンスルールの追加
- テストカバレッジの向上

## ライセンス

Apache 2.0 -- [LICENSE](LICENSE) をご覧ください
