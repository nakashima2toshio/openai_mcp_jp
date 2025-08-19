# CLAUDE_jp.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリでコード作業を行う際のガイダンスを提供します。

## プロジェクト概要

これはMCP（Model Context Protocol）デモンストレーションプロジェクトで、OpenAIのResponses APIと様々なMCPサーバーの使用方法を紹介しています。プロジェクトには、MCPを通じて複数のデータベースとサービスバックエンドと相互作用するStreamlit UIアプリケーションとFastAPIサーバー実装の両方が含まれています。

## 主要なアーキテクチャコンポーネント

### コアアプリケーション
- **openai_api_mcp_sample.py** - メインのStreamlitアプリケーションエントリーポイント (helper_mcp.py:MCPApplication)
- **mcp_api_server.py** - MCP操作用のFastAPIベースのRESTサーバー (FastAPIアプリインスタンス)
- **mcp_api_client.py** - MCP APIサーバーとの相互作用用クライアントライブラリ (MCPAPIClientクラス)

### ヘルパーモジュール
- **helper_mcp.py** - コアMCP機能、データベース接続、アプリケーションロジック
- **helper_api.py** - OpenAI API統合、ConfigManagerシングルトンによるYAML設定管理
- **helper_st.py** - Streamlit UIコンポーネントとインターフェースヘルパー
- **helper_mcp_pages.py** - マルチページStreamlitアプリのページ管理

### データベースサポート
プロジェクトは複数のデータベースバックエンドをサポートしています：
- **PostgreSQL** - プライマリリレーショナルデータベース（スキーマ）:
  - `customers` (id, name, email, age, city, created_at)
  - `orders` (id, customer_id, product_name, price, quantity, order_date)
  - `products` (id, name, category, price, stock_quantity, description)
- **Redis** - キャッシュとセッションストレージ
- **Elasticsearch** - ドキュメント検索とインデックス
- **Qdrant** - 埋め込みと類似度検索用ベクトルデータベース

## 共通開発コマンド

### 環境セットアップ
```bash
# 依存関係インストールを含む初期セットアップ（uv/pipを自動検出）
./setup_env.sh

# 手動で依存関係をインストール
pip install -r requirements.txt
# または uv を使用（利用可能な場合推奨）
uv sync
```

### アプリケーションの実行
```bash
# Streamlitアプリケーションを開始
streamlit run openai_api_mcp_sample.py --server.port=8501
# または uv を使用
uv run streamlit run openai_api_mcp_sample.py --server.port=8501

# FastAPIサーバーを開始（推奨）
./start_api.sh
# または手動で
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload
```

### データベースとインフラストラクチャ
```bash
# Docker ComposeでMCPデモ環境を開始
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d

# テストデータをセットアップ
python setup_test_data.py
python setup_sample_data.py

# Qdrant診断をチェック
python qdrant_diagnostic.py

# クイックテストを実行
python quick_test.py
```

### 開発ワークフロー
```bash
# データベース接続をチェック
./check_server/check_qdrant.sh

# ヘルスチェックは起動時に自動実行
# APIサーバー: /health エンドポイント
# クライアント: 初期化時の自動ヘルスチェック
```

## 設定

### 環境変数
`.env`ファイルで必要な設定：
- `OPENAI_API_KEY` - Responses API用のOpenAI APIキー
- `PG_CONN_STR` - PostgreSQL接続文字列（デフォルト: `postgresql://testuser:testpass@localhost:5432/testdb`）
- `REDIS_URL` - Redis接続URL（デフォルト: `redis://localhost:6379/0`）
- `ELASTIC_URL` - Elasticsearch URL（デフォルト: `http://localhost:9200`）
- `QDRANT_URL` - Qdrant URL（デフォルト: `http://localhost:6333`）
- `PINECONE_API_KEY` - Pinecone APIキー（オプション）

### モデル設定
プロジェクトはOpenAIモデルの包括的な設定に`config.yml`を使用：
- **モデルカテゴリ**: 
  - frontier (GPT-5シリーズ)
  - reasoning (o3/o4-mini, o1/o1-pro)
  - deep_research (o3/o4 深層研究バリアント)
  - standard (GPT-4o/4.1シリーズ)
  - vision, audio, realtime, image, search, embeddings
- **デフォルトモデル**: gpt-4.1 (ConfigManagerシングルトンで設定可能)
- **音声サポート**: 日本語サポート付き完全なTTS/STTパイプライン
- **設定管理**: helper_api.py:ConfigManagerシングルトンが価格情報付きYAML設定の読み込みとモデル分類を処理

### プロジェクト構造
- `doc/` - 設定、セットアップ、RAGドキュメントを含むドキュメントとガイド
- `README_doc/` - セットアップ手順、APIドキュメント、Claude Codeガイド
- `docker-compose/` - MCPデモ環境用のDocker Compose設定
  - `init-data/` - データベース初期化スクリプト
- `check_server/` - サーバーヘルスチェックスクリプト
- `assets/` - アプリケーションスクリーンショットを含む静的アセット
- `helper_*.py` - コアアプリケーションロジックモジュール
- `mcp_api_*.py` - MCP APIサーバーとクライアント実装
- `setup_*.py` - 環境とデータセットアップスクリプト

## MCP統合パターン

プロジェクトは以下のMCP統合パターンを実証しています：
1. 複数のMCPサーバーがコンテナ化され、HTTP/SSEエンドポイント経由で公開
2. OpenAI Responses APIが`server_url`設定を使用してこれらのサーバーに接続
3. `helper_mcp.py`がMCPプロトコルを通じて異なるデータベース操作を調整
4. UIアプリケーション（Streamlit）がMCP操作用の対話的インターフェースを提供

### MCPサーバーエンドポイント
Docker Composeセットアップを実行すると、MCPサーバーは以下のポートで公開されます：
- Redis MCP: `http://localhost:8000/mcp`
- PostgreSQL MCP: `http://localhost:8001/mcp`
- Elasticsearch MCP: `http://localhost:8002/mcp`
- Qdrant MCP: `http://localhost:8003/mcp`

### APIエンドポイント（FastAPIサーバー）
`mcp_api_server.py`は以下のRESTエンドポイントを提供します：
- **Health**: `/health` - サーバーヘルスチェック
- **Customers**: `/api/customers` (GET, POST), `/api/customers/{id}` (GET)
- **Products**: `/api/products` (GET), `/api/products/{id}` (GET)
- **Orders**: `/api/orders` (GET, POST)
- **Analytics**: `/api/stats/sales`, `/api/stats/customers/{id}/orders`

## テストと開発

### テストコマンド
```bash
# 基本API機能テストを実行
python quick_test.py

# すべてのデータベース用テストデータを生成
python setup_test_data.py

# 現実的な例を含むサンプルデータをセットアップ
python setup_sample_data.py

# Qdrant診断を実行
python qdrant_diagnostic.py
```

### 開発のヒント
- ヘルスチェックはクライアントクラスで自動実行
- 利用可能な場合は高速な依存関係管理のため`uv`を使用
- データベース接続は適切なデフォルトで自動リトライ
- `config.yml`による設定は開発環境でのホットリロードをサポート

## 依存関係

pyproject.tomlからの主要依存関係：
- **streamlit>=1.48.0** - Web UIフレームワーク
- **openai>=1.99.9** - Responses APIサポート付きOpenAI APIクライアント
- **fastapi>=0.116.1** - 自動APIドキュメント付きREST APIフレームワーク
- **データベースクライアント**: psycopg2-binary, redis, elasticsearch, qdrant-client
- **データ処理**: pandas, numpy
- **サーバー**: uvicorn (ASGIサーバー)
- **開発**: python-dotenv, watchdog

### Pythonバージョン
Python >=3.12.2が必要