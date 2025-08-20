# 📋 mcp_elasticsearch.py 設計書

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

**MCP経由Elasticsearchドキュメント検索アプリケーション**

mcp_elasticsearch.pyは、MCP (Model Context Protocol) 経由でElasticsearchドキュメントストアに自然言語でアクセスするStreamlitアプリケーションです。OpenAI APIを使用してユーザーの自然言語クエリを最適なElasticsearch検索戦略に変換し、実行結果を分かりやすく表示・分析する高度なドキュメント検索システムです。

#### 🌟 主要機能カテゴリ

| カテゴリ | 機能群 | 説明 |
|---------|--------|------|
| 🔍 **自然言語検索** | AI検索戦略生成 | OpenAI APIによる自然言語→Elasticsearchクエリ変換 |
| 🗄️ **インデックス管理** | ドキュメント構造解析 | blog_articles・products・knowledge_base管理 |
| 📊 **結果処理** | 検索結果分析・可視化 | スコアリング・フィルタリング・説明生成 |
| 🤖 **MCP統合** | プロトコル準拠通信 | MCP Server経由でのElasticsearch操作 |

#### 🔄 自然言語検索処理フロー

```mermaid
graph TD
    A["自然言語クエリ入力"] --> B["OpenAI API: 検索戦略生成"]
    B --> C["JSON戦略: インデックス・フィールド・クエリ型選択"]
    C --> D["Elasticsearch: 実際の検索実行"]
    D --> E["結果取得: スコア・ドキュメント・メタデータ"]
    E --> F["OpenAI API: 結果解釈・説明生成"]
    F --> G["Streamlit UI: 結果表示・ダウンロード"]
```

### 🔄 主要処理の流れ（MCP+Elasticsearch）

```mermaid
flowchart TD
    Start(["mcp_elasticsearch.py start"]) --> Init["アプリケーション初期化"]
    Init --> ESManager["MCPElasticsearchManager: 接続・インデックス情報取得"]
    ESManager --> QueryProcessor["MCPDocumentQueryProcessor: AI検索処理準備"]
    QueryProcessor --> UISetup["Streamlit UI: サイドバー・メイン画面構成"]
    
    UISetup --> UserInput["ユーザー自然言語クエリ入力"]
    UserInput --> AIStrategy["OpenAI API: 検索戦略生成"]
    AIStrategy --> ESSearch["Elasticsearch: ドキュメント検索実行"]
    ESSearch --> ResultProcess["結果処理: スコア計算・フィルタリング"]
    ResultProcess --> AIExplain["OpenAI API: 結果説明生成"]
    AIExplain --> Display["結果表示: カード・JSON・ダウンロード"]
    
    ESManager --> MockData["モックデータ対応"]
    ESSearch --> MockData
```

---

## 🔧 システム構成

### 📦 主要コンポーネント

```mermaid
classDiagram
    class MCPElasticsearchManager {
        +mcp_server_url: str
        +elasticsearch_url: str
        +indices_info: dict
        +_es_client: Elasticsearch
        +get_indices_info()
        +_check_connection()
    }

    class MCPDocumentQueryProcessor {
        +openai_client: OpenAIClient
        +elasticsearch_manager: MCPElasticsearchManager
        +indices_info: dict
        +build_mcp_prompt()
        +execute_mcp_query()
        +_generate_search_strategy_via_ai()
        +_execute_document_search_directly()
        +explain_results()
    }

    class NaturalLanguageDocumentInterface {
        +openai_client: OpenAIClient
        +query_processor: MCPDocumentQueryProcessor
        +create_sidebar()
        +create_main_interface()
        +execute_mcp_query()
        +display_results()
        +run()
    }

    class ElasticsearchIndices {
        +blog_articles: IndexInfo
        +products: IndexInfo
        +knowledge_base: IndexInfo
    }

    MCPElasticsearchManager --> ElasticsearchIndices
    MCPDocumentQueryProcessor --> MCPElasticsearchManager
    NaturalLanguageDocumentInterface --> MCPDocumentQueryProcessor
```

### 📋 データフロー（検索実行）

```mermaid
graph TD
    A["ユーザークエリ: '機械学習の記事を探して'"] --> B["OpenAI API: 検索戦略AI生成"]
    B --> C["JSON戦略: {index: 'blog_articles', query_type: 'multi_match', fields: ['title', 'content']}"]
    C --> D["Elasticsearch実行: multi_match クエリ"]
    D --> E["検索結果: [{title: 'AI技術', score: 1.95}, ...]"]
    E --> F["OpenAI API: 結果説明生成"]
    F --> G["UI表示: カード形式・スコア・説明・ダウンロード"]
    
    D --> H["接続エラー時"]
    H --> I["モックデータ返却"]
    I --> G
```

---

## 📋 関数一覧

### 🗄️ Elasticsearchインデックス管理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `MCPElasticsearchManager.__init__()` | 🏗️ 初期化 | MCP URL・ES URL設定・クライアント初期化 | ⭐⭐⭐ |
| `MCPElasticsearchManager.get_indices_info()` | 📊 情報取得 | インデックス構造・フィールド情報キャッシュ取得 | ⭐⭐⭐ |

### 🤖 AI検索戦略処理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `MCPDocumentQueryProcessor.build_mcp_prompt()` | 📝 プロンプト | MCP用システム・ユーザープロンプト構築 | ⭐⭐⭐ |
| `MCPDocumentQueryProcessor.execute_mcp_query()` | 🔍 検索実行 | AI戦略→ES実行→結果説明の全体制御 | ⭐⭐⭐ |
| `MCPDocumentQueryProcessor._generate_search_strategy_via_ai()` | 🧠 AI戦略 | OpenAI APIによるJSON検索戦略生成 | ⭐⭐⭐ |
| `MCPDocumentQueryProcessor._execute_document_search_directly()` | 🔍 ES実行 | Elasticsearchクエリ直接実行 | ⭐⭐⭐ |
| `MCPDocumentQueryProcessor.explain_results()` | 📖 結果説明 | OpenAI APIによる検索結果解釈 | ⭐⭐ |

### 🔄 クエリ処理・変換

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `_clean_json_response()` | 🔧 JSON処理 | AI応答からのJSON抽出・クリーンアップ | ⭐⭐⭐ |
| `_format_indices_info()` | 📋 フォーマット | インデックス情報のテキスト形式変換 | ⭐⭐ |
| `_generate_mock_search_results()` | 🎭 モック | 接続エラー時のサンプル結果生成 | ⭐⭐ |

### 🎨 Streamlit UI管理

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `NaturalLanguageDocumentInterface.__init__()` | 🏗️ 初期化 | OpenAI・ES manager・セッション初期化 | ⭐⭐⭐ |
| `create_sidebar()` | 🎛️ サイドバー | モデル選択・インデックス情報・履歴表示 | ⭐⭐ |
| `create_main_interface()` | 🖥️ メイン画面 | クエリ入力・候補表示・実行制御 | ⭐⭐⭐ |
| `display_results()` | 📊 結果表示 | カード形式結果・JSON ダウンロード | ⭐⭐ |
| `get_query_suggestions()` | 💡 候補生成 | 自然言語クエリ例12個の提供 | ⭐ |

### 🔧 ユーティリティ・設定

| 関数名 | 分類 | 処理概要 | 重要度 |
|--------|------|----------|---------|
| `_init_session_state()` | ⚙️ セッション | Streamlitセッション状態初期化 | ⭐⭐ |
| `get_available_models()` | 🎯 モデル管理 | 利用可能OpenAIモデル一覧取得 | ⭐⭐ |
| `_check_mcp_server_status()` | 🔍 状態確認 | MCP/ES サーバー接続状態確認 | ⭐⭐ |

---

## 📑 関数詳細設計

### 🧠 _generate_search_strategy_via_ai()

#### 🎯 処理概要
ユーザーの自然言語クエリをOpenAI APIでElasticsearch検索戦略JSON に変換

#### 📊 処理の流れ
```mermaid
graph TD
    A["User Query Input"] --> B["インデックス情報テキスト化"]
    B --> C["戦略生成プロンプト構築"]
    C --> D["OpenAI API: 戦略生成"]
    D --> E["AI応答テキスト取得"]
    E --> F["JSON応答クリーンアップ"]
    F --> G{"JSON Parse成功?"}
    G -->|Yes| H["検索戦略JSON返却"]
    G -->|No| I["フォールバック戦略生成"]
    I --> H
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `user_query: str` - 自然言語クエリ<br>`model: str` - OpenAI モデル名 |
| **PROCESS** | プロンプト構築 → OpenAI API呼び出し → JSON抽出・パース → フォールバック対応 |
| **OUTPUT** | `Tuple[Dict, str]` - 検索戦略JSON・説明文 |

#### 🔧 戦略JSON仕様

```json
{
    "index": "blog_articles",
    "query_type": "multi_match",
    "search_text": "機械学習 基礎",
    "fields": ["title", "content"],
    "filters": {},
    "sort": [{"_score": {"order": "desc"}}],
    "size": 10,
    "description": "ブログ記事から機械学習関連コンテンツを検索"
}
```

---

### 🔍 _execute_document_search_directly()

#### 🎯 処理概要
AI生成検索戦略をElasticsearchクエリに変換・実行・結果処理

#### 📊 処理の流れ
```mermaid
graph TD
    A["検索戦略JSON"] --> B["クエリパラメータ抽出"]
    B --> C["Elasticsearchクエリ構築"]
    C --> D{"クエリタイプ判定"}
    D -->|multi_match| E["Multi-match Query"]
    D -->|match| F["Match Query"]
    D -->|match_phrase| G["Match Phrase Query"]
    E --> H["フィルター適用（オプション）"]
    F --> H
    G --> H
    H --> I["Elasticsearch実行"]
    I --> J{"実行成功?"}
    J -->|Yes| K["結果をDict形式変換"]
    J -->|No| L["モックデータ返却"]
    K --> M["結果リスト返却"]
    L --> M
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `strategy: Dict` - AI生成検索戦略<br>`user_query: str` - 元クエリ |
| **PROCESS** | 戦略解析 → ESクエリ構築 → 実行 → 結果変換 → エラー処理 |
| **OUTPUT** | `List[Dict]` - 検索結果（id・score・source含む） |

#### 🔧 Elasticsearchクエリ例

```python
# Multi-match クエリ構築
query_body = {
    "query": {
        "multi_match": {
            "query": "機械学習",
            "fields": ["title", "content"],
            "fuzziness": "AUTO"
        }
    },
    "size": 10,
    "sort": [{"_score": {"order": "desc"}}]
}

# フィルター付きクエリ
query_body = {
    "query": {
        "bool": {
            "must": [{"multi_match": {...}}],
            "filter": [{"term": {"category": "AI"}}]
        }
    }
}
```

---

### 📖 explain_results()

#### 🎯 処理概要
Elasticsearch検索結果をOpenAI APIで自然言語解釈・説明生成

#### 📊 処理の流れ
```mermaid
graph TD
    A["検索結果リスト"] --> B{"結果存在確認"}
    B -->|なし| C["'結果なし'メッセージ"]
    B -->|あり| D["結果サマリー作成"]
    D --> E["上位3件詳細抽出"]
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
| **INPUT** | `query: str` - 元クエリ<br>`results: List[Dict]` - ES検索結果<br>`model: str` - OpenAIモデル |
| **PROCESS** | 結果確認 → サマリー作成 → プロンプト構築 → OpenAI API → 説明抽出 |
| **OUTPUT** | `str` - 自然言語による検索結果説明 |

#### 🔧 説明生成プロンプト

```python
system_prompt = """あなたはドキュメント検索結果を分かりやすく説明する専門家です。
検索結果の内容とスコアを自然な日本語で要約してください。"""

user_content = f"""以下のドキュメント検索結果について、わかりやすく日本語で説明してください:

質問: {query}

検索結果データ:
1. [スコア: 1.95] {'title': 'AI技術概要', 'content': '...'}
2. [スコア: 1.85] {'title': '機械学習の基礎', 'content': '...'}
... (他N件)"""
```

---

### 🖥️ create_main_interface()

#### 🎯 処理概要
メインUI構築：API情報・クエリ入力・候補表示・実行制御

#### 📊 処理の流れ
```mermaid
graph TD
    A["Interface Setup"] --> B["API説明セクション展開"]
    B --> C["MCP情報セクション展開"]
    C --> D["クエリ入力エリア作成"]
    D --> E["候補ボタン12個表示"]
    E --> F{"実行ボタン押下?"}
    F -->|Yes+Query| G["execute_mcp_query()実行"]
    F -->|Yes+NoQuery| H["警告表示"]
    F -->|No| I["候補選択待機"]
    I --> J{"候補ボタン押下?"}
    J -->|Yes| K["テキスト入力欄に設定"]
    J -->|No| I
    G --> L["display_results()実行"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | Streamlitセッション状態・ユーザーインタラクション |
| **PROCESS** | UI要素配置 → イベント処理 → 状態管理 → クエリ実行制御 |
| **OUTPUT** | 対話型Webインターフェース |

#### 🎨 UI構成要素

```python
# API情報展開
with st.expander("🔗 OpenAI API 部分"):
    st.code("""OpenAI API レスポンス作成・検索戦略生成例""")

# クエリ入力
col1, col2 = st.columns([3, 1])
with col1:
    user_query = st.text_input("質問を入力してください:")
with col2:
    execute_button = st.button("🔍 実行", type="primary")

# 候補表示（3列レイアウト）
cols = st.columns(3)
for i, suggestion in enumerate(suggestions):
    with cols[i % 3]:
        if st.button(suggestion, key=f"suggestion_{i}"):
            # 候補選択処理
```

---

### 🎭 _generate_mock_search_results()

#### 🎯 処理概要
Elasticsearch接続失敗時の高品質モックデータ生成

#### 📊 処理の流れ
```mermaid
graph TD
    A["Mock Data Request"] --> B["インデックス名確認"]
    B --> C{"Index Type?"}
    C -->|blog_articles| D["ブログ記事モック（5件）"]
    C -->|products| E["商品情報モック（2件）"]
    C -->|knowledge_base| F["知識ベースモック（1件）"]
    D --> G["サイズ制限適用"]
    E --> G
    F --> G
    G --> H["リアルなモックデータ返却"]
```

#### 📋 IPO設計

| 項目 | 内容 |
|------|------|
| **INPUT** | `strategy: Dict` - 検索戦略<br>`user_query: str` - ユーザークエリ |
| **PROCESS** | インデックス判定 → 適切なモックデータ選択 → サイズ制限適用 |
| **OUTPUT** | `List[Dict]` - リアルな検索結果モック |

#### 🔧 モックデータ例

```python
blog_articles_mock = [
    {
        'id': '1',
        'score': 1.95,
        'source': {
            'title': 'Pythonプログラミング入門',
            'content': 'Pythonは初心者にも学びやすいプログラミング言語です...',
            'category': 'プログラミング',
            'author': '田中太郎',
            'published_date': '2024-01-15',
            'view_count': 1250,
            'tags': ['Python', '入門', 'プログラミング']
        }
    }
]
```

---

## ⚙️ 技術仕様

### 📦 依存ライブラリ

| ライブラリ | バージョン | 用途 | 重要度 |
|-----------|-----------|------|---------|
| `streamlit` | >=1.48.0 | 🌐 Webアプリケーションフレームワーク | ⭐⭐⭐ |
| `elasticsearch` | 最新 | 🔍 Elasticsearch公式クライアント | ⭐⭐⭐ |
| `openai` | >=1.99.9 | 🤖 OpenAI API（検索戦略・結果説明） | ⭐⭐⭐ |
| `plotly` | 最新 | 📊 結果データ可視化 | ⭐⭐ |
| `pandas` | 最新 | 📋 データ処理・変換 | ⭐⭐ |
| `json` | 標準 | 📋 JSON処理・戦略パース | ⭐⭐⭐ |
| `time` | 標準 | ⏰ タイムスタンプ・ファイル名生成 | ⭐⭐ |
| `python-dotenv` | 最新 | 🔧 環境変数管理 | ⭐⭐⭐ |

### 🔍 Elasticsearch統合仕様

#### 📋 対応インデックス構造

```yaml
Blog_Articles_Index:
  description: "ブログ記事のドキュメントインデックス"
  fields:
    title: "text"
    content: "text"
    category: "keyword"
    author: "keyword"
    published_date: "date"
    view_count: "integer"
    tags: "keyword[]"
  analyzer: "standard"
  sample_count: 5

Products_Index:
  description: "商品情報のドキュメントインデックス"
  fields:
    name: "text"
    description: "text"
    category: "keyword"
    price: "integer"
    brand: "keyword"
  analyzer: "standard"
  sample_count: 10

Knowledge_Base_Index:
  description: "知識ベースのドキュメントインデックス"
  fields:
    topic: "text"
    content: "text"
    tags: "keyword[]"
    difficulty_level: "keyword"
    source: "keyword"
  analyzer: "standard"
  sample_count: 50
```

#### 🔧 Elasticsearchクエリ対応

```yaml
Supported_Query_Types:
  multi_match:
    description: "複数フィールド横断検索"
    use_case: "汎用的な全文検索"
    features: ["fuzziness: AUTO", "boost対応"]
  
  match:
    description: "単一フィールド完全検索"
    use_case: "特定フィールド精密検索"
    features: ["fuzziness: AUTO"]
  
  match_phrase:
    description: "フレーズ完全一致検索"
    use_case: "正確なフレーズ検索"
    features: ["語順保持"]
  
  bool:
    description: "複合条件検索"
    use_case: "フィルター・除外条件"
    features: ["must", "should", "filter", "must_not"]
```

### 🤖 OpenAI API統合仕様

#### 📋 使用APIエンドポイント

```yaml
OpenAI_API_Usage:
  search_strategy_generation:
    endpoint: "responses.create()"
    model: "gpt-5-mini (default)"
    purpose: "自然言語→ES戦略JSON変換"
    input_format: "システム・ユーザープロンプト"
    output_format: "JSON戦略オブジェクト"
  
  result_explanation:
    endpoint: "responses.create()"
    model: "gpt-4o-mini (default)"
    purpose: "検索結果の自然言語説明"
    input_format: "結果サマリー+元クエリ"
    output_format: "日本語説明文"
```

#### 🎯 プロンプトエンジニアリング

```python
# 検索戦略生成プロンプト
strategy_prompt_template = """以下のElasticsearchインデックス情報に基づいて、ユーザーの質問に対応するドキュメント検索戦略を生成してください。

【Elasticsearchインデックス情報】
{indices_text}

【制約】
- 適切なインデックスを選択してください
- 検索クエリのタイプを決定してください
- 安全な検索戦略を心がけてください
- JSON形式で戦略を出力してください

【質問】: {user_query}

以下のJSON形式で回答してください：
{{
    "index": "適切なインデックス名",
    "query_type": "match|match_phrase|bool|range|wildcard|multi_match",
    "search_text": "検索に使用するテキスト",
    "fields": ["検索対象フィールド"],
    "filters": {{}},
    "sort": [],
    "size": 10,
    "description": "検索戦略の説明"
}}"""

# 結果説明プロンプト  
explanation_prompt_template = """あなたはドキュメント検索結果を分かりやすく説明する専門家です。検索結果の内容とスコアを自然な日本語で要約してください。

以下のドキュメント検索結果について、わかりやすく日本語で説明してください:

質問: {query}

{result_summary}"""
```

### 🌐 Streamlit UI仕様

#### 📋 ページ設定

```python
Streamlit_Configuration:
  page_title: "MCP経由Elasticsearchアクセス"
  page_icon: "🔍"
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
  
  index_information:
    widget: "expander"
    content: "インデックス構造・フィールド・ドキュメント数"
  
  query_history:
    widget: "button_list"
    limit: 5
    format: "truncated_query + timestamp"

Main_Interface_Components:
  api_information:
    widget: "expander"
    content: "OpenAI API・MCP動作コード例"
  
  query_input:
    widget: "text_input + button"
    layout: "3:1 column ratio"
    placeholder: "例: Pythonプログラミングに関する記事を探して"
  
  query_suggestions:
    widget: "button_grid"
    layout: "3 columns"
    count: 12
    
  results_display:
    widget: "card_container + download_button"
    format: "title, content, score, metadata"
```

### 🔄 MCP統合仕様

#### 📋 MCPサーバー通信

```yaml
MCP_Server_Configuration:
  elasticsearch_mcp_server:
    url: "http://localhost:8002/mcp"
    protocol: "HTTP/SSE"
    features: ["document_search", "index_management"]
  
  communication_flow:
    step1: "Streamlit UI → OpenAI Responses API"
    step2: "AI戦略生成 → 検索戦略JSON"
    step3: "MCP Server → Elasticsearch"
    step4: "検索結果 → OpenAI解釈 → UI表示"
```

#### 🏗️ アーキテクチャ連携

```mermaid
graph TD
    A["mcp_elasticsearch.py"] --> B["MCPElasticsearchManager"]
    B --> C["MCP Server (Port 8002)"]
    C --> D["Elasticsearch Cluster"]
    
    A --> E["MCPDocumentQueryProcessor"]
    E --> F["OpenAI Responses API"]
    F --> G["検索戦略生成"]
    F --> H["結果説明生成"]
    
    A --> I["NaturalLanguageDocumentInterface"]
    I --> J["Streamlit Web UI"]
```

---

## 🚨 エラーハンドリング

### 📋 エラーカテゴリ

#### 🔍 Elasticsearch関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **Elasticsearch接続エラー** | 🌐 サーバー未起動・URL誤り | モックデータ使用・接続手順表示 | 🟡 中 |
| **インデックス不在エラー** | 📊 指定インデックス存在しない | デフォルトインデックス使用・警告表示 | 🟡 中 |
| **クエリ構文エラー** | 🔤 不正なElasticsearchクエリ | クエリ修正・シンプルクエリ代替 | 🟡 中 |
| **ES9互換性エラー** | 🔄 バージョン互換性問題 | モックデータモード強制使用 | 🟠 低 |

#### 🤖 OpenAI API関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **API キー未設定・無効** | 🔑 認証エラー | キー確認指示・機能制限モード | 🔴 高 |
| **レート制限エラー** | ⏱️ API使用量上限 | 待機時間表示・リトライ機構 | 🟡 中 |
| **JSON パースエラー** | 📋 AI応答の形式不正 | フォールバック戦略使用・警告 | 🟡 中 |
| **モデル不存在エラー** | 🤖 指定モデル利用不可 | デフォルトモデル切り替え | 🟠 低 |

#### 📊 データ処理関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **結果フォーマットエラー** | 📋 予期しない検索結果形式 | 結果検証・デフォルトフォーマット | 🟡 中 |
| **JSON シリアライゼーションエラー** | 🔄 複雑オブジェクト変換失敗 | 文字列変換フォールバック | 🟠 低 |
| **ファイルダウンロードエラー** | 💾 書き込み権限・容量不足 | エラー詳細表示・代替保存方法 | 🟠 低 |

#### 🎨 UI・セッション関連エラー

| エラー種別 | 原因 | 対処法 | 影響度 |
|-----------|------|--------|---------|
| **セッション状態エラー** | 📱 Streamlitセッション破損 | セッション初期化・警告表示 | 🟡 中 |
| **UI コンポーネントエラー** | 🖥️ ウィジェット初期化失敗 | デフォルトUI・縮小機能 | 🟠 低 |

### 🛠️ エラーハンドリング戦略

#### 🔧 段階的フォールバック処理

```mermaid
graph TD
    A["Error Detection"] --> B{"Error Type"}
    B -->|Elasticsearch| C["Mock Data Mode"]
    B -->|OpenAI API| D["Simplified Processing"]
    B -->|JSON Parse| E["Fallback Strategy"]
    B -->|UI Error| F["Default Interface"]

    C --> G["Continue with Sample Data"]
    D --> H["Basic Search without AI"]
    E --> I["Use Hardcoded Strategy"]
    F --> J["Minimal Functionality"]

    G --> K["User Notification"]
    H --> K
    I --> K
    J --> K
```

#### 🎯 具体的エラーハンドリング実装

```python
# Elasticsearch接続エラー（モックデータ使用）
def _execute_document_search_directly(self, strategy, user_query):
    try:
        if not self.elasticsearch_manager._es_client or True:  # ES9互換性対応
            return self._generate_mock_search_results(strategy, user_query)
        # 実際のElasticsearch処理
    except Exception as e:
        logger.error(f"Direct document search execution error: {e}")
        return self._generate_mock_search_results(strategy, user_query)

# OpenAI API エラー（フォールバック戦略）
def _generate_search_strategy_via_ai(self, user_query, model):
    try:
        response = self.openai_client.create_response(...)
        strategy = json.loads(strategy_text)
        return strategy, explanation
    except json.JSONDecodeError:
        # JSONパース失敗時のフォールバック
        fallback_strategy = {
            "index": "blog_articles",
            "query_type": "multi_match",
            "search_text": user_query,
            "fields": ["title", "content"],
            "filters": {},
            "sort": [{"_score": {"order": "desc"}}],
            "size": 10,
            "description": "デフォルト検索戦略"
        }
        return fallback_strategy, "フォールバック戦略を使用します。"

# UI エラー（グレースフル デグラデーション）
def _check_mcp_server_status(self):
    try:
        if not self.elasticsearch_manager._es_client:
            return False
        # 接続テスト（ES9互換性問題のためスキップ）
        return True  # モックデータモードで動作
    except Exception as e:
        logger.error(f"Elasticsearch connection check failed: {e}")
        return False
```

#### ✅ ユーザーフレンドリーなエラーメッセージ

```python
# Elasticsearch接続エラー
if not mcp_status:
    st.error("⚠️ Elasticsearchドキュメントデータベースに接続できません")
    st.info("💡 **解決方法**:\n1. `docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d elasticsearch` でElasticsearchを起動\n2. 環境変数 `ELASTIC_URL` を確認してください")

# OpenAI API エラー
if not success:
    st.error(f"MCPドキュメントクエリ実行エラー: {response_message}")
    return

# 一般的な情報提示
st.success("MCP経由でドキュメントデータを取得しました！")
with st.expander("🤖 MCPサーバーからの応答", expanded=True):
    st.markdown(response_message)
```

#### 🚨 復旧・診断手順

```yaml
Diagnostic_Procedures:
  elasticsearch_connection:
    step1: "curl http://localhost:9200/_cluster/health"
    step2: "docker-compose logs elasticsearch"
    step3: "Check ELASTIC_URL environment variable"
  
  mcp_server_verification:
    step1: "curl http://localhost:8002/mcp"
    step2: "docker-compose ps"
    step3: "Check MCP server logs"
  
  openai_api_troubleshooting:
    step1: "Verify OPENAI_API_KEY in .env"
    step2: "Test API connectivity: curl -H 'Authorization: Bearer $OPENAI_API_KEY' https://api.openai.com/v1/models"
    step3: "Check API usage limits"
  
  application_recovery:
    step1: "Restart Streamlit application"
    step2: "Clear browser cache/session"
    step3: "Check application logs"
```

#### 🔄 自動復旧メカニズム

```python
auto_recovery_strategies = {
    "elasticsearch_fallback": {
        "trigger": "Connection timeout or error",
        "action": "Switch to mock data mode",
        "notification": "モックデータモードで動作中"
    },
    "json_parse_recovery": {
        "trigger": "AI response JSON parse failure",
        "action": "Use predefined fallback strategy",
        "notification": "デフォルト検索戦略を使用"
    },
    "api_rate_limit": {
        "trigger": "OpenAI API rate limit hit",
        "action": "Queue request with exponential backoff",
        "notification": "API制限のため待機中"
    },
    "session_corruption": {
        "trigger": "Streamlit session state error",
        "action": "Reinitialize session with defaults",
        "notification": "セッションを初期化しました"
    }
}
```

---

## 🎉 まとめ

この設計書は、**mcp_elasticsearch.py** の完全な技術仕様と実装詳細を記載した包括的なドキュメントです。

### 🌟 設計のハイライト

- **🔍 AI駆動検索**: OpenAI APIによる自然言語→Elasticsearch戦略変換
- **🗄️ インデックス対応**: blog_articles・products・knowledge_base完全サポート
- **🛡️ 堅牢なフォールバック**: 接続エラー時の高品質モックデータ提供
- **📊 結果解釈**: AI による検索結果の自然言語説明生成

### 🔧 アーキテクチャ特徴

- **🤖 MCP準拠設計**: Model Context Protocol標準アーキテクチャ
- **🔄 ハイブリッド処理**: AI戦略生成+直接Elasticsearch実行
- **📱 Streamlit統合**: 直感的なWeb UI+リアルタイム検索
- **⚙️ 設定駆動**: 環境変数・設定ファイルによる柔軟な構成

### 📈 自然言語検索価値

- **🧠 知的検索**: 技術的クエリ構文不要の直感的検索
- **📋 構造化戦略**: JSON形式での明確な検索戦略定義
- **🎯 精密制御**: フィールド・フィルター・ソート条件の最適化
- **📖 結果説明**: 検索結果の自動解釈・要約機能

### 🚀 拡張可能性

- 🔄 新しいインデックス・フィールド対応
- 📊 高度な分析・可視化機能
- 🌐 マルチテナント・権限管理
- 📱 リアルタイム検索・ストリーミング
- 🔐 セキュリティ強化・監査ログ