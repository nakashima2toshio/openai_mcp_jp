# 📋 mcp_postgresql.py 設計書

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

**MCP経由PostgreSQL自然言語SQLアプリケーション**

mcp_postgresql.pyは、MCP (Model Context Protocol) 経由でPostgreSQLデータベースに自然言語でアクセスするStreamlitアプリケーションです。OpenAI APIを使用してユーザーの自然言語クエリを安全なSQLクエリに変換し、データベースから結果を取得・可視化する高度なデータベース分析システムです。セキュリティを重視し、SELECT文のみを許可する制限付きアクセスを提供します。

#### 🌟 主要機能カテゴリ

| カテゴリ | 機能群 | 説明 |
|---------|--------|------|
| 🗣️ **自然言語SQL変換** | AI SQL生成 | OpenAI APIによる自然言語→PostgreSQLクエリ変換 |
| 🛡️ **セキュリティ管理** | SQL安全性チェック | SELECT文限定・危険キーワード禁止・SQL インジェクション対策 |
| 📊 **データ可視化** | 結果分析・グラフ化 | 棒グラフ・円グラフ・散布図・自動数値列検出 |
| 🤖 **MCP統合** | プロトコル準拠通信 | MCP Server経由でのPostgreSQL操作 |

#### 🔄 自然言語SQL処理フロー

```mermaid
graph TD
    A["自然言語クエリ入力"] --> B["OpenAI API: SQL生成"]
    B --> C["SQL安全性チェック: SELECT文・危険キーワード検証"]
    C --> D["PostgreSQL: 安全なSQL実行"]
    D --> E["結果取得: Dict形式・RealDictCursor"]
    E --> F["OpenAI API: 結果解釈・説明生成"]
    F --> G["Streamlit UI: データ可視化・CSV出力"]
```

### 🔄 主要処理の流れ（MCP+PostgreSQL）

```mermaid
flowchart TD
    Start(["mcp_postgresql.py start"]) --> Init["アプリケーション初期化"]
    Init --> DBManager["MCPDatabaseManager: 接続・スキーマ情報取得"]
    DBManager --> QueryProcessor["MCPQueryProcessor: AI SQL処理準備"]
    QueryProcessor --> UISetup["Streamlit UI: サイドバー・メイン画面構成"]
    
    UISetup --> UserInput["ユーザー自然言語クエリ入力"]
    UserInput --> AISQL["OpenAI API: SQL生成"]
    AISQL --> Security["SQL安全性チェック"]
    Security --> PGExec["PostgreSQL: SQL実行"]
    PGExec --> ResultProcess["結果処理: Dict変換・データフレーム化"]
    ResultProcess --> AIExplain["OpenAI API: 結果説明生成"]
    AIExplain --> Visualize["データ可視化: グラフ・チャート・CSV"]
    
    DBManager --> Schema["customers・orders・products スキーマ"]
    PGExec --> Schema
```

---

## 🔧 システム構成

### 📦 主要コンポーネント

```mermaid
classDiagram
    class MCPDatabaseManager {
        +mcp_server_url: str
        +pg_conn_str: str
        +schema_info: dict
        +_pg_connection: psycopg2.connection
        +get_schema_info()
        +_get_actual_schema()
    }

    class MCPQueryProcessor {
        +openai_client: OpenAIClient
        +db_manager: MCPDatabaseManager
        +schema_info: dict
        +build_mcp_prompt()
        +execute_mcp_query()
        +_generate_sql_via_ai()
        +_execute_sql_directly()
        +_is_safe_query()
        +explain_results()
    }

    class NaturalLanguageDBInterface {
        +openai_client: OpenAIClient
        +query_processor: MCPQueryProcessor
        +create_sidebar()
        +create_main_interface()
        +execute_mcp_query()
        +display_results()
        +run()
    }

    class PostgreSQLSchemas {
        +customers: TableSchema
        +orders: TableSchema
        +products: TableSchema
    }

    MCPDatabaseManager --> PostgreSQLSchemas
    MCPQueryProcessor --> MCPDatabaseManager
    NaturalLanguageDBInterface --> MCPQueryProcessor
```

### 📋 データフロー（SQL実行）

```mermaid
graph TD
    A["ユーザークエリ: '東京在住の30歳以上の顧客'"] --> B["OpenAI API: SQL生成"]
    B --> C["生成SQL: SELECT * FROM customers WHERE city='東京' AND age>=30"]
    C --> D["安全性チェック: SELECT文・危険キーワード"]
    D --> E["PostgreSQL実行: psycopg2.RealDictCursor"]
    E --> F["結果: [{id: 1, name: '田中', age: 35}, ...]"]
    F --> G["OpenAI API: 結果説明生成"]
    G --> H["UI表示: データフレーム・グラフ・CSV出力"]
    
    D --> I["危険SQL検出"]
    I --> J["実行拒否・警告表示"]
```

---

## 📋 関数一覧

### 🗄️ PostgreSQLデータベース管理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `MCPDatabaseManager.__init__()` | 🏗️ 初期化 | MCP URL・PG接続文字列設定・接続プール準備 | ⭐⭐⭐ |
| `MCPDatabaseManager.get_schema_info()` | 📊 スキーマ取得 | テーブル構造・カラム情報キャッシュ取得 | ⭐⭐⭐ |

### 🤖 AI SQL生成処理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `MCPQueryProcessor.build_mcp_prompt()` | 📝 プロンプト | MCP用システム・ユーザープロンプト構築 | ⭐⭐⭐ |
| `MCPQueryProcessor.execute_mcp_query()` | 🔍 SQL実行 | AI SQL生成→安全性チェック→PG実行→説明の全体制御 | ⭐⭐⭐ |
| `MCPQueryProcessor._generate_sql_via_ai()` | 🧠 AI SQL | OpenAI APIによるPostgreSQL SQL生成 | ⭐⭐⭐ |
| `MCPQueryProcessor._execute_sql_directly()` | 🔍 PG実行 | PostgreSQL SQL直接実行・結果辞書変換 | ⭐⭐⭐ |
| `MCPQueryProcessor.explain_results()` | 📖 結果説明 | OpenAI APIによるクエリ結果解釈 | ⭐⭐ |

### 🛡️ セキュリティ・安全性処理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `_is_safe_query()` | 🛡️ 安全性チェック | SELECT文限定・危険キーワード検出 | ⭐⭐⭐ |
| `_clean_sql_query()` | 🔧 SQL処理 | マークダウン除去・セミコロン補完 | ⭐⭐⭐ |

### 🎨 Streamlit UI管理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `NaturalLanguageDBInterface.__init__()` | 🏗️ 初期化 | OpenAI・DB manager・セッション初期化 | ⭐⭐⭐ |
| `create_sidebar()` | 🎛️ サイドバー | モデル選択・スキーマ情報・履歴表示 | ⭐⭐ |
| `create_main_interface()` | 🖥️ メイン画面 | クエリ入力・候補表示・実行制御 | ⭐⭐⭐ |
| `display_results()` | 📊 結果表示 | データフレーム・グラフ・CSV ダウンロード | ⭐⭐ |
| `get_query_suggestions()` | 💡 候補生成 | 自然言語SQL クエリ例12個の提供 | ⭐ |

### 🔧 ユーティリティ・設定

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `_init_session_state()` | ⚙️ セッション | Streamlitセッション状態初期化 | ⭐⭐ |
| `get_available_models()` | 🎯 モデル管理 | 利用可能OpenAIモデル一覧取得 | ⭐⭐ |
| `_check_mcp_server_status()` | 🔍 状態確認 | MCP/PostgreSQL サーバー接続状態確認 | ⭐⭐ |

---

## 📑 関数詳細設計

### 🧠 _generate_sql_via_ai()

#### 🎯 処理概要
ユーザーの自然言語クエリをOpenAI APIでPostgreSQL SQLクエリに変換

#### 📊 処理の流れ
```mermaid
graph TD
    A["User Query Input"] --> B["スキーマ情報テキスト化"]
    B --> C["SQL生成プロンプト構築"]
    C --> D["OpenAI API: SQL生成"]
    D --> E["AI応答テキスト取得"]
    E --> F["SQL クリーンアップ"]
    F --> G{"SQL生成成功?"}
    G -->|Yes| H["生成SQL・説明返却"]
    G -->|No| I["空文字列・エラー返却"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `user_query: str` - 自然言語クエリ<br>`model: str` - OpenAI モデル名 |
| **PROCESS** | スキーマプロンプト構築 → OpenAI API呼び出し → SQL抽出・クリーンアップ |
| **OUTPUT** | `Tuple[str, str]` - 生成SQL・説明文 |

#### 🔧 SQL生成プロンプト構造

```python
sql_prompt_template = """以下のデータベーススキーマに基づいて、ユーザーの質問に対応するPostgreSQLクエリを生成してください。

【データベーススキーマ】
【テーブル: customers】
  - id (integer) NOT NULL
  - name (character varying) NOT NULL
  - email (character varying) NOT NULL
  - age (integer) NULL可
  - city (character varying) NULL可
  - created_at (timestamp without time zone) NULL可

【テーブル: orders】
  - id (integer) NOT NULL
  - customer_id (integer) NULL可
  - product_name (character varying) NOT NULL
  - price (numeric) NOT NULL
  - quantity (integer) NOT NULL
  - order_date (timestamp without time zone) NULL可

【テーブル: products】
  - id (integer) NOT NULL
  - name (character varying) NOT NULL
  - category (character varying) NULL可
  - price (numeric) NOT NULL
  - stock_quantity (integer) NULL可
  - description (text) NULL可

【制約】
- SELECT文のみ生成してください
- 安全なクエリを心がけてください
- SQLクエリのみを出力してください（説明不要）

【質問】: {user_query}

SQL:"""
```

---

### 🛡️ _is_safe_query()

#### 🎯 処理概要
生成されたSQLクエリの安全性をチェック（SQL インジェクション対策）

#### 📊 処理の流れ
```mermaid
graph TD
    A["SQL Query Input"] --> B["大文字変換・前後空白除去"]
    B --> C{"SELECT or WITH で開始?"}
    C -->|No| D["危険: False返却"]
    C -->|Yes| E["危険キーワード検査"]
    E --> F{"危険キーワード存在?"}
    F -->|Yes| D
    F -->|No| G["安全: True返却"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `sql: str` - 検証対象SQLクエリ |
| **PROCESS** | 文字列正規化 → 開始文検証 → 危険キーワード検査 |
| **OUTPUT** | `bool` - 安全性判定結果 |

#### 🛡️ セキュリティチェック仕様

```python
# 許可される開始文
allowed_starts = ('SELECT', 'WITH')

# 危険なキーワード（大文字）
dangerous_keywords = [
    'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
    'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
]

# チェックロジック
def _is_safe_query(self, sql: str) -> bool:
    sql_upper = sql.upper().strip()
    
    # SELECT文のみ許可
    if not sql_upper.startswith(allowed_starts):
        return False
    
    # 危険キーワード検出
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    return True
```

---

### 🔍 _execute_sql_directly()

#### 🎯 処理概要
安全性チェック済みSQLをPostgreSQLで実行・結果をDict形式で返却

#### 📊 処理の流れ
```mermaid
graph TD
    A["安全なSQL"] --> B["安全性再チェック"]
    B --> C{"安全?"}
    C -->|No| D["ValueError例外発生"]
    C -->|Yes| E["psycopg2接続作成"]
    E --> F["RealDictCursor使用"]
    F --> G["SQL実行"]
    G --> H["結果fetch"]
    H --> I["Dict形式変換"]
    I --> J["接続自動クローズ"]
    J --> K["結果リスト返却"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `sql_query: str` - 実行対象SQL |
| **PROCESS** | 安全性確認 → DB接続 → カーソル作成 → SQL実行 → 結果変換 |
| **OUTPUT** | `List[Dict]` - クエリ結果（辞書のリスト） |

#### 🔧 PostgreSQL実行アーキテクチャ

```python
def _execute_sql_directly(self, sql_query: str) -> List[Dict]:
    # 安全性チェック
    if not self._is_safe_query(sql_query):
        raise ValueError("安全でないクエリです")
    
    # Context Manager でリソース管理
    with psycopg2.connect(
        self.db_manager.pg_conn_str,
        cursor_factory=psycopg2.extras.RealDictCursor
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    
    # 自動的にconnection・cursor がクローズされる
```

---

### 📖 explain_results()

#### 🎯 処理概要
PostgreSQLクエリ結果をOpenAI APIで自然言語解釈・説明生成

#### 📊 処理の流れ
```mermaid
graph TD
    A["クエリ結果リスト"] --> B{"結果存在確認"}
    B -->|なし| C["'結果なし'メッセージ"]
    B -->|あり| D["結果サマリー作成"]
    D --> E["件数に応じた詳細度調整"]
    E --> F["説明生成プロンプト構築"]
    F --> G["OpenAI API: 結果解釈"]
    G --> H["自然言語説明取得"]
    H --> I{"API成功?"}
    I -->|Yes| J["説明文返却"]
    I -->|No| K["デフォルト説明返却"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `query: str` - 元クエリ<br>`results: List[Dict]` - PG クエリ結果<br>`model: str` - OpenAIモデル |
| **PROCESS** | 結果確認 → サマリー作成 → 詳細度調整 → OpenAI API → 説明抽出 |
| **OUTPUT** | `str` - 自然言語による検索結果説明 |

#### 🔧 説明生成プロンプト

```python
# 結果が5件以下の場合
if len(results) <= 5:
    result_summary += "\n結果データ:\n"
    for i, row in enumerate(results, 1):
        result_summary += f"{i}. {dict(row)}\n"

# 結果が多い場合
else:
    result_summary += f"\n最初の3件:\n"
    for i, row in enumerate(results[:3], 1):
        result_summary += f"{i}. {dict(row)}\n"
    result_summary += f"... (他{len(results)-3}件)"

system_prompt = """あなたは分析結果を分かりやすく説明する専門家です。
データベースの検索結果を自然な日本語で要約してください。"""

user_content = f"""以下の検索結果について、わかりやすく日本語で説明してください:

質問: {query}

{result_summary}"""
```

---

### 📊 display_results()

#### 🎯 処理概要
PostgreSQLクエリ結果のデータフレーム表示・可視化・CSV出力

#### 📊 処理の流れ
```mermaid
graph TD
    A["結果表示開始"] --> B{"結果存在?"}
    B -->|No| C["'結果なし'警告"]
    B -->|Yes| D["pandas DataFrame作成"]
    D --> E["データフレーム表示"]
    E --> F["数値カラム検出"]
    F --> G{"数値カラムあり?"}
    G -->|Yes| H["可視化オプション表示"]
    H --> I["グラフタイプ選択"]
    I --> J["Plotly グラフ作成"]
    J --> K["CSV ダウンロードボタン"]
    G -->|No| K
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `st.session_state.current_results` - PostgreSQL結果 |
| **PROCESS** | DataFrame変換 → 表示 → 数値検出 → 可視化 → エクスポート |
| **OUTPUT** | Streamlit UI（表・グラフ・ダウンロード） |

#### 📊 データ可視化仕様

```python
# 数値カラム自動検出
numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns

# 対応グラフタイプ
chart_types = ["棒グラフ", "折れ線グラフ", "円グラフ", "散布図"]

# 棒グラフ例
if chart_type == "棒グラフ" and len(df.columns) >= 2:
    x_col = st.selectbox("X軸:", df.columns, index=0)
    y_col = st.selectbox("Y軸:", numeric_columns, index=0)
    fig = px.bar(df, x=x_col, y=y_col)
    st.plotly_chart(fig, use_container_width=True)

# 円グラフ例
elif chart_type == "円グラフ" and len(numeric_columns) > 0:
    values_col = st.selectbox("値:", numeric_columns)
    names_col = st.selectbox("ラベル:", df.columns)
    fig = px.pie(df, values=values_col, names=names_col)
    st.plotly_chart(fig, use_container_width=True)

# CSV出力
csv = df.to_csv(index=False, encoding='utf-8')
st.download_button(
    label="📥 CSVダウンロード",
    data=csv,
    file_name=f"query_results_{int(time.time())}.csv",
    mime="text/csv"
)
```

---

## ⚙️ 技術仕様

### 📦 依存ライブラリ

| ライブラリ | バージョン | 用途 | 重要度 |
|-----------|-----------|------|---------|
| `streamlit` | >=1.48.0 | 🌐 Webアプリケーションフレームワーク | ⭐⭐⭐ |
| `psycopg2-binary` | 最新 | 🗄️ PostgreSQL公式クライアント | ⭐⭐⭐ |
| `openai` | >=1.99.9 | 🤖 OpenAI API（SQL生成・結果説明） | ⭐⭐⭐ |
| `pandas` | 最新 | 📋 データフレーム処理・分析 | ⭐⭐⭐ |
| `plotly` | 最新 | 📊 インタラクティブ可視化 | ⭐⭐ |
| `time` | 標準 | ⏰ タイムスタンプ・ファイル名生成 | ⭐⭐ |
| `typing` | 標準 | 🔧 型ヒント・タプル定義 | ⭐⭐ |
| `python-dotenv` | 最新 | 🔧 環境変数管理 | ⭐⭐⭐ |

### 🗄️ PostgreSQL統合仕様

#### 📋 デフォルトテーブルスキーマ

```yaml
Customers_Table:
  description: "顧客情報テーブル"
  columns:
    id: "integer NOT NULL (primary key)"
    name: "character varying NOT NULL"
    email: "character varying NOT NULL"
    age: "integer NULL"
    city: "character varying NULL"
    created_at: "timestamp without time zone NULL"
  sample_data_count: "multiple records"
  
Orders_Table:
  description: "注文情報テーブル"
  columns:
    id: "integer NOT NULL (primary key)"
    customer_id: "integer NULL (foreign key)"
    product_name: "character varying NOT NULL"
    price: "numeric NOT NULL"
    quantity: "integer NOT NULL"
    order_date: "timestamp without time zone NULL"
  sample_data_count: "multiple records"

Products_Table:
  description: "商品情報テーブル"
  columns:
    id: "integer NOT NULL (primary key)"
    name: "character varying NOT NULL"
    category: "character varying NULL"
    price: "numeric NOT NULL"
    stock_quantity: "integer NULL"
    description: "text NULL"
  sample_data_count: "multiple records"
```

#### 🔧 PostgreSQL接続仕様

```yaml
Connection_Configuration:
  driver: "psycopg2-binary"
  cursor_factory: "psycopg2.extras.RealDictCursor"
  context_manager: "automatic resource cleanup"
  timeout: "3 seconds (connection check)"
  
Connection_String_Format:
  default: "postgresql://testuser:testpass@localhost:5432/testdb"
  environment_variable: "PG_CONN_STR"
  
SQL_Safety:
  allowed_statements: ["SELECT", "WITH"]
  forbidden_keywords: ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"]
  injection_protection: "keyword blacklist + statement whitelist"
```

### 🤖 OpenAI API統合仕様

#### 📋 使用APIエンドポイント

```yaml
OpenAI_API_Usage:
  sql_generation:
    endpoint: "responses.create()"
    model: "gpt-5-mini (default)"
    purpose: "自然言語→PostgreSQL SQL変換"
    input_format: "スキーマ情報+制約+ユーザークエリ"
    output_format: "実行可能SQLクエリ"
  
  result_explanation:
    endpoint: "responses.create()"
    model: "gpt-4o-mini (default)"
    purpose: "クエリ結果の自然言語説明"
    input_format: "結果サマリー+元クエリ"
    output_format: "日本語説明文"
```

#### 🎯 プロンプトエンジニアリング

```python
# SQL生成プロンプト構造
sql_generation_template = """以下のデータベーススキーマに基づいて、ユーザーの質問に対応するPostgreSQLクエリを生成してください。

【データベーススキーマ】
{schema_text}

【制約】
- SELECT文のみ生成してください
- 安全なクエリを心がけてください
- SQLクエリのみを出力してください（説明不要）

【質問】: {user_query}

SQL:"""

# 結果説明プロンプト
explanation_template = """あなたは分析結果を分かりやすく説明する専門家です。データベースの検索結果を自然な日本語で要約してください。

以下の検索結果について、わかりやすく日本語で説明してください:

質問: {query}

{result_summary}"""
```

### 🌐 Streamlit UI仕様

#### 📋 ページ設定

```python
Streamlit_Configuration:
  page_title: "MCP経由PostgreSQLアクセス"
  page_icon: "🗣️"
  layout: "wide"
  initial_sidebar_state: "expanded"
```

#### 🎨 UI コンポーネント設計

```yaml
Sidebar_Components:
  model_selection:
    widget: "selectbox"
    options: ["gpt-5", "gpt-5-mini", "gpt-4.1", "gpt-4o", "o3"]
    default: "gpt-5-mini"
  
  schema_information:
    widget: "expander"
    content: "テーブル構造・カラム情報・データ型"
  
  query_history:
    widget: "button_list"
    limit: 5
    format: "truncated_query + execution_status"

Main_Interface_Components:
  api_information:
    widget: "expander"
    content: "OpenAI API・MCP動作コード例"
  
  query_input:
    widget: "text_input + button"
    layout: "3:1 column ratio"
    placeholder: "例: 東京在住の30歳以上の顧客を表示して"
  
  query_suggestions:
    widget: "button_grid"
    layout: "3 columns"
    count: 12
    
  results_display:
    widget: "dataframe + charts + download_button"
    formats: ["table", "bar_chart", "pie_chart", "scatter_plot", "csv"]
```

#### 🔢 自然言語クエリ候補

```python
query_suggestions = [
    "全ての顧客を表示して",
    "東京在住の顧客を表示して",
    "30歳以上の顧客を表示して",
    "各都市の顧客数を教えて",
    "最も売上の高い商品トップ5を表示して",
    "注文金額の平均値を教えて",
    "各顧客の総注文金額を表示して",
    "在庫が10個以下の商品を表示して",
    "エレクトロニクス商品の在庫状況を教えて",
    "月別の売上推移を表示して",
    "顧客の年齢別分布を教えて",
    "注文件数が多い商品ランキングを表示して"
]
```

### 🔄 MCP統合仕様

#### 📋 MCPサーバー通信

```yaml
MCP_Server_Configuration:
  postgresql_mcp_server:
    url: "http://localhost:8001/mcp"
    protocol: "HTTP/SSE"
    features: ["sql_execution", "schema_introspection"]
  
  communication_flow:
    step1: "Streamlit UI → OpenAI Responses API"
    step2: "AI SQL生成 → 安全性チェック"
    step3: "MCP Server → PostgreSQL"
    step4: "クエリ結果 → OpenAI解釈 → UI可視化"
```

#### 🏗️ アーキテクチャ連携

```mermaid
graph TD
    A["mcp_postgresql.py"] --> B["MCPDatabaseManager"]
    B --> C["MCP Server (Port 8001)"]
    C --> D["PostgreSQL Database"]
    
    A --> E["MCPQueryProcessor"]
    E --> F["OpenAI Responses API"]
    F --> G["SQL生成"]
    F --> H["結果説明生成"]
    
    A --> I["NaturalLanguageDBInterface"]
    I --> J["Streamlit Web UI"]
    J --> K["Plotly Visualizations"]
```

---

## 🚨 エラーハンドリング

### 📋 エラーカテゴリ

#### 🗄️ PostgreSQL関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **PostgreSQL接続エラー** | 🌐 サーバー未起動・接続文字列誤り | 接続確認手順表示・設定見直し指示 | 🔴 高 |
| **SQL構文エラー** | 🔤 不正なSQL文・AI生成ミス | SQL修正・シンプルクエリ代替 | 🟡 中 |
| **テーブル不存在エラー** | 📊 指定テーブル存在しない | スキーマ確認・テーブル作成指示 | 🟡 中 |
| **権限エラー** | 🔒 DB ユーザー権限不足 | 権限設定確認・ユーザー変更指示 | 🟡 中 |

#### 🛡️ セキュリティ関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **危険SQL検出** | 🚨 DROP・DELETE等の危険文検出 | 実行拒否・安全なクエリ指示 | 🔴 高 |
| **SQL インジェクション疑い** | 🔐 不正な文字列・構文検出 | クエリ拒否・セキュリティ警告 | 🔴 高 |
| **非SELECT文実行試行** | 🛑 INSERT・UPDATE等の実行試行 | 実行拒否・SELECT限定説明 | 🔴 高 |

#### 🤖 OpenAI API関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **API キー未設定・無効** | 🔑 認証エラー | キー確認指示・機能制限モード | 🔴 高 |
| **SQL生成失敗** | 🧠 AI応答不正・プロンプト問題 | シンプルクエリ提案・マニュアル入力 | 🟡 中 |
| **レート制限エラー** | ⏱️ API使用量上限 | 待機時間表示・リトライ機構 | 🟡 中 |
| **モデル不存在エラー** | 🤖 指定モデル利用不可 | デフォルトモデル切り替え | 🟠 低 |

#### 📊 データ処理関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **DataFrame変換エラー** | 📋 複雑なデータ型・NULL処理 | 型変換・NULL値処理・警告表示 | 🟡 中 |
| **可視化エラー** | 📈 数値データ不足・形式不適 | グラフタイプ制限・エラー表示 | 🟠 低 |
| **CSV出力エラー** | 💾 エンコーディング・容量問題 | UTF-8強制・分割出力提案 | 🟠 低 |

### 🛠️ エラーハンドリング戦略

#### 🔧 段階的セキュリティ処理

```mermaid
graph TD
    A["SQL Query Generated"] --> B["Basic Safety Check"]
    B --> C{"SELECT/WITH start?"}
    C -->|No| D["Immediate Rejection"]
    C -->|Yes| E["Keyword Blacklist Check"]
    E --> F{"Dangerous keywords?"}
    F -->|Yes| D
    F -->|No| G["Pattern Analysis"]
    G --> H{"Injection patterns?"}
    H -->|Yes| D
    H -->|No| I["Approved for Execution"]

    D --> J["Security Warning Display"]
    I --> K["PostgreSQL Execution"]
```

#### 🎯 具体的エラーハンドリング実装

```python
# PostgreSQL接続エラー（重要）
def _check_mcp_server_status(self):
    try:
        with psycopg2.connect(self.db_manager.pg_conn_str, connect_timeout=3) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"PostgreSQL connection check failed: {e}")
        return False

# SQL安全性チェック（クリティカル）
def _is_safe_query(self, sql: str) -> bool:
    sql_upper = sql.upper().strip()
    
    # SELECT文のみ許可
    if not sql_upper.startswith(('SELECT', 'WITH')):
        return False
    
    # 危険なキーワードをチェック
    dangerous_keywords = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
        'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False
    
    return True

# SQL実行エラー（安全性重視）
def _execute_sql_directly(self, sql_query: str):
    # 安全性チェック
    if not self._is_safe_query(sql_query):
        raise ValueError("安全でないクエリです")
    
    try:
        with psycopg2.connect(
            self.db_manager.pg_conn_str,
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                results = cursor.fetchall()
                return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Direct SQL execution error: {e}")
        raise
```

#### ✅ ユーザーフレンドリーなエラーメッセージ

```python
# PostgreSQL接続エラー
if not mcp_status:
    st.error("⚠️ PostgreSQLデータベースに接続できません")
    st.info("💡 **解決方法**:\n1. `docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d postgres` でPostgreSQLを起動\n2. 環境変数 `PG_CONN_STR` を確認してください")

# セキュリティエラー  
if not success:
    st.error(f"MCPクエリ実行エラー: {response_message}")
    return

# 成功時の情報表示
st.success("MCP経由でデータを取得しました！")
with st.expander("🤖 MCPサーバーからの応答", expanded=True):
    st.markdown(response_message)
```

#### 🚨 復旧・診断手順

```yaml
Diagnostic_Procedures:
  postgresql_connection:
    step1: "psql postgresql://testuser:testpass@localhost:5432/testdb"
    step2: "docker-compose logs postgres"
    step3: "Check PG_CONN_STR environment variable"
  
  mcp_server_verification:
    step1: "curl http://localhost:8001/mcp"
    step2: "docker-compose ps"
    step3: "Check MCP server logs"
  
  sql_safety_verification:
    step1: "Review generated SQL for dangerous keywords"
    step2: "Test SQL manually with read-only user"
    step3: "Verify query starts with SELECT/WITH"
  
  openai_api_troubleshooting:
    step1: "Verify OPENAI_API_KEY in .env"
    step2: "Test API connectivity"
    step3: "Check SQL generation prompt effectiveness"
```

#### 🔄 自動復旧メカニズム

```python
auto_recovery_strategies = {
    "postgresql_connection": {
        "trigger": "Connection timeout or authentication failure",
        "action": "Display connection instructions",
        "notification": "PostgreSQL接続確認が必要です"
    },
    "dangerous_sql_detection": {
        "trigger": "Dangerous keywords in generated SQL",
        "action": "Block execution and suggest safe alternatives",
        "notification": "安全でないSQLのため実行を拒否しました"
    },
    "sql_generation_failure": {
        "trigger": "OpenAI API fails to generate valid SQL",
        "action": "Provide manual SQL input option",
        "notification": "手動でSQLを入力してください"
    },
    "data_visualization_error": {
        "trigger": "Chart generation fails due to data type issues",
        "action": "Fall back to table display only",
        "notification": "データ表示のみ利用可能です"
    }
}
```

---

## 🎉 まとめ

この設計書は、**mcp_postgresql.py** の完全な技術仕様と実装詳細を記載した包括的なドキュメントです。

### 🌟 設計のハイライト

- **🗣️ 自然言語SQL**: OpenAI APIによる直感的なデータベースクエリ
- **🛡️ セキュリティ重視**: SELECT文限定・危険キーワード禁止・SQL インジェクション対策
- **📊 データ可視化**: 自動グラフ生成・CSV出力・インタラクティブ分析
- **🤖 MCP準拠**: Model Context Protocol標準アーキテクチャ

### 🔧 アーキテクチャ特徴

- **🔒 セキュリティファースト**: 多層防御・安全性チェック・権限制御
- **🔄 AI統合**: SQL生成+結果説明のダブルAI活用
- **📱 直感的UI**: 候補選択・リアルタイム可視化・履歴管理
- **⚙️ 堅牢性**: エラーハンドリング・自動復旧・診断機能

### 📈 自然言語データベース価値

- **🧠 知的分析**: 技術的SQL知識不要の高度なデータ分析
- **🔍 探索的クエリ**: 自然な質問形式でのデータ探索
- **📊 即座の可視化**: クエリ結果の自動グラフ化・パターン発見
- **📖 結果解釈**: AI による分析結果の自動解釈・説明

### 🚀 拡張可能性

- 🔄 新しいテーブル・ビューの動的対応
- 📊 高度な統計分析・機械学習クエリ
- 🌐 マルチデータベース・フェデレーション
- 📱 リアルタイムダッシュボード・アラート
- 🔐 高度なセキュリティ・監査ログ・アクセス制御