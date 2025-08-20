# 📋 setup.py / data.py / server.py 設計書

## 📝 目次

1. [📖 概要書](#📖-概要書)
2. [🔧 システム構成](#🔧-システム構成)
3. [📋 関数一覧](#📋-関数一覧)
4. [📑 関数詳細設計](#📑-関数詳細設計)
5. [⚙️ 技術仕様](#⚙️-技術仕様)
6. [🚨 エラーハンドリング](#🚨-エラーハンドリング)

---

## 📖 概要書

### 🎯 処理の概要

**MCP環境セットアップとサーバー管理スクリプト群**

setup.py、data.py、server.pyは、MCP（Model Context Protocol）デモンストレーションプロジェクトの環境構築・データ初期化・サーバー起動を担当する中核スクリプト群です。これらのスクリプトにより、複雑なマルチデータベース環境を自動的にセットアップし、即座に利用可能な状態にできます。

#### 🌟 主要機能カテゴリ

| スクリプト | 機能群 | 説明 |
|-----------|--------|------|
| 🛠️ **setup.py** | 環境構築 | 依存関係インストール・環境変数設定・Python環境検証 |
| 📊 **data.py** | データ初期化 | 4つのデータベースへのテストデータ投入・スキーマ作成 |
| 🚀 **server.py** | サーバー管理 | FastAPIサーバー起動・接続確認・ヘルスチェック |

#### 🔄 統合処理フロー

```mermaid
graph TD
    A["setup.py実行"] --> B["Python環境確認"]
    B --> C["パッケージマネージャ検出"]
    C --> D["依存関係インストール"]
    D --> E["環境変数テンプレート作成"]
    E --> F["data.py実行"]
    F --> G["データベース接続確認"]
    G --> H["テストデータ投入"]
    H --> I["server.py実行"]
    I --> J["FastAPIサーバー起動"]
    J --> K["APIエンドポイント確認"]
    K --> L["MCP環境完成"]
```

### 🔄 主要処理の流れ（環境構築→データ初期化→サーバー起動）

```mermaid
flowchart TD
    Start(["Environment Setup Start"]) --> PyCheck["Python Version Check (3.8+)"]
    PyCheck --> PkgMgr["Package Manager Detection (uv/pip)"]
    PkgMgr --> Install["Dependencies Installation"]
    Install --> EnvVar["Environment Variables Template"]
    
    EnvVar --> DataInit["Data Initialization Start"]
    DataInit --> DBConn["Database Connections Check"]
    DBConn --> Redis["Redis Test Data"]
    Redis --> PostgreSQL["PostgreSQL Schema & Data"]
    PostgreSQL --> Elasticsearch["Elasticsearch Index & Documents"]
    Elasticsearch --> Qdrant["Qdrant Collection & Vectors"]
    
    Qdrant --> ServerStart["Server Startup"]
    ServerStart --> APILaunch["FastAPI Server Launch"]
    APILaunch --> Health["Health Checks"]
    Health --> Endpoints["API Endpoints Test"]
    Endpoints --> Complete["MCP Environment Ready"]
```

---

## 🔧 システム構成

### 📦 主要コンポーネント

```mermaid
classDiagram
    class Setup {
        +check_python_version(): bool
        +detect_package_manager(): str
        +install_packages(manager): bool
        +create_env_template(): bool
        +verify_installation(): bool
    }

    class DataInitializer {
        +setup_redis_data(): bool
        +setup_postgresql_data(): bool
        +setup_elasticsearch_data(): bool
        +setup_qdrant_data(): bool
        +verify_data_integrity(): bool
    }

    class ServerManager {
        +check_database_connections(): bool
        +start_api_server(): bool
        +test_api_endpoints(): bool
        +display_usage_info(): void
    }

    class DatabaseConnections {
        +redis_client: Redis
        +postgresql_client: psycopg2
        +elasticsearch_client: Elasticsearch
        +qdrant_client: QdrantClient
    }

    Setup --> DataInitializer
    DataInitializer --> ServerManager
    DataInitializer --> DatabaseConnections
    ServerManager --> DatabaseConnections
```

### 📋 データフロー（環境構築プロセス）

```mermaid
graph TD
    A["Requirements.txt"] --> B["Package Manager Detection"]
    B --> C["Automated Installation"]
    C --> D["Environment Variables"]
    D --> E["Database Connections"]
    E --> F["Test Data Generation"]
    F --> G["Schema Creation"]
    G --> H["Data Insertion"]
    H --> I["Server Configuration"]
    I --> J["FastAPI Launch"]
    J --> K["Health Verification"]
```

---

## 📋 関数一覧

### 🛠️ setup.py関数

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `check_python_version()` | 🔍 検証 | Python 3.8以上のバージョン確認 | ⭐⭐⭐ |
| `detect_package_manager()` | 🔍 検出 | uv/pipの自動検出・優先順位判定 | ⭐⭐⭐ |
| `install_packages()` | 📦 インストール | パッケージマネージャ別の依存関係インストール | ⭐⭐⭐ |
| `create_env_template()` | 📝 生成 | 環境変数テンプレート(.env)ファイル作成 | ⭐⭐⭐ |
| `verify_installation()` | ✅ 確認 | インストール完了の検証・問題診断 | ⭐⭐ |
| `setup_logging()` | 📝 設定 | ログ設定・デバッグモード対応 | ⭐⭐ |
| `cleanup_old_files()` | 🧹 整理 | 古い設定ファイル・ログの整理 | ⭐ |

### 📊 data.py関数

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `setup_redis_data()` | 🔴 Redis | セッション・キャッシュ・カウンタデータ投入 | ⭐⭐⭐ |
| `setup_postgresql_data()` | 🐘 PostgreSQL | customers・orders・productsテーブル作成・データ投入 | ⭐⭐⭐ |
| `setup_elasticsearch_data()` | 🔍 Elasticsearch | blog_articlesインデックス作成・記事データ投入 | ⭐⭐⭐ |
| `setup_qdrant_data()` | 🎯 Qdrant | product_embeddingsコレクション作成・ベクトルデータ投入 | ⭐⭐⭐ |
| `generate_sample_customers()` | 🧑 生成 | 顧客サンプルデータの生成（日本語対応） | ⭐⭐ |
| `generate_sample_orders()` | 📋 生成 | 注文サンプルデータの生成・リレーション管理 | ⭐⭐ |
| `generate_sample_products()` | 🛍️ 生成 | 商品サンプルデータの生成・カテゴリ分類 | ⭐⭐ |
| `generate_embeddings()` | 🧮 ベクトル | OpenAI embeddings APIを使用したベクトル生成 | ⭐⭐⭐ |
| `verify_data_integrity()` | ✅ 検証 | データ整合性・リレーション確認 | ⭐⭐ |

### 🚀 server.py関数

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `check_database_connections()` | 🔍 接続確認 | 4つのデータベースへの接続確認 | ⭐⭐⭐ |
| `start_api_server()` | 🚀 起動 | uvicornを使用したFastAPIサーバー起動 | ⭐⭐⭐ |
| `test_api_endpoints()` | 🧪 テスト | APIエンドポイントの動作確認 | ⭐⭐⭐ |
| `monitor_server_health()` | 👀 監視 | サーバーヘルスチェック・パフォーマンス監視 | ⭐⭐ |
| `display_usage_info()` | 📖 情報 | 使用方法・URLの表示 | ⭐⭐ |
| `graceful_shutdown()` | 🛑 終了 | サーバーの安全な停止処理 | ⭐⭐ |
| `setup_cors()` | 🌐 CORS | Cross-Origin Resource Sharingの設定 | ⭐ |

---

## 📑 関数詳細設計

### 🛠️ setup.py: check_python_version()

#### 🎯 処理概要
Python実行環境のバージョン確認（3.8以上必須）

#### 📊 処理の流れ
```mermaid
graph TD
    A["Function Start"] --> B["Get Python Version"]
    B --> C{"Version >= 3.8?"}
    C -->|Yes| D["Return True"]
    C -->|No| E["Display Error Message"]
    E --> F["Show Installation Instructions"]
    F --> G["Return False"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | なし |
| **PROCESS** | sys.version_info確認 → バージョン比較 → エラーメッセージ表示 |
| **OUTPUT** | `bool` - バージョン適合性 |

#### 🔧 バージョン確認ロジック

```python
def check_python_version():
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version >= required_version:
        print(f"✅ Python {current_version[0]}.{current_version[1]} detected")
        return True
    else:
        print(f"❌ Python {required_version[0]}.{required_version[1]}+ required")
        print("Please upgrade your Python installation")
        return False
```

---

### 📊 data.py: setup_postgresql_data()

#### 🎯 処理概要
PostgreSQLデータベースにMCPデモ用のテーブル作成・サンプルデータ投入

#### 📊 処理の流れ
```mermaid
graph TD
    A["Function Start"] --> B["Connect to PostgreSQL"]
    B --> C["Create customers table"]
    C --> D["Create products table"]
    D --> E["Create orders table"]
    E --> F["Generate sample customers"]
    F --> G["Generate sample products"]
    G --> H["Generate sample orders"]
    H --> I["Insert data with transactions"]
    I --> J["Verify data integrity"]
    J --> K["Return success status"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | なし（環境変数から接続情報取得） |
| **PROCESS** | テーブル作成 → サンプルデータ生成 → トランザクション投入 → 検証 |
| **OUTPUT** | `bool` - セットアップ成功/失敗 |

#### 🗃️ データベーススキーマ

```sql
-- customers テーブル
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    age INTEGER,
    city VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- products テーブル
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2),
    stock_quantity INTEGER,
    description TEXT
);

-- orders テーブル
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    product_name VARCHAR(100),
    price DECIMAL(10, 2),
    quantity INTEGER,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 🚀 server.py: start_api_server()

#### 🎯 処理概要
uvicornを使用したFastAPIサーバーの起動・ヘルスチェック

#### 📊 処理の流れ
```mermaid
graph TD
    A["Function Start"] --> B["Check database connections"]
    B -->|Success| C["Configure uvicorn"]
    B -->|Failure| D["Exit with error"]
    C --> E["Start FastAPI server"]
    E --> F["Wait for startup"]
    F --> G["Health check"]
    G -->|Success| H["Display server info"]
    G -->|Failure| I["Retry startup"]
    H --> J["Monitor server status"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `host: str = "0.0.0.0"` - サーバーホスト<br>`port: int = 8000` - サーバーポート<br>`reload: bool = True` - 自動リロード |
| **PROCESS** | 接続確認 → uvicorn設定 → サーバー起動 → ヘルスチェック |
| **OUTPUT** | `bool` - サーバー起動成功/失敗 |

#### 🌐 サーバー設定

```python
uvicorn_config = {
    "app": "mcp_api_server:app",
    "host": host,
    "port": port,
    "reload": reload,
    "log_level": "info",
    "workers": 1,
    "timeout_keep_alive": 65
}
```

---

## ⚙️ 技術仕様

### 📦 依存ライブラリ

| ライブラリ | バージョン | 用途 | 重要度 |
|-----------|-----------|------|---------|
| `psycopg2-binary` | 最新 | 🐘 PostgreSQL接続 | ⭐⭐⭐ |
| `redis` | 最新 | 🔴 Redis接続 | ⭐⭐⭐ |
| `elasticsearch` | 最新 | 🔍 Elasticsearch接続 | ⭐⭐⭐ |
| `qdrant-client` | 最新 | 🎯 Qdrant接続 | ⭐⭐⭐ |
| `openai` | >=1.99.9 | 🤖 OpenAI API（embeddings） | ⭐⭐⭐ |
| `fastapi` | >=0.116.1 | 🚀 APIサーバーフレームワーク | ⭐⭐⭐ |
| `uvicorn` | 最新 | 🌐 ASGI サーバー | ⭐⭐⭐ |
| `python-dotenv` | 最新 | ⚙️ 環境変数管理 | ⭐⭐ |

### 🔧 環境変数仕様

#### 📄 必須環境変数

```yaml
Required_Environment_Variables:
  OPENAI_API_KEY: 
    description: "OpenAI API key for embeddings"
    required: true
    example: "sk-..."
    
  PG_CONN_STR:
    description: "PostgreSQL connection string"
    default: "postgresql://testuser:testpass@localhost:5432/testdb"
    
  REDIS_URL:
    description: "Redis connection URL"
    default: "redis://localhost:6379/0"
    
  ELASTIC_URL:
    description: "Elasticsearch connection URL"
    default: "http://localhost:9200"
    
  QDRANT_URL:
    description: "Qdrant connection URL"
    default: "http://localhost:6333"
```

#### 📋 生成される.envテンプレート

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Connections
PG_CONN_STR=postgresql://testuser:testpass@localhost:5432/testdb
REDIS_URL=redis://localhost:6379/0
ELASTIC_URL=http://localhost:9200
QDRANT_URL=http://localhost:6333

# Optional: Pinecone (alternative vector DB)
PINECONE_API_KEY=your_pinecone_key_here

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG_MODE=false
```

### 📊 データベース接続仕様

#### 🔧 接続設定

```yaml
Database_Connections:
  redis:
    url: "redis://localhost:6379/0"
    timeout: 5
    max_connections: 10
    
  postgresql:
    connection_string: "postgresql://testuser:testpass@localhost:5432/testdb"
    pool_size: 5
    timeout: 10
    
  elasticsearch:
    url: "http://localhost:9200"
    timeout: 30
    max_retries: 3
    
  qdrant:
    url: "http://localhost:6333"
    timeout: 10
    prefer_grpc: false
```

### 🎯 サンプルデータ仕様

#### 📋 PostgreSQLサンプルデータ

```yaml
Sample_Data_Counts:
  customers: 100
  products: 50
  orders: 200

Customer_Data_Template:
  name: "田中太郎、佐藤花子..."（日本語名前）
  email: "user@example.com"
  age: 20-70（ランダム）
  city: "東京都、大阪府、愛知県..."（日本の都道府県）

Product_Data_Template:
  category: ["Electronics", "Books", "Clothing", "Home", "Sports"]
  price_range: 500-50000（円）
  stock_quantity: 0-100
```

#### 🔍 Elasticsearchサンプルデータ

```yaml
Blog_Articles_Sample:
  count: 20
  languages: ["日本語", "English"]
  categories: ["Technology", "Business", "Health", "Travel"]
  content_length: 500-2000文字
```

#### 🎯 Qdrantサンプルデータ

```yaml
Vector_Embeddings:
  collection: "product_embeddings"
  dimension: 384（sentence-transformers/all-MiniLM-L6-v2）
  distance: "cosine"
  vector_count: 50
```

---

## 🚨 エラーハンドリング

### 📋 エラーカテゴリ

#### 🛠️ setup.py関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **Python バージョン不適合** | 🐍 Python < 3.8 | Pythonアップグレード指示・詳細リンク | 🔴 高 |
| **パッケージマネージャ不在** | 📦 pip/uv両方利用不可 | pip インストール指示・環境確認 | 🔴 高 |
| **権限エラー** | 🔒 パッケージインストール権限不足 | sudo使用提案・仮想環境推奨 | 🟡 中 |
| **ネットワークエラー** | 🌐 PyPI接続失敗 | 接続確認・プロキシ設定提案 | 🟡 中 |

#### 📊 data.py関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **データベース接続失敗** | 🔌 接続情報・サーバー起動状態 | 接続文字列確認・Docker起動指示 | 🔴 高 |
| **スキーマ作成エラー** | 🏗️ 権限・既存テーブル競合 | 権限確認・DROP TABLE提案 | 🟡 中 |
| **データ挿入失敗** | 📋 制約違反・メモリ不足 | データクリア・バッチサイズ調整 | 🟡 中 |
| **Embedding API エラー** | 🤖 OpenAI APIキー・レート制限 | APIキー確認・待機時間調整 | 🟡 中 |

#### 🚀 server.py関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **ポート使用中** | 🔌 既存プロセスがポート占有 | プロセス確認・代替ポート提案 | 🟡 中 |
| **FastAPI 起動失敗** | 🚀 設定・依存関係問題 | ログ確認・設定見直し指示 | 🔴 高 |
| **ヘルスチェック失敗** | 👀 サーバー応答なし・タイムアウト | 待機時間延長・手動確認提案 | 🟡 中 |
| **API エンドポイント エラー** | 🌐 ルーティング・認証問題 | 設定確認・ログ詳細表示 | 🟡 中 |

### 🛠️ エラーハンドリング戦略

#### 🔧 段階的エラー処理

```mermaid
graph TD
    A["Error Detected"] --> B{"Error Type"}
    B -->|Setup| C["Environment Fix"]
    B -->|Data| D["Database Recovery"]
    B -->|Server| E["Service Restart"]
    
    C --> F["Instruction Display"]
    D --> G["Data Cleanup & Retry"]
    E --> H["Port Change & Retry"]
    
    F --> I["User Action Required"]
    G --> J{"Recovery Success?"}
    H --> K["Server Status Check"]
    
    J -->|Yes| L["Continue Process"]
    J -->|No| M["Manual Intervention"]
```

#### ✅ エラーメッセージ例

```python
# Python バージョンエラー
print("❌ Python 3.8以上が必要です")
print("現在のバージョン:", sys.version)
print("アップグレード: https://www.python.org/downloads/")

# データベース接続エラー
print("❌ PostgreSQL接続に失敗しました")
print("接続文字列を確認してください:", conn_str)
print("Dockerコンテナ起動: docker-compose up -d")

# サーバー起動エラー
print("❌ ポート8000が使用中です")
print("使用中プロセス確認: lsof -i :8000")
print("代替ポート使用: python server.py --port 8001")
```

#### 🚨 自動復旧機能

```python
retry_strategies = {
    "database_connection": {
        "max_retries": 3,
        "backoff_factor": 2,
        "actions": ["wait", "reconnect", "use_fallback"]
    },
    "package_installation": {
        "max_retries": 2,
        "alternatives": ["pip", "pip3", "python -m pip"]
    },
    "server_startup": {
        "max_retries": 3,
        "port_alternatives": [8000, 8001, 8002, 8080]
    }
}
```

#### 📊 診断機能

```python
def diagnose_environment():
    """包括的な環境診断"""
    checks = {
        "python_version": check_python_version(),
        "package_manager": detect_package_manager() is not None,
        "database_connections": check_all_databases(),
        "required_packages": verify_installation(),
        "environment_variables": check_env_vars()
    }
    
    # 診断レポート生成
    generate_diagnostic_report(checks)
```

---

## 🎉 まとめ

この設計書は、**setup.py、data.py、server.py** の包括的な技術仕様と実装詳細を記載した完全なドキュメントです。

### 🌟 設計のハイライト

- **🛠️ 自動環境構築**: Python環境確認・依存関係インストール・設定ファイル生成
- **📊 マルチDB対応**: Redis・PostgreSQL・Elasticsearch・Qdrant統合管理
- **🚀 簡単サーバー起動**: FastAPI・uvicorn・ヘルスチェック自動化
- **🛡️ 堅牢なエラー処理**: 包括的な診断・自動復旧・ユーザーガイダンス

### 🔧 アーキテクチャ特徴

- **📦 段階的セットアップ**: 環境構築→データ初期化→サーバー起動の論理的順序
- **🎯 現実的なサンプルデータ**: 日本語対応・リレーション整合性・ベクトル埋め込み
- **🔄 自動復旧機能**: 失敗時の代替手段・詳細なエラーガイダンス
- **📊 包括的な検証**: 各段階でのデータ整合性・接続確認

### 📈 MCP環境最適化機能

- **⚙️ 柔軟な設定管理**: 環境変数・デフォルト値・オーバーライド対応
- **🔍 包括的な診断**: システム状態確認・問題特定・解決提案
- **🌐 プロダクション対応**: CORS設定・セキュリティ考慮・パフォーマンス最適化
- **📋 開発者体験**: 詳細なログ・親切なエラーメッセージ・ステップバイステップガイド

### 🚀 今後の拡張可能性

- 🔄 クラウド環境対応（AWS・Azure・GCP）
- 📊 監視・メトリクス収集機能
- 🌐 Kubernetes デプロイメント対応
- 📱 CI/CD パイプライン統合
- 🔐 高度なセキュリティ機能