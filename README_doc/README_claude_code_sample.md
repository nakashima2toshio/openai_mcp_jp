# Claude Code 指示手順 - MCP API Client改修

## 📝 現在の状況
- **プロジェクト**: `/Users/nakashima_toshio/PycharmProjects/openai_mcp`
- **改修対象**: `mcp_api_client.py` (コマンドライン → Streamlit)
- **参照アプリ**: `openai_api_mcp_sample.py`
- **使用ヘルパー**: helper_mcp.py, helper_st.py, helper_api.py

## 🚀 Step 1: プロジェクト構造の分析

```bash
# Claude Codeで以下のコマンドを順番に実行

# 1-1. 初期化とプロジェクト概要
/init

# 1-2. プロジェクト構造を確認
how does the overall project structure work?

# 1-3. 参照アプリの分析
how does openai_api_mcp_sample.py work?

# 1-4. ヘルパーモジュールの理解
how do helper_mcp.py helper_mcp_pages.py and helper_st.py work together?
```

## 🔍 Step 2: 現在のmcp_api_client.pyの分析

```bash
# 2-1. 現在の機能を詳細分析
analyze mcp_api_client.py - what are its main functions and how is it structured?

# 2-2. Streamlit化における課題の特定
what challenges will we face converting mcp_api_client.py from a CLI tool to a Streamlit app?
```

## 🏗️ Step 3: Streamlitアプリ設計

```bash
# 3-1. アプリ設計の提案
design a Streamlit app based on mcp_api_client.py functionality, using the same structure as openai_api_mcp_sample.py

# 3-2. 具体的なページ構成を決定
create a page structure plan for the Streamlit app that covers all the demo functions from mcp_api_client.py
```

## ✏️ Step 4: 実際の改修実行

```bash
# 4-1. 新しいStreamlitアプリファイルを作成
create mcp_api_streamlit_app.py as a Streamlit version of mcp_api_client.py, following the structure of openai_api_mcp_sample.py

# 4-2. メインアプリケーションクラスの作成
add a main application class to mcp_api_streamlit_app.py that manages the API client functionality with Streamlit UI

# 4-3. デモページの個別実装
create individual page classes for each demo function from mcp_api_client.py (basic operations, sales analytics, customer analysis, etc.)
```

## 🎨 Step 5: UI/UX の最適化

```bash
# 5-1. インタラクティブな機能の追加
enhance mcp_api_streamlit_app.py with interactive forms for creating customers and orders

# 5-2. データ可視化の追加
add data visualization components using Streamlit's charting capabilities for sales stats and analytics

# 5-3. エラーハンドリングの改善
improve error handling in mcp_api_streamlit_app.py with user-friendly Streamlit error messages
```

## 🧩 Step 6: ヘルパーモジュール統合

```bash
# 6-1. helper_mcpの統合
integrate mcp_api_streamlit_app.py with helper_mcp.py for database management

# 6-2. helper_stの活用
use helper_st.py components for consistent UI elements in mcp_api_streamlit_app.py

# 6-3. helper_apiの連携
ensure mcp_api_streamlit_app.py properly uses helper_api.py for API communication
```

## 🔧 Step 7: 設定とテスト

```bash
# 7-1. 設定ファイルの調整
update any configuration needed for mcp_api_streamlit_app.py to work with the existing project setup

# 7-2. 起動スクリプトの作成
create a launch script or configuration for running mcp_api_streamlit_app.py

# 7-3. 動作テストとデバッグ
test mcp_api_streamlit_app.py and fix any issues with the Streamlit interface
```

## 📋 具体的なコマンド例（コピー&ペースト用）

### 最初の分析段階
```
/init

how does the overall project structure work?

analyze mcp_api_client.py - what are its main functions and how is it structured?

how does openai_api_mcp_sample.py work?
```

### 設計段階
```
design a Streamlit app based on mcp_api_client.py functionality, using the same structure as openai_api_mcp_sample.py. Include all demo functions: basic operations, sales analytics, customer analysis, data creation, pandas integration, error handling, performance tests, and interactive features.

create a detailed page structure plan for the new Streamlit app that mirrors the menu system from mcp_api_client.py
```

### 実装段階
```
create mcp_api_streamlit_app.py as a complete Streamlit version of mcp_api_client.py. Follow the exact structure and patterns from openai_api_mcp_sample.py, using helper_mcp.py for database management and helper_st.py for UI components. Include all 9 demo functions as separate Streamlit pages.

enhance mcp_api_streamlit_app.py with interactive forms, data visualization charts, and user-friendly error handling for all the API client functionality
```

### 統合・テスト段階
```
integrate mcp_api_streamlit_app.py with the existing helper modules (helper_mcp.py, helper_st.py, helper_api.py) and ensure consistent styling and functionality

test mcp_api_streamlit_app.py and create a launch configuration that works with the existing project setup
```

## 🎯 期待される成果物

### 1. `mcp_api_streamlit_app.py`
- MCPAPIClientの全機能をStreamlit化
- openai_api_mcp_sample.pyと同様の構造
- 9つのデモ機能をページ別に実装

### 2. 主要機能ページ
- **基本操作ページ**: 顧客・商品・注文の表示・作成
- **売上分析ページ**: グラフ付きの統計表示
- **顧客分析ページ**: 個別顧客の詳細分析
- **データ作成ページ**: フォームベースの新規作成
- **Pandas分析ページ**: DataFrame表示と操作
- **エラーハンドリングページ**: テスト機能
- **パフォーマンステストページ**: API速度測定
- **インタラクティブページ**: リアルタイム操作

### 3. UI/UX改善
- レスポンシブデザイン
- リアルタイムデータ更新
- エラー表示の改善
- データビジュアライゼーション

## ⚡ 効率的な作業フロー

1. **一括実行**: 分析段階のコマンドを連続実行
2. **段階確認**: 各段階の成果物を確認してから次へ
3. **カスタマイズ**: 必要に応じて追加の指示
4. **テスト**: 作成されたファイルをStreamlitで実行確認

## 🚨 注意点

- **既存ファイルの保持**: mcp_api_client.pyは残しておく
- **import文の調整**: 新しいファイルでのモジュール参照
- **エラーハンドリング**: Streamlit特有のエラー表示対応
- **セッション管理**: Streamlitのstate管理の活用

この手順に従って段階的に進めることで、効率的にCLIツールをStreamlitアプリに改修できます。
