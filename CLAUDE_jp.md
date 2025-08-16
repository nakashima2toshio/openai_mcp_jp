# CLAUDE_jp.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリでコード作業を行う際のガイダンスを提供します。

## プロジェクト概要

これはMCP（Model Context Protocol）デモンストレーションプロジェクトで、OpenAIのResponses APIと様々なMCPサーバーの使用方法を紹介しています。プロジェクトには、MCPを通じて複数のデータベースとサービスバックエンドと相互作用するStreamlit UIアプリケーションとFastAPIサーバー実装の両方が含まれています。

## 主要なアーキテクチャコンポーネント

### コアアプリケーション
- **openai_api_mcp_sample.py** - メインのStreamlitアプリケーションエントリーポイント (11行目: `from helper_mcp import MCPApplication`)
- **mcp_api_server.py** - MCP操作用のFastAPIベースのRESTサーバー (19行目: `app = FastAPI`)
- **mcp_api_client.py** - MCP APIサーバーとの相互作用用クライアントライブラリ (14行目: `class MCPAPIClient`)
- **mcp_api_streamlit_app.py** - MCP APIクライアントのStreamlit化アプリ（9つのデモ機能を含む）

### ヘルパーモジュール
- **helper_mcp.py** - コアMCP機能、データベース接続、アプリケーションロジック
- **helper_api.py** - OpenAI API統合、設定管理、レスポンス処理
- **helper_st.py** - Streamlit UIコンポーネントとインターフェースヘルパー
- **helper_mcp_pages.py** - マルチページStreamlitアプリのページ管理

### データベースサポート
プロジェクトは複数のデータベースバックエンドをサポートしています：
- PostgreSQL (psycopg2-binary)
- Redis
- Elasticsearch
- Qdrant (ベクトルデータベース)

## 共通開発コマンド

### 環境セットアップ
```bash
# 依存関係インストールを含む初期セットアップ
./setup_env.sh

# 手動で依存関係をインストール
pip install -r requirements.txt
# または uv を使用（利用可能な場合）
uv add streamlit openai python-dotenv pandas numpy requests redis psycopg2-binary elasticsearch qdrant-client watchdog plotly
```

### アプリケーションの実行
```bash
# Streamlitアプリケーション（メイン）を開始
streamlit run openai_api_mcp_sample.py --server.port=8501

# Streamlitアプリケーション（APIデモ）を開始
streamlit run mcp_api_streamlit_app.py --server.port=8502

# FastAPIサーバーを開始
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload
# またはスクリプトを使用
./start_api.sh
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

# APIサーバーヘルスチェック (helper_api.py:33)
# クライアントには初期化時にヘルスチェックが含まれています (mcp_api_client.py:33)
```

## 設定

### 環境変数
`.env`ファイルで必要な設定：
- `OPENAI_API_KEY` - Responses API用のOpenAI APIキー
- `PG_CONN_STR` - PostgreSQL接続文字列（デフォルト: `postgresql://testuser:testpass@localhost:5432/testdb`）
- `REDIS_URL` - Redis接続URL（デフォルト: `redis://localhost:6379/0`）
- `ELASTIC_URL` - Elasticsearch URL（デフォルト: `http://localhost:9200`）
- `QDRANT_URL` - Qdrant URL（デフォルト: `http://localhost:6333`）
- `MCP_API_BASE_URL` - MCP APIサーバーのベースURL（デフォルト: `http://localhost:8000`）

### プロジェクト構造
- `doc/` - ドキュメントとガイド
- `docker-compose/` - MCPサーバー用のDocker Compose設定
- `check_server/` - サーバーヘルスチェックスクリプト
- `assets/` - 画像を含む静的アセット

## MCP統合パターン

プロジェクトは以下のMCP統合パターンを実証しています：
1. 複数のMCPサーバーがコンテナ化され、HTTP/SSEエンドポイント経由で公開
2. OpenAI Responses APIが`server_url`設定を使用してこれらのサーバーに接続
3. `helper_mcp.py`がMCPプロトコルを通じて異なるデータベース操作を調整
4. UIアプリケーション（Streamlit）がMCP操作用の対話的インターフェースを提供

## アプリケーション機能

### openai_api_mcp_sample.py（メインアプリ）
- 基本的なMCP機能デモ
- データベース接続管理
- AI チャット機能
- サーバー状態監視

### mcp_api_streamlit_app.py（APIデモアプリ）
以下の9つのデモ機能を提供：
1. **ホーム** - システム状態とヘルスチェック
2. **基本操作** - 顧客・商品・注文データの表示と検索
3. **売上分析** - 売上統計ダッシュボードとグラフ表示
4. **顧客分析** - 個別顧客の詳細分析
5. **データ作成** - 顧客・注文の新規作成フォーム
6. **データ分析** - Pandas連携データ分析
7. **エラーテスト** - エラーハンドリング実演
8. **パフォーマンス** - API応答時間測定
9. **対話機能** - リアルタイムデータ操作

## テスト

- `quick_test.py` - 基本機能テスト
- `setup_test_data.py` - データベース用テストデータ生成
- ヘルスチェックはクライアントクラスに組み込まれています (mcp_api_client.py:33)

## 依存関係

pyproject.tomlからの主要依存関係：
- streamlit>=1.48.0 - Web UIフレームワーク
- openai>=1.99.9 - Responses APIサポート付きOpenAI APIクライアント
- fastapi>=0.116.1 - REST APIフレームワーク
- データベースクライアント: psycopg2-binary, redis, elasticsearch, qdrant-client
- データ処理: pandas, numpy
- サーバー: uvicorn
- 可視化: plotly（売上分析グラフ用）

## 開発上の注意点

### 日本語UI対応
- すべてのStreamlitアプリは日本語UIに対応
- エラーメッセージも日本語で表示
- CSVダウンロード時のファイル名は日本語対応（UTF-8 BOM付き）

### エラーハンドリング
- 包括的なエラー処理が実装済み
- APIサーバー未接続時の適切なフォールバック
- ユーザーフレンドリーなエラーメッセージ

### セッション管理
- Streamlitセッション状態を活用した状態管理
- ページ間でのデータ永続化
- 作成履歴の追跡と管理

### パフォーマンス最適化
- データキャッシングによる応答速度向上
- 効率的なAPI呼び出しパターン
- リアルタイム更新機能