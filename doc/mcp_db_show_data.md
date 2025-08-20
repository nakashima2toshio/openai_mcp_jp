# 📋 mcp_db_show_data.py 設計書

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

**MCPデモアプリケーションメインエントリーポイント**

mcp_db_show_data.pyは、MCP (Model Context Protocol) とOpenAI APIを統合したマルチデータベース対応デモンストレーションアプリケーションのメインエントリーポイントです。わずか85行のシンプルな構造で、PostgreSQL、Elasticsearch、Redis、Qdrantという4つの異なるデータベースシステムとの統合MCPアーキテクチャを提供します。

#### 🌟 主要機能カテゴリ

| カテゴリ | 機能群 | 説明 |
|---------|--------|------|
| 🚀 **アプリケーション起動** | main | 統一エントリーポイント・環境設定・アプリ初期化 |
| 🎨 **UI設定** | Streamlit設定 | ページ設定・カスタムCSS・レイアウト管理 |
| 🤖 **OpenAI統合** | API初期化 | OpenAIクライアント設定・エラーハンドリング |
| 📱 **MCP実行** | MCPApplication | ヘルパーモジュール経由でのMCP機能実行 |

#### 🔄 アプリケーション処理フロー

```mermaid
graph TD
    A["Application Start"] --> B["環境変数読み込み (load_dotenv)"]
    B --> C["Streamlit設定 (page_config)"]
    C --> D["カスタムCSS適用"]
    D --> E["OpenAI API初期化 (オプション)"]
    E --> F["MCPApplication インスタンス化"]
    F --> G["app.run() 実行"]
    G --> H["フッター表示"]
    H --> I["Application Complete"]
```

### 🔄 主要処理の流れ（MCP統合）

```mermaid
flowchart TD
    Start(["mcp_db_show_data.py start"]) --> LoadEnv["load_dotenv() 環境変数読み込み"]
    LoadEnv --> StreamlitConfig["Streamlit設定 (page_title, icon, layout)"]
    StreamlitConfig --> CSS["カスタムCSS適用"]
    CSS --> OpenAI["OpenAI API初期化チェック"]
    
    OpenAI --> MCPApp["MCPApplication() インスタンス化"]
    MCPApp --> MCPRun["app.run() - MCP機能実行"]
    MCPRun --> Footer["フッター表示"]
    Footer --> End(["Application Running"])
    
    MCPRun --> DBPostgreSQL["PostgreSQL MCP"]
    MCPRun --> DBElasticsearch["Elasticsearch MCP"]
    MCPRun --> DBRedis["Redis MCP"]
    MCPRun --> DBQdrant["Qdrant MCP"]
```

---

## 🔧 システム構成

### 📦 主要コンポーネント

```mermaid
classDiagram
    class main {
        +load_dotenv()
        +set_page_config()
        +apply_custom_css()
        +initialize_openai()
        +create_mcp_application()
        +display_footer()
    }

    class StreamlitConfig {
        +page_title: str
        +page_icon: str
        +layout: str
        +sidebar_state: str
    }

    class CustomCSS {
        +main_header: style
        +status_good: style
        +status_bad: style
        +info_box: style
    }

    class OpenAIIntegration {
        +api_key: str
        +client: OpenAI
        +error_handling: bool
    }

    class MCPApplication {
        +run()
        +database_connections()
        +ui_components()
        +session_management()
    }

    main --> StreamlitConfig
    main --> CustomCSS
    main --> OpenAIIntegration
    main --> MCPApplication
```

### 📋 データフロー（アプリケーション初期化）

```mermaid
graph TD
    A["環境変数ファイル (.env)"] --> B["load_dotenv() 読み込み"]
    B --> C["OPENAI_API_KEY 確認"]
    C --> D["OpenAI Client 初期化"]
    D --> E["Streamlit Page Config"]
    E --> F["Custom CSS 適用"]
    F --> G["MCPApplication インスタンス化"]
    G --> H["helper_mcp.py 経由 MCP実行"]
    H --> I["Multi-Database UI 表示"]
```

---

## 📋 関数一覧

### 🚀 メイン実行関数

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `main()` | 🏗️ 主処理 | アプリケーション全体の初期化・実行制御 | ⭐⭐⭐ |
| `if __name__ == "__main__"` | 🎯 エントリー | スクリプト直接実行時の処理分岐 | ⭐⭐⭐ |

### ⚙️ 初期化処理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `load_dotenv()` | 🔧 環境設定 | .envファイルからの環境変数読み込み | ⭐⭐⭐ |
| `st.set_page_config()` | 🎨 UI設定 | Streamlitページ設定・レイアウト定義 | ⭐⭐⭐ |
| `st.markdown()` | 🎨 CSS適用 | カスタムCSS・スタイリング適用 | ⭐⭐ |

### 🤖 OpenAI統合処理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `os.getenv('OPENAI_API_KEY')` | 🔑 認証 | OpenAI APIキー環境変数取得 | ⭐⭐⭐ |
| `openai.api_key = ...` | 🔗 API設定 | OpenAI APIキー設定 | ⭐⭐ |
| `openai.OpenAI()` | 🤖 クライアント | OpenAI クライアント初期化 | ⭐⭐ |

### 📱 MCP実行処理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `MCPApplication()` | 🏗️ 初期化 | MCPアプリケーションインスタンス作成 | ⭐⭐⭐ |
| `app.run()` | 🚀 実行 | MCPアプリケーションメイン実行 | ⭐⭐⭐ |

### 🎨 UI表示処理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `st.write()` | 📝 表示 | ヘッダー・説明文表示 | ⭐⭐ |
| `st.markdown()` | 🎨 装飾 | HTML・マークダウン装飾表示 | ⭐⭐ |

---

## 📑 関数詳細設計

### 🚀 main()

#### 🎯 処理概要
アプリケーション全体の初期化・設定・実行を統括するメイン関数

#### 📊 処理の流れ
```mermaid
graph TD
    A["main() called"] --> B["load_dotenv() 環境変数読み込み"]
    B --> C["st.set_page_config() Streamlit設定"]
    C --> D["Display header & instructions"]
    D --> E["Apply custom CSS styles"]
    E --> F{"OPENAI_API_KEY exists?"}
    F -->|Yes| G["Initialize OpenAI client"]
    F -->|No| H["Skip OpenAI initialization"]
    G --> I["Create MCPApplication instance"]
    H --> I
    I --> J["app.run() execute"]
    J --> K["Display footer"]
    K --> L["Function complete"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | なし（グローバル環境・設定ファイル依存） |
| **PROCESS** | 環境設定 → UI設定 → OpenAI初期化 → MCP実行 → フッター表示 |
| **OUTPUT** | Streamlit Webアプリケーション表示 |

#### 🔧 環境変数・設定管理

```python
# 環境変数読み込み
load_dotenv()

# Streamlit設定
st.set_page_config(
    page_title="MCP サーバー デモ",
    page_icon="🤖",
    layout="wide"
)

# OpenAI API設定（オプション）
if os.getenv('OPENAI_API_KEY'):
    openai.api_key = os.getenv('OPENAI_API_KEY')
    client = openai.OpenAI()
```

---

### 🎨 Streamlit設定系

#### 🎯 処理概要
Webアプリケーションの外観・レイアウト・スタイルの統一設定

#### 📊 処理の流れ
```mermaid
graph TD
    A["UI Setup Start"] --> B["Page Config (title, icon, layout)"]
    B --> C["Header & Instructions Display"]
    C --> D["Custom CSS Definition"]
    D --> E["Apply CSS Styles"]
    E --> F["UI Setup Complete"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | ページ設定パラメータ・CSSスタイル定義 |
| **PROCESS** | ページ設定適用 → ヘッダー表示 → CSS適用 |
| **OUTPUT** | 統一されたWebアプリケーション外観 |

#### 🎨 カスタムCSS仕様

```css
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}

.status-good {
    color: #28a745;
    font-weight: bold;
}

.status-bad {
    color: #dc3545;
    font-weight: bold;
}

.info-box {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #17a2b8;
    margin: 1rem 0;
}
```

---

### 🤖 OpenAI統合処理

#### 🎯 処理概要
OpenAI APIクライアントの条件付き初期化・エラーハンドリング

#### 📊 処理の流れ
```mermaid
graph TD
    A["OpenAI Setup Start"] --> B{"OPENAI_API_KEY in env?"}
    B -->|Yes| C["Import openai library"]
    C --> D{"Import successful?"}
    D -->|Yes| E["Set API key"]
    E --> F["Create OpenAI client"]
    F --> G["OpenAI Ready"]
    D -->|No| H["Display warning"]
    B -->|No| I["Skip OpenAI setup"]
    H --> I
    I --> J["Continue without OpenAI"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | 環境変数 `OPENAI_API_KEY` |
| **PROCESS** | APIキー確認 → ライブラリインポート → クライアント作成 |
| **OUTPUT** | OpenAI クライアントインスタンス（またはNone） |

#### 🛡️ エラーハンドリング戦略

```python
if os.getenv('OPENAI_API_KEY'):
    try:
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        client = openai.OpenAI()
    except ImportError:
        st.warning("OpenAIライブラリがインストールされていません")
        # アプリケーションは継続実行
```

---

### 📱 MCPApplication実行

#### 🎯 処理概要
helper_mcp.pyモジュールからMCPApplicationクラスをインスタンス化・実行

#### 📊 処理の流れ
```mermaid
graph TD
    A["MCP Execution Start"] --> B["Import MCPApplication"]
    B --> C["Create app instance"]
    C --> D["Call app.run()"]
    D --> E["MCP UI Components"]
    E --> F["Database Connections"]
    F --> G["Session Management"]
    G --> H["MCP Execution Complete"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | helper_mcp.MCPApplication クラス |
| **PROCESS** | インスタンス作成 → run()メソッド実行 |
| **OUTPUT** | 対話型MCPアプリケーション（4つのデータベース対応） |

#### 🔄 MCP統合アーキテクチャ

```python
from helper_mcp import MCPApplication

# MCPアプリケーション実行
app = MCPApplication()
app.run()

# 内部的には以下を統合:
# - PostgreSQL MCP Server
# - Elasticsearch MCP Server
# - Redis MCP Server  
# - Qdrant MCP Server
```

---

## ⚙️ 技術仕様

### 📦 依存ライブラリ

| ライブラリ | バージョン | 用途 | 重要度 |
|-----------|-----------|------|---------|
| `streamlit` | >=1.48.0 | 🌐 Webアプリケーションフレームワーク | ⭐⭐⭐ |
| `python-dotenv` | 最新 | 🔧 環境変数管理 | ⭐⭐⭐ |
| `openai` | >=1.99.9 | 🤖 OpenAI API統合（オプション） | ⭐⭐ |
| `helper_mcp` | 内部 | 📱 MCPアプリケーション機能 | ⭐⭐⭐ |
| `os` | 標準 | 🔧 環境変数・OS操作 | ⭐⭐⭐ |

### 🚀 実行環境仕様

#### 📋 実行方法

```bash
# 基本実行
streamlit run mcp_db_show_data.py --server.port=8501

# Docker環境での実行
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d
streamlit run mcp_db_show_data.py --server.port=8501
```

#### ⚙️ 環境変数設定

```yaml
Required_Environment_Variables:
  OPENAI_API_KEY: "OpenAI API key (optional)"
  PG_CONN_STR: "PostgreSQL connection string"
  REDIS_URL: "Redis connection URL"
  ELASTIC_URL: "Elasticsearch URL"
  QDRANT_URL: "Qdrant URL"
```

#### 📄 設定ファイル構造

```yaml
# .env ファイル例
OPENAI_API_KEY=your_openai_api_key_here
PG_CONN_STR=postgresql://testuser:testpass@localhost:5432/testdb
REDIS_URL=redis://localhost:6379/0
ELASTIC_URL=http://localhost:9200
QDRANT_URL=http://localhost:6333
```

### 🎨 Streamlit UI仕様

#### 📋 ページ設定

```python
Streamlit_Configuration:
  page_title: "MCP サーバー デモ"
  page_icon: "🤖"
  layout: "wide"
  initial_sidebar_state: "auto"
```

#### 🎨 CSS カスタマイズ仕様

```css
Custom_Styles:
  main_header:
    font_size: "2.5rem"
    color: "#1f77b4"
    text_align: "center"
    margin_bottom: "2rem"
  
  status_indicators:
    good: "#28a745"
    bad: "#dc3545"
    weight: "bold"
  
  info_box:
    background: "#f8f9fa"
    padding: "1rem"
    border_radius: "0.5rem"
    border_left: "4px solid #17a2b8"
```

### 🔄 MCP統合仕様

#### 📋 対応データベース

```yaml
MCP_Database_Support:
  postgresql:
    description: "PostgreSQL関係データベース"
    mcp_server_port: 8001
    features: ["SQL自然言語変換", "データ可視化"]
  
  elasticsearch:
    description: "Elasticsearchドキュメントストア"
    mcp_server_port: 8002
    features: ["全文検索", "インデックス管理"]
  
  redis:
    description: "Redisキー・バリューストア"
    mcp_server_port: 8000
    features: ["キャッシュ操作", "セッション管理"]
  
  qdrant:
    description: "Qdrantベクトルデータベース"
    mcp_server_port: 8003
    features: ["セマンティック検索", "埋め込みベクトル"]
```

#### 🏗️ アーキテクチャ連携

```mermaid
graph TD
    A["mcp_db_show_data.py"] --> B["helper_mcp.MCPApplication"]
    B --> C["PostgreSQL MCP Server"]
    B --> D["Elasticsearch MCP Server"]
    B --> E["Redis MCP Server"]
    B --> F["Qdrant MCP Server"]
    
    C --> G["PostgreSQL Database"]
    D --> H["Elasticsearch Cluster"]
    E --> I["Redis Instance"]
    F --> J["Qdrant Vector DB"]
```

---

## 🚨 エラーハンドリング

### 📋 エラーカテゴリ

#### ⚙️ 環境設定関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **.env ファイル不在** | 📄 環境変数ファイル未作成 | デフォルト設定で動作継続・警告表示 | 🟡 中 |
| **必須環境変数未設定** | 🔑 DATABASE_URL等の重要な変数未設定 | 設定指示表示・アプリケーション継続 | 🟡 中 |
| **OpenAI API キー未設定** | 🔑 OPENAI_API_KEY環境変数なし | OpenAI機能無効化・警告表示 | 🟠 低 |

#### 🤖 OpenAI統合関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **OpenAIライブラリ未インストール** | 📦 `pip install openai` 未実行 | 警告表示・OpenAI機能スキップ | 🟠 低 |
| **OpenAI APIキー無効** | 🔑 不正なAPIキー | 警告表示・OpenAI機能無効化 | 🟠 低 |

#### 📱 MCP実行関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **helper_mcp インポートエラー** | 📦 必要モジュール不在 | エラー表示・アプリケーション停止 | 🔴 高 |
| **MCPApplication 初期化失敗** | 🔧 設定・依存関係エラー | 詳細エラー情報表示・修正指示 | 🔴 高 |
| **データベース接続エラー** | 🗄️ DB サーバー未起動・設定誤り | 接続確認指示・代替機能提供 | 🟡 中 |

#### 🎨 Streamlit関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **ポート競合エラー** | 🌐 8501ポート使用中 | 代替ポート指示・解決方法表示 | 🟡 中 |
| **CSS適用エラー** | 🎨 CSS記法・構文エラー | デフォルトスタイルで継続 | 🟠 低 |

### 🛠️ エラーハンドリング戦略

#### 🔧 段階的エラー処理

```mermaid
graph TD
    A["Error Detected"] --> B{"Error Category"}
    B -->|Critical| C["Show Error & Stop"]
    B -->|Medium| D["Warning + Continue"]
    B -->|Low| E["Log + Continue"]

    C --> F["Critical Error Message"]
    D --> G["Warning Display"]
    E --> H["Background Logging"]

    F --> I["User Action Required"]
    G --> J["Reduced Functionality"]
    H --> K["Normal Operation"]
```

#### 🎯 エラー種別別対応

```python
# 環境変数エラー（継続型）
try:
    load_dotenv()
except Exception as e:
    st.warning("環境変数ファイルの読み込みに失敗しました")
    # アプリケーション継続

# OpenAI エラー（オプション機能）
try:
    import openai
    client = openai.OpenAI()
except ImportError:
    st.warning("OpenAIライブラリがインストールされていません")
    # OpenAI機能を無効化して継続

# MCP エラー（クリティカル）
try:
    from helper_mcp import MCPApplication
    app = MCPApplication()
    app.run()
except Exception as e:
    st.error(f"MCPアプリケーション初期化エラー: {e}")
    st.stop()  # アプリケーション停止
```

#### ✅ 適切なエラーメッセージ例

```python
# 環境設定エラー
st.warning("環境変数の設定を確認してください")
st.info("💡 解決方法: .envファイルを作成し、必要な環境変数を設定")

# データベース接続エラー
st.error("⚠️ データベースに接続できません")
st.info("💡 解決方法: Docker Composeでデータベースサーバーを起動してください")

# ライブラリ不足エラー
st.error("必要なライブラリが不足しています")
st.code("pip install openai streamlit python-dotenv")
```

#### 🚨 フォールバック戦略

```python
fallback_strategies = {
    "dotenv_loading": {
        "action": "Continue without .env file",
        "message": "環境変数ファイル不在 → OS環境変数使用"
    },
    "openai_missing": {
        "action": "Disable OpenAI features",
        "message": "OpenAI機能無効化 → MCPのみ動作"
    },
    "mcp_failure": {
        "action": "Display error and stop",
        "message": "MCP機能は必須のため停止"
    },
    "css_error": {
        "action": "Use default styling",
        "message": "カスタムCSS無効化 → デフォルトスタイル"
    }
}
```

#### 📊 復旧手順

```yaml
Recovery_Procedures:
  environment_setup:
    step1: "Create .env file in project root"
    step2: "Set required environment variables"
    step3: "Restart application"
  
  database_connection:
    step1: "Start Docker Compose services"
    step2: "Verify database connectivity"
    step3: "Check MCP server status"
  
  dependency_installation:
    step1: "pip install -r requirements.txt"
    step2: "Verify imports in Python"
    step3: "Restart Streamlit application"
```

---

## 🎉 まとめ

この設計書は、**mcp_db_show_data.py** の完全な技術仕様と実装詳細を記載した包括的なドキュメントです。

### 🌟 設計のハイライト

- **🚀 シンプルエントリーポイント**: 85行でマルチデータベース統合
- **🔄 MCP統合アーキテクチャ**: 4つのデータベースシステム統一インターフェース
- **🎨 統一UI設計**: Streamlit + カスタムCSS による一貫性
- **🛡️ 堅牢なエラー処理**: 段階的フォールバック・継続性重視

### 🔧 アーキテクチャ特徴

- **📦 モジュール分離**: ヘルパーモジュール活用・責務分離
- **⚙️ 柔軟な設定管理**: 環境変数・設定ファイル対応
- **🤖 オプション統合**: OpenAI API の条件付き統合
- **🌐 Web対応**: Streamlit による即座のWeb化

### 📈 MCP統合価値

- **🗄️ マルチデータベース**: PostgreSQL・Elasticsearch・Redis・Qdrant統合
- **🔄 プロトコル標準化**: MCP による統一アクセス方式
- **📱 即時利用**: Dockerコンテナによる迅速な環境構築
- **🎯 デモ特化**: 学習・検証に最適化された構成

### 🚀 拡張可能性

- 🔄 新しいデータベースのMCP対応
- 📊 高度な分析・可視化機能
- 🌐 マルチユーザー対応
- 📱 モバイル最適化
- 🔐 セキュリティ強化機能