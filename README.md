# 🤖 OpenAI MCP Japan - 自然言語データベースアクセスデモ

**OpenAI Responses API + MCP (Model Context Protocol) による革新的なマルチデータベース自然言語インターフェース**

[![Python](https://img.shields.io/badge/Python-3.12.2+-blue.svg)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-Responses_API-green.svg)](https://openai.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.48.0+-red.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1+-teal.svg)](https://fastapi.tiangolo.com)

![MCP Demo Overview](assets/start_img.png)

## 🎯 プロジェクト概要

このプロジェクトは、**OpenAIの最新Responses API**と**Model Context Protocol (MCP)**を統合した、マルチデータベース対応の自然言語インターフェースデモンストレーションです。複雑なデータベースクエリを日本語で入力するだけで、AIが適切なクエリ戦略を生成し、実行結果を分かりやすく説明します。

### 🌟 主要特徴

- 🗣️ **自然言語データベースアクセス** - 日本語でデータベースを操作
- 🤖 **最新OpenAI統合** - GPT-5、GPT-4.1、o3/o4シリーズ対応
- 🔄 **MCP準拠アーキテクチャ** - Model Context Protocol実装
- 📊 **マルチデータベース対応** - PostgreSQL、Elasticsearch、Redis、Qdrant
- 🌐 **Webインターフェース** - Streamlit + FastAPI
- 🛡️ **プロダクション対応** - セキュリティ、エラーハンドリング、監視機能

## 🏗️ アーキテクチャ

```mermaid
graph TD
    A[Streamlit UI] --> B[OpenAI Responses API]
    B --> C[MCP Server]
    C --> D[PostgreSQL]
    C --> E[Elasticsearch]
    C --> F[Redis]
    C --> G[Qdrant]
    
    H[FastAPI Server] --> D
    H --> E
    H --> F
    H --> G
```

## 💾 対応データベース

| データベース | 用途 | 主要機能 | MCP エンドポイント |
|-------------|------|---------|-------------------|
| **PostgreSQL** | リレーショナルデータ | SQL生成・CRUD・分析 | `http://localhost:8001/mcp` |
| **Elasticsearch** | ドキュメント検索 | 全文検索・集約分析 | `http://localhost:8002/mcp` |
| **Redis** | キャッシュ・セッション | リアルタイムデータ管理 | `http://localhost:8000/mcp` |
| **Qdrant** | ベクトル検索 | セマンティック検索 | `http://localhost:8003/mcp` |

## 🚀 クイックスタート

### 📋 必要環境

- **Python**: 3.12.2 以上
- **Docker & Docker Compose**: コンテナ環境
- **OpenAI API Key**: Responses API対応

### ⚙️ セットアップ

#### 1. 依存関係インストール

```bash
# 自動検出スクリプト（推奨）
./setup_env.sh

# 手動インストール
pip install -r requirements.txt
# または uv 使用（高速）
uv sync
```

#### 2. 環境変数設定

```bash
# .env ファイル作成
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
PG_CONN_STR=postgresql://testuser:testpass@localhost:5432/testdb
REDIS_URL=redis://localhost:6379/0
ELASTIC_URL=http://localhost:9200
QDRANT_URL=http://localhost:6333
EOF
```

#### 3. インフラストラクチャ起動

```bash
# MCP デモ環境起動（PostgreSQL、Redis、Elasticsearch、Qdrant）
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d

# サンプルデータ投入
python check_server/setup_sample_data.py
```

#### 4. アプリケーション起動

```bash
# Streamlit UI （メイン）
streamlit run mcp_db_show_data.py --server.port=8501

# FastAPI サーバー（REST API）
./check_server/start_api.sh
# または手動起動
uvicorn check_server.mcp_api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 🌐 アクセス

- **Streamlit UI**: http://localhost:8501
- **FastAPI API**: http://localhost:8000
- **API ドキュメント**: http://localhost:8000/docs

## 🎮 使用例

### 📊 PostgreSQL - 自然言語SQL

![PostgreSQL Demo](assets/postgresql_image.png)

```
入力: "東京在住の30歳以上の顧客で、過去3ヶ月の注文金額が10万円以上の人を表示して"
↓ AI が自動生成
SELECT c.*, SUM(o.price * o.quantity) as total_amount 
FROM customers c 
JOIN orders o ON c.id = o.customer_id 
WHERE c.city = '東京' AND c.age >= 30 
  AND o.order_date >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY c.id 
HAVING SUM(o.price * o.quantity) >= 100000
```

### 🔍 Elasticsearch - ドキュメント検索

```
入力: "Pythonプログラミングに関する技術記事で、初心者向けの内容を探して"
↓ AI が検索戦略生成
{
  "query": {"bool": {"must": [
    {"match": {"content": "Python プログラミング"}},
    {"match": {"tags": "初心者"}}
  ]}},
  "sort": [{"score": {"order": "desc"}}]
}
```

### 🎯 Qdrant - セマンティック検索

```
入力: "プログラミング作業に適したノートPCを探して"
↓ OpenAI Embeddings でベクトル化 + 意味検索
類似結果: "高性能ノートPC", "開発用マシン", "コーディング環境"
類似度スコア: 0.892, 0.847, 0.823
```

## 📁 プロジェクト構造

```
openai_mcp_jp/
├── 🚀 メインアプリケーション
│   ├── mcp_db_show_data.py          # メインエントリーポイント
│   ├── mcp_postgresql.py            # PostgreSQL自然言語インターフェース
│   ├── mcp_elasticsearch.py         # Elasticsearchドキュメント検索
│   └── mcp_qdrant.py               # Qdrantベクトル検索
├── 🔧 ヘルパーモジュール
│   ├── helper_mcp.py               # MCP機能・データベース接続
│   ├── helper_api.py               # OpenAI API統合・設定管理
│   ├── helper_st.py                # Streamlit UIコンポーネント
│   └── helper_mcp_pages.py         # ページ管理
├── ⚙️ 設定・インフラ
│   ├── config.yml                  # OpenAIモデル設定
│   ├── pyproject.toml             # Python依存関係
│   ├── docker-compose/            # Dockerコンテナ設定
│   └── .env                       # 環境変数
├── 📖 ドキュメント
│   ├── doc/                       # 設計書・技術仕様
│   └── assets/                    # スクリーンショット・画像
└── README.md                      # このファイル
```

## 🔧 FastAPI REST エンドポイント

### 📊 顧客管理

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/customers` | GET | 顧客一覧（都市フィルタ対応） |
| `/api/customers/{id}` | GET | 特定顧客取得 |
| `/api/customers` | POST | 新規顧客作成 |

### 🛍️ 商品・注文管理

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/products` | GET | 商品一覧（カテゴリ・価格フィルタ） |
| `/api/products/{id}` | GET | 特定商品取得 |
| `/api/orders` | GET | 注文一覧（顧客・商品フィルタ） |
| `/api/orders` | POST | 新規注文作成 |

### 📈 分析・統計

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/stats/sales` | GET | 売上統計 |
| `/api/stats/customers/{id}/orders` | GET | 顧客別統計 |
| `/health` | GET | ヘルスチェック |

## 🤖 OpenAI統合仕様

### 📋 対応モデル

| カテゴリ | モデル | 用途 |
|---------|--------|------|
| **Frontier** | GPT-5, GPT-5-mini | 最先端推論・複雑タスク |
| **Reasoning** | o3, o4-mini, o1-pro | 論理的推論・数学・コード |
| **Deep Research** | o3, o4 (深層研究版) | 研究・分析・長文生成 |
| **Standard** | GPT-4.1, GPT-4o | 汎用タスク・安定性重視 |
| **Audio** | GPT-4o-audio | 音声合成・認識（日本語対応） |

### ⚙️ 設定管理

```yaml
# config.yml 抜粋
default_model: "gpt-4.1"
model_categories:
  frontier:
    - "gpt-5"
    - "gpt-5-mini"
  reasoning:
    - "o3"
    - "o4-mini"
    - "o1-pro"
audio:
  tts:
    model: "gpt-4o-audio-preview"
    voice: "nova"
    language: "ja"
```

## 🛡️ セキュリティ・安全性

### 🔒 セキュリティ機能

- **SQL インジェクション対策**: ホワイトリスト方式クエリ検証
- **安全なクエリ検証**: SELECT文のみ許可（PostgreSQL）
- **トークン管理**: 精密なトークン計算・コスト推定
- **エラーハンドリング**: 包括的例外処理・フォールバック

### 🚨 エラー対応

```python
# 多層フォールバック例
try:
    # 主戦略: MCP経由でデータベースアクセス
    return execute_mcp_query(query)
except MCPConnectionError:
    # フォールバック: 直接データベースアクセス
    return execute_direct_query(query)
except Exception:
    # 最終フォールバック: モックデータ・エラー説明
    return provide_mock_data_with_explanation()
```

## 🐳 Docker Compose 設定

### 🚀 完全な開発環境

```bash
# フル環境起動
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d

# 個別サービス起動
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d postgresql
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d elasticsearch
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d qdrant
```

### 📊 ヘルスチェック

```bash
# 全サービス状態確認
docker-compose -f docker-compose/docker-compose.mcp-demo.yml ps

# 個別ヘルスチェック
curl http://localhost:5432  # PostgreSQL
curl http://localhost:9200/_cluster/health  # Elasticsearch
curl http://localhost:6333/health  # Qdrant
curl http://localhost:6379  # Redis (redis-cli ping)
```

## 🧪 開発・テスト

### ✅ テスト実行

```bash
# 基本機能テスト
python quick_test.py

# データベース診断
python qdrant_diagnostic.py

# サンプルデータ生成
python check_server/setup_sample_data.py
```

### 🔍 開発用コマンド

```bash
# 開発サーバー起動（自動リロード）
streamlit run mcp_db_show_data.py --server.port=8501 --server.reload

# FastAPI開発サーバー
uvicorn check_server.mcp_api_server:app --reload --host 0.0.0.0 --port 8000

# ログ監視
docker-compose -f docker-compose/docker-compose.mcp-demo.yml logs -f
```

## 📚 技術仕様詳細

### 📖 設計書

プロジェクトの詳細な技術仕様は以下の設計書をご覧ください：

- [mcp_db_show_data.py 設計書](doc/mcp_db_show_data.md) - メインアプリケーション
- [mcp_postgresql.py 設計書](doc/mcp_postgresql.md) - PostgreSQL自然言語インターフェース
- [mcp_elasticsearch.py 設計書](doc/mcp_elasticsearch.md) - Elasticsearchドキュメント検索
- [mcp_qdrant.py 設計書](doc/mcp_qdrant.md) - Qdrantベクトル検索
- [helper_api.py 設計書](doc/helper_api_rag.md) - OpenAI API統合・設定管理

### 🔧 依存関係

```toml
[project]
requires-python = ">=3.12.2"
dependencies = [
    "streamlit>=1.48.0",      # Webアプリケーションフレームワーク
    "openai>=1.99.9",         # OpenAI API（Responses API対応）
    "fastapi>=0.116.1",       # REST APIフレームワーク
    "psycopg2-binary",        # PostgreSQL
    "redis>=5.2.0",           # Redis
    "elasticsearch>=9.1.0",   # Elasticsearch
    "qdrant-client>=1.15.1",  # Qdrant
    "pandas>=2.3.1",          # データ処理
    "plotly>=5.24.1",         # データ可視化
    "uvicorn",                # ASGI サーバー
]
```

## 🚨 トラブルシューティング

### ❗ よくある問題

#### 🔌 データベース接続エラー

```bash
# Docker サービス状態確認
docker-compose -f docker-compose/docker-compose.mcp-demo.yml ps

# 個別サービス再起動
docker-compose -f docker-compose/docker-compose.mcp-demo.yml restart postgresql
```

#### 🤖 OpenAI API エラー

```bash
# API キー確認
echo $OPENAI_API_KEY

# 残高・制限確認
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/usage
```

#### 🌐 ポート競合

```bash
# ポート使用状況確認
lsof -i :8501  # Streamlit
lsof -i :8000  # FastAPI

# 代替ポートで起動
streamlit run mcp_db_show_data.py --server.port=8502
```

### 🔧 ログ・デバッグ

```bash
# アプリケーションログ
tail -f logs/app.log

# Docker ログ
docker-compose -f docker-compose/docker-compose.mcp-demo.yml logs -f postgresql

# Streamlit デバッグモード
streamlit run mcp_db_show_data.py --logger.level=debug
```

## 🤝 貢献・開発

### 🔄 開発フロー

1. **Fork & Clone**
2. **ブランチ作成**: `git checkout -b feature/your-feature`
3. **開発・テスト**: `python quick_test.py`
4. **プルリクエスト作成**

### 📋 開発者向け情報

- **コーディング規約**: PEP 8 準拠
- **型ヒント**: 必須（Python 3.12+）
- **テスト**: pytest 使用
- **ドキュメント**: Markdown + Mermaid

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🙏 謝辞

- **OpenAI**: 革新的なResponses API・MCP仕様
- **Streamlit**: 優れたWebアプリケーションフレームワーク  
- **FastAPI**: 高性能なWebAPIフレームワーク
- **Database Teams**: PostgreSQL、Elasticsearch、Redis、Qdrant開発チーム

---

## 📞 サポート・お問い合わせ

- **Issue報告**: [GitHub Issues](https://github.com/your-repo/issues)
- **機能要望**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **ドキュメント**: [doc/](doc/) ディレクトリ

**🚀 OpenAI Responses API + MCP で、データベースアクセスの未来を体験してください！**