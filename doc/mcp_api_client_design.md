# MCP API Client 設計資料

## 概要

### プロジェクト概要
MCP API Clientは、MCP API ServerにアクセスするためのユーザーフレンドリーなPythonクライアントライブラリです。HTTPリクエストの複雑さを隠蔽し、型安全で使いやすいインターフェースを提供することで、アプリケーション開発者がデータベース操作と分析機能を簡単に利用できるようにします。

### 主要機能
- **HTTP通信の抽象化**: requests セッション管理と共通エラーハンドリング
- **自動ヘルスチェック**: 初期化時のサーバー接続確認
- **包括的API呼び出し**: 全てのサーバーエンドポイントに対応
- **日本語対応**: エラーメッセージとログの日本語表示
- **デモ機能**: 9種類の実践的なデモスクリプト内蔵
- **インタラクティブモード**: 対話型テストとデバッグ機能

### アーキテクチャの特徴
- **シングルトン設計**: 1つのクライアントインスタンスでの効率的な通信
- **セッション管理**: requests.Session による接続再利用
- **タイムアウト制御**: 適切なタイムアウト設定
- **例外処理**: 詳細なエラー情報と解決方法の提示
- **Pandas統合**: データ分析ライブラリとの連携

## 実行・停止方法

### 基本的な実行方法
```bash
# メインデモの実行
python mcp_api_client.py

# 特定機能の実行例
python -c "from mcp_api_client import MCPAPIClient; client = MCPAPIClient(); print(client.get_customers())"
```

### インタラクティブモードの実行
```bash
# Pythonインタープリターから
python
>>> from mcp_api_client import MCPAPIClient
>>> client = MCPAPIClient()
>>> customers = client.get_customers()
>>> print(len(customers))
```

### デモの実行方法
```bash
# 全デモの実行
python mcp_api_client.py
# メニューで「9」を選択

# 特定デモの実行（Python内部から）
>>> from mcp_api_client import demo_basic_operations
>>> demo_basic_operations()
```

### 必要な事前準備
```bash
# 1. MCP API Server の起動確認
curl http://localhost:8000/health

# 2. 依存関係の確認
pip install requests pandas

# 3. 環境設定（必要に応じて）
export MCP_API_BASE_URL="http://localhost:8000"
```

### 停止方法
- インタラクティブデモ: Ctrl+C または メニューで「0」選択
- デモ実行中: Ctrl+C
- インポート使用時: 特別な停止処理は不要

## クライアント設計（IPO）

### 1. 初期化とヘルスチェック

#### MCPAPIClientクラス初期化
**Input**: 
- `base_url` (default: "http://localhost:8000"): API サーバーのベースURL

**Process**:
- requests.Session の初期化
- 自動ヘルスチェック実行
- 接続状態の確認とフィードバック表示
- エラー時の解決方法提示

**Output**: MCPAPIClient インスタンス

### 2. HTTP通信の共通処理

#### _make_request メソッド
**Input**:
- `method`: HTTPメソッド（GET, POST等）
- `endpoint`: APIエンドポイント（/api/customers等）
- `**kwargs`: requests追加パラメータ

**Process**:
- タイムアウト設定（10秒）
- HTTPリクエスト実行
- レスポンス形式の判定（JSON/テキスト）
- 例外処理とユーザーフレンドリーなエラーメッセージ

**Output**: レスポンスデータ（dict形式）

### 3. 顧客管理メソッド

#### get_customers
**Input**:
- `city` (optional): 都市名フィルタ
- `limit` (default: 100): 取得件数上限

**Process**: GET /api/customers へのリクエスト送信

**Output**: 顧客データのリスト

#### get_customer
**Input**: `customer_id` (int): 顧客ID

**Process**: GET /api/customers/{customer_id} へのリクエスト送信

**Output**: 単一顧客データ

#### create_customer
**Input**:
- `name`: 顧客名
- `email`: メールアドレス  
- `city`: 都市名

**Process**: POST /api/customers への顧客作成リクエスト

**Output**: 作成された顧客データ

### 4. 商品管理メソッド

#### get_products
**Input**:
- `category` (optional): カテゴリフィルタ
- `min_price` (optional): 最低価格
- `max_price` (optional): 最高価格
- `limit` (default: 100): 取得件数上限

**Process**: GET /api/products への条件付きリクエスト

**Output**: 商品データのリスト

#### get_product
**Input**: `product_id` (int): 商品ID

**Process**: GET /api/products/{product_id} へのリクエスト

**Output**: 単一商品データ

### 5. 注文管理メソッド

#### get_orders  
**Input**:
- `customer_id` (optional): 顧客IDフィルタ
- `product_name` (optional): 商品名フィルタ
- `limit` (default: 100): 取得件数上限

**Process**: GET /api/orders への条件付きリクエスト

**Output**: 注文データのリスト（顧客情報含む）

#### create_order
**Input**:
- `customer_id`: 顧客ID
- `product_name`: 商品名
- `quantity`: 数量
- `price`: 価格
- `order_date` (optional): 注文日（YYYY-MM-DD形式）

**Process**: POST /api/orders への注文作成リクエスト

**Output**: 作成された注文データ

### 6. 統計・分析メソッド

#### get_sales_stats
**Input**: なし

**Process**: GET /api/stats/sales への統計リクエスト

**Output**: 売上統計データ（総売上、人気商品、都市別売上等）

#### get_customer_order_stats
**Input**: `customer_id` (int): 顧客ID

**Process**: GET /api/stats/customers/{customer_id}/orders への顧客分析リクエスト

**Output**: 顧客別注文統計データ

### 7. ユーティリティメソッド

#### ping
**Input**: なし

**Process**: ヘルスチェックエンドポイントへの接続確認

**Output**: bool（接続成功/失敗）

#### get_api_info
**Input**: なし

**Process**: GET / へのAPI情報リクエスト

**Output**: API基本情報

## デモ機能設計

### 1. demo_basic_operations
- 顧客・商品・注文の基本的なCRUD操作
- フィルタリング機能のテスト
- データ存在確認

### 2. demo_sales_analytics  
- 売上統計の表示
- 人気商品ランキング
- 都市別売上分析

### 3. demo_customer_analysis
- 顧客別購入履歴分析
- 購入パターンの可視化
- 複数顧客の比較分析

### 4. demo_create_data
- 新規顧客・注文作成のテスト
- 一意性制約のテスト
- 作成データの検証

### 5. demo_pandas_integration
- DataFrameへの変換
- 統計分析機能
- データ可視化

### 6. demo_error_handling
- 404エラーのテスト
- バリデーションエラーのテスト  
- 適切なエラーメッセージの確認

### 7. demo_performance_test
- レスポンス時間の測定
- 連続リクエストのテスト
- パフォーマンス統計の表示

### 8. interactive_demo
- メニュー形式の対話型インターフェース
- リアルタイムデータ操作
- ユーザー入力による動的クエリ

## 詳細設計

### エラーハンドリング設計

#### 例外の分類
- **ConnectionError**: サーバー接続失敗
- **Timeout**: リクエストタイムアウト
- **HTTPError**: HTTPステータスエラー（404, 422, 500等）
- **RequestException**: その他リクエストエラー

#### エラーメッセージの日本語化
```python
if e.response.status_code == 404:
    print("   リソースが見つかりません")
elif e.response.status_code == 422:
    print("   リクエストデータが無効です")
elif e.response.status_code == 500:
    print("   サーバー内部エラーです")
```

#### トラブルシューティング情報
各エラーに対する具体的な解決方法を提示：
- APIサーバー起動確認
- ポート確認方法
- ファイアウォール設定

### セッション管理設計

#### requests.Session使用
- 接続の再利用による性能向上
- Cookie自動管理
- デフォルトタイムアウト設定

#### タイムアウト設定
- ヘルスチェック: 5秒
- 通常リクエスト: 10秒
- ユーザビリティと安定性のバランス

### データ型設計

#### 型ヒント活用
```python
def get_customers(self, city: Optional[str] = None, limit: int = 100) -> List[Dict]
```

#### オプショナル引数
- デフォルト値による簡便性
- 柔軟なフィルタリングオプション

### パフォーマンス設計

#### 効率的なデータ取得
- デフォルト制限値（100件）
- 必要に応じたlimit調整
- ページング検討

#### メモリ効率
- 大量データ処理時の配慮
- ストリーミング対応検討

### テスト・デバッグ設計

#### 包括的デモカバレッジ
- 全API機能のテスト
- 正常・異常ケースの両方
- 実用的な使用例の提示

#### ログ設計
- 接続状態の可視化
- エラー詳細の表示
- パフォーマンス情報の記録

### 拡張性設計

#### 新機能追加対応
- 統一されたメソッド命名規則
- 共通パラメータ処理
- エラーハンドリングの継承

#### Pandas統合
- データ分析ワークフローとの連携
- DataFrameへの自動変換オプション
- 可視化ライブラリとの連携

### 運用設計

#### 設定管理
- 環境変数による設定
- デフォルト値の提供
- 設定値の検証

#### 監視・診断
- 自動ヘルスチェック
- 接続状態の継続監視
- レスポンス時間の測定

#### ユーザビリティ
- 直感的なメソッド名
- 詳細なドキュメント文字列
- 実用的なデモとサンプルコード