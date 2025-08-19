# MCP API Server 設計資料

## 概要

### プロジェクト概要
MCP (Model Context Protocol) API Serverは、OpenAI Responses APIと統合されたFastAPIベースのRESTful APIサーバーです。PostgreSQLデータベースに保存された顧客・商品・注文データにアクセスするための統合的なAPIエンドポイントを提供し、データ管理と分析機能を実現します。

### 主要機能
- **顧客管理**: 顧客の作成、検索、詳細取得
- **商品管理**: 商品情報の検索とフィルタリング
- **注文管理**: 注文の作成、検索、顧客関連付け
- **売上分析**: 総売上統計、商品別分析、都市別分析
- **ヘルスチェック**: サーバーとデータベース接続状態の監視

### アーキテクチャの特徴
- **RESTful API設計**: 標準的なHTTPメソッドとステータスコード
- **自動API文書生成**: FastAPIによるOpenAPI/Swagger対応
- **Pydantic検証**: 入出力データの型安全性とバリデーション
- **包括的エラーハンドリング**: 適切なHTTPステータスコードと詳細なエラーメッセージ
- **CORS対応**: クロスオリジンリクエストサポート

## 実行・停止方法

### 起動方法
```bash
# 推奨: start_api.shスクリプトを使用（PostgreSQL接続確認込み）
./start_api.sh

# 手動起動
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload

# Python直接実行
python mcp_api_server.py

# uv環境での実行
uv run python mcp_api_server.py
```

### 停止方法
```bash
# Ctrl+C でサーバー停止
# またはプロセス終了
pkill -f "uvicorn mcp_api_server"
```

### 必要な事前準備
```bash
# 1. PostgreSQLサーバー起動
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d postgres

# 2. 環境変数設定 (.env)
PG_CONN_STR=postgresql://testuser:testpass@localhost:5432/testdb

# 3. テストデータ投入
python setup_test_data.py
```

### 動作確認
```bash
# ヘルスチェック
curl http://localhost:8000/health

# API文書アクセス
curl http://localhost:8000/docs
# ブラウザで http://localhost:8000/docs

# 基本動作確認
curl http://localhost:8000/api/customers
```

## エンドポイント設計（IPO）

### 1. ルートエンドポイント
**Endpoint**: `GET /`

**Input**: なし

**Process**: API基本情報を返す

**Output**:
```json
{
  "name": "MCP API Server",
  "version": "1.0.0",
  "description": "Model Context Protocol API Server",
  "docs": "/docs",
  "health": "/health"
}
```

### 2. ヘルスチェック
**Endpoint**: `GET /health`

**Input**: なし

**Process**: 
- データベース接続テスト（SELECT 1実行）
- サーバー状態確認

**Output**:
```json
{
  "status": "healthy|unhealthy",
  "database": "connected|disconnected",
  "timestamp": "2024-01-01T12:00:00"
}
```

### 3. 顧客管理エンドポイント

#### 3.1 顧客一覧取得
**Endpoint**: `GET /api/customers`

**Input (Query Parameters)**:
- `city` (optional): 都市名フィルタ
- `limit` (default: 100): 取得件数上限

**Process**: 
- PostgreSQL customers テーブルから条件に合致するレコードを取得
- 都市フィルタが指定されている場合は WHERE 句で絞り込み
- LIMIT句で件数制限

**Output**:
```json
[
  {
    "id": 1,
    "name": "顧客名",
    "email": "email@example.com",
    "city": "東京",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

#### 3.2 特定顧客取得
**Endpoint**: `GET /api/customers/{customer_id}`

**Input (Path Parameters)**:
- `customer_id`: 顧客ID (integer)

**Process**: 
- 指定されたIDの顧客をデータベースから検索
- 存在しない場合は404エラー

**Output**: 顧客オブジェクト（上記と同じ形式）

#### 3.3 顧客作成
**Endpoint**: `POST /api/customers`

**Input (Request Body)**:
```json
{
  "name": "顧客名",
  "email": "email@example.com",
  "city": "都市名"
}
```

**Process**: 
- Pydanticでリクエストデータ検証
- メールアドレス重複チェック
- PostgreSQLのINSERT実行
- 作成されたレコードをRETURNING句で取得

**Output**: 作成された顧客オブジェクト

### 4. 商品管理エンドポイント

#### 4.1 商品一覧取得
**Endpoint**: `GET /api/products`

**Input (Query Parameters)**:
- `category` (optional): カテゴリフィルタ
- `min_price` (optional): 最低価格
- `max_price` (optional): 最高価格  
- `limit` (default: 100): 取得件数上限

**Process**: 
- products テーブルから条件に応じてSELECT
- 複数フィルタ条件をWHERE句で組み合わせ
- ORDER BY id でソート

**Output**:
```json
[
  {
    "id": 1,
    "name": "商品名",
    "category": "カテゴリ",
    "price": 10000.0,
    "stock_quantity": 100
  }
]
```

#### 4.2 特定商品取得
**Endpoint**: `GET /api/products/{product_id}`

**Input (Path Parameters)**:
- `product_id`: 商品ID (integer)

**Process**: 指定IDの商品を取得、存在しない場合は404

**Output**: 商品オブジェクト

### 5. 注文管理エンドポイント

#### 5.1 注文一覧取得
**Endpoint**: `GET /api/orders`

**Input (Query Parameters)**:
- `customer_id` (optional): 顧客IDフィルタ
- `product_name` (optional): 商品名フィルタ（部分一致）
- `limit` (default: 100): 取得件数上限

**Process**: 
- orders テーブルとcustomers テーブルをJOIN
- 顧客名と合計金額を計算
- 注文日降順、ID降順でソート

**Output**:
```json
[
  {
    "id": 1,
    "customer_id": 1,
    "product_name": "商品名",
    "quantity": 2,
    "price": 5000.0,
    "order_date": "2024-01-01",
    "total_amount": 10000.0,
    "customer_name": "顧客名"
  }
]
```

#### 5.2 注文作成
**Endpoint**: `POST /api/orders`

**Input (Request Body)**:
```json
{
  "customer_id": 1,
  "product_name": "商品名",
  "quantity": 2,
  "price": 5000.0,
  "order_date": "2024-01-01" // optional
}
```

**Process**: 
- 顧客存在確認
- 注文日がnullの場合は今日の日付を使用
- orders テーブルにINSERT
- 顧客名と合計金額を計算して返す

**Output**: 作成された注文オブジェクト

### 6. 統計・分析エンドポイント

#### 6.1 売上統計取得
**Endpoint**: `GET /api/stats/sales`

**Input**: なし

**Process**: 
- 基本統計（総売上、注文数、平均注文額）の計算
- 人気商品ランキング（売上順Top10）
- 都市別売上分析

**Output**:
```json
{
  "total_sales": 1000000.0,
  "total_orders": 500,
  "avg_order_value": 2000.0,
  "top_products": [
    {
      "product_name": "商品名",
      "total_quantity": 100,
      "total_sales": 500000.0,
      "order_count": 50
    }
  ],
  "sales_by_city": [
    {
      "city": "東京",
      "customer_count": 10,
      "total_sales": 300000.0,
      "order_count": 150
    }
  ]
}
```

#### 6.2 顧客別注文統計
**Endpoint**: `GET /api/stats/customers/{customer_id}/orders`

**Input (Path Parameters)**:
- `customer_id`: 顧客ID (integer)

**Process**: 
- 顧客情報取得
- 注文統計計算（総注文数、総購入額、平均注文額、初回・最終注文日）
- 商品別購入履歴分析

**Output**:
```json
{
  "customer": { /* 顧客情報 */ },
  "order_stats": {
    "total_orders": 10,
    "total_spent": 100000.0,
    "avg_order_value": 10000.0,
    "first_order_date": "2024-01-01",
    "last_order_date": "2024-12-31"
  },
  "product_preferences": [
    {
      "product_name": "商品名",
      "total_quantity": 5,
      "total_spent": 50000.0,
      "order_count": 3
    }
  ]
}
```

## 詳細設計

### データベース設計

#### テーブル構成
- **customers**: 顧客情報（id, name, email, city, created_at）
- **orders**: 注文情報（id, customer_id, product_name, quantity, price, order_date）
- **products**: 商品情報（id, name, category, price, stock_quantity, description）

#### リレーション
- orders.customer_id → customers.id (外部キー制約)

### Pydanticモデル設計

#### リクエストモデル
- `CustomerCreate`: 顧客作成用（name, email, city）
- `OrderCreate`: 注文作成用（customer_id, product_name, quantity, price, order_date?）

#### レスポンスモデル  
- `CustomerResponse`: 顧客情報（id, name, email, city, created_at）
- `OrderResponse`: 注文情報（id, customer_id, product_name, quantity, price, order_date, total_amount, customer_name?）
- `ProductResponse`: 商品情報（id, name, category, price, stock_quantity）
- `HealthResponse`: ヘルス状態（status, database, timestamp）

### エラーハンドリング設計

#### HTTPステータスコード
- **200**: 正常レスポンス
- **404**: リソース未発見
- **422**: バリデーションエラー
- **500**: サーバー内部エラー

#### エラーレスポンス形式
```json
{
  "detail": "エラーメッセージ"
}
```

### セキュリティ考慮事項

#### SQLインジェクション対策
- パラメータ化クエリの使用
- psycopg2のプレースホルダー（%s）使用

#### CORS設定
- 開発環境では全オリジン許可
- 本番環境では適切なオリジン制限が必要

#### データ検証
- Pydanticによる入力値検証
- EmailStr型によるメールアドレス形式チェック

### パフォーマンス設計

#### データベース最適化
- 適切なINDEX設定（customers.city, orders.customer_id, orders.order_date等）
- LIMIT句による結果セット制限
- JOINクエリの最適化

#### コネクション管理
- リクエスト毎のコネクション作成・切断
- コネクションプールの導入検討（本番環境）

### 監視・運用設計

#### ログ設計
- リクエスト/レスポンスログ
- エラーログ詳細記録
- パフォーマンスメトリクス

#### ヘルスチェック
- `/health`エンドポイントによる死活監視
- データベース接続状態確認
- レスポンス時間監視

### デプロイメント設計

#### 環境設定
- 環境変数による設定管理
- `.env`ファイルサポート
- デフォルト値設定

#### 起動オプション
- ホスト: 0.0.0.0 (全インターフェース)
- ポート: 8000 (設定可能)
- リロード: 開発環境では有効

#### 依存関係
- Python >= 3.12.2
- FastAPI >= 0.116.1
- psycopg2-binary >= 2.9.10
- pydantic（EmailStr対応）