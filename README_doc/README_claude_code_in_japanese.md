# Claude Code 日本語指示ガイド

## ✅ 日本語指示の可否

**結論**: Claude Codeは日本語での指示も完全に対応しています！

## 🎯 効果的な使い分け

### 🟢 日本語が適している場面

#### 1. **概念説明・要求仕様**
```bash
# 日本語で自然に説明
mcp_api_client.pyをStreamlitアプリに変換したい。openai_api_mcp_sample.pyと同じ構造で、9つのデモ機能をページ別に実装してください。

# 詳細な要求事項
顧客管理機能で、新規作成フォームにバリデーション機能を追加し、エラーメッセージを日本語で表示するようにしてください。
```

#### 2. **設計相談・アドバイス**
```bash
# 設計の相談
このプロジェクトでStreamlitアプリを作る時、パフォーマンスを考慮すべき点は何ですか？

# アーキテクチャの質問
helper_mcp.pyとhelper_st.pyを連携させる最適な方法を教えてください。
```

#### 3. **問題解決・デバッグ**
```bash
# エラーの相談
Streamlitアプリでセッション状態が正しく保持されません。原因と対策を教えてください。

# パフォーマンス改善
データベースクエリが重いので、キャッシュ機能を追加したいです。
```

### 🟡 英語の方が良い場面

#### 1. **技術的なコマンド**
```bash
# ファイル操作
create mcp_api_streamlit_app.py

# 分析コマンド
analyze mcp_api_client.py structure

# Git操作
commit changes with message "Add Streamlit interface"
```

#### 2. **プログラミング専門用語**
```bash
# 英語の方が正確
refactor the error handling to use try-catch blocks

# 日本語だと曖昧になりがち
エラーハンドリングをリファクタリング（どの程度？どの方法？）
```

## 🎨 実際の使用例

### MCPプロジェクト改修での日本語指示例

#### **Step 1: プロジェクト理解**
```bash
# 日本語で自然な質問
このプロジェクトの全体構造を教えてください。特にhelperモジュールの役割が知りたいです。

# 具体的なファイル分析
mcp_api_client.pyの機能を詳しく分析して、Streamlit化する際の課題を教えてください。
```

#### **Step 2: 設計相談**
```bash
# 日本語で要求を詳しく説明
mcp_api_client.pyの9つのデモ機能を、Streamlitの複数ページアプリとして実装したいです。openai_api_mcp_sample.pyと同じような構造で、以下の点を考慮してください：

1. 各デモ機能を独立したページにする
2. helper_mcp.pyを使ってデータベース管理
3. helper_st.pyでUI部品を統一
4. エラーハンドリングを改善
5. 日本語UIにする

具体的な設計案を提案してください。
```

#### **Step 3: 実装指示**
```bash
# 日本語 + 英語のハイブリッド
以下の仕様でmcp_api_streamlit_app.pyを作成してください：

create mcp_api_streamlit_app.py with the following features:
- 基本操作ページ（顧客・商品・注文の表示と作成）
- 売上分析ページ（グラフ付き統計表示）
- 顧客分析ページ（個別顧客の詳細分析）
- インタラクティブページ（リアルタイム操作）

openai_api_mcp_sample.pyの構造を参考にして、helper_st.pyのUIコンポーネントを活用してください。
```

#### **Step 4: 細かい調整**
```bash
# 日本語で詳細指示
売上分析ページに以下の機能を追加してください：
- 月別売上推移のグラフ
- 商品カテゴリ別の円グラフ
- 都市別売上の棒グラフ
- フィルタ機能（期間、都市、商品カテゴリ）

既存のhelper機能を使って、Streamlitのst.plotly_chartでインタラクティブなグラフにしてください。
```

## 💡 おすすめの指示パターン

### **パターン1: 日本語メイン**
```bash
# 要求仕様を日本語で詳しく説明
mcp_api_client.pyのインタラクティブデモ機能をStreamlitで再現したいです。ユーザーが以下のことをWeb UIでできるようにしてください：

1. 顧客検索（都市名でフィルタ）
2. 商品検索（カテゴリ・価格帯でフィルタ）
3. 新規顧客登録（フォーム入力）
4. 新規注文作成（顧客選択 + 商品選択）
5. 売上統計の表示（グラフ付き）

技術的には create interactive_demo_page.py を実行してください。
```

### **パターン2: ハイブリッド**
```bash
# 日本語で概要 + 英語で技術仕様
顧客管理機能を改善したいです。以下の技術仕様で実装してください：

enhance customer management in mcp_api_streamlit_app.py:
- Add form validation using Pydantic models
- Implement real-time search with st.text_input
- Add customer edit functionality
- Show customer order history with expandable cards
- Use helper_st.py UIHelper components for consistent styling

日本語のエラーメッセージとツールチップも追加してください。
```

### **パターン3: 段階的指示**
```bash
# 最初は日本語で大まかに
まず、mcp_api_client.pyの基本操作デモをStreamlitページとして作成してください。

# 次に英語で具体的に
create basic_operations_page.py with:
- Customer list display with filtering
- Product catalog with category tabs
- Order history with pagination
- Create new customer form
- Create new order form

# 最後に日本語で調整
UIを日本語化して、エラーハンドリングを改善してください。
```

## 🚀 実践での使い方

### **今すぐ試せる日本語指示**

```bash
# 1. プロジェクト理解（日本語）
このMCPプロジェクトの構造と、各ファイルの役割を教えてください

# 2. 具体的な分析（日本語）
mcp_api_client.pyをStreamlitアプリに変換する場合の設計方針を提案してください

# 3. 実装指示（ハイブリッド）
以下の仕様でStreamlitアプリを作成：
create mcp_streamlit_dashboard.py based on mcp_api_client.py demos

# 4. 詳細調整（日本語）
作成したアプリにデータ可視化機能を追加して、日本語UIに対応してください
```

## ⚡ Tips

### **日本語指示のコツ**
1. **具体的に書く**: 「改善して」→「バリデーション機能を追加して」
2. **例を示す**: 「こんな機能」→「顧客検索で都市名フィルタのような」
3. **技術用語は英語併記**: 「キャッシュ(cache)機能」

### **英語と併用するメリット**
- **日本語**: 要求の詳細説明、ビジネスロジック
- **英語**: ファイル名、関数名、技術仕様

## 🎯 まとめ

- **日本語完全対応**: Claude Codeは日本語指示を正確に理解
- **使い分けが効果的**: 要求仕様は日本語、技術コマンドは英語
- **ハイブリッド推奨**: 日本語で説明 + 英語で実装指示

**今すぐ試してみてください！**
```bash
mcp_api_client.pyの機能をすべてStreamlitアプリに移植したいです。詳細な実装計画を立ててください。
```
