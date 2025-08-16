# MCP PostgreSQL API 使用ガイド

MCPサーバーのPostgreSQLデータベースに外部からアクセスするためのREST APIとサンプルクライアントです。

## 📋 目次

- [クイックスタート](#クイックスタート)
- [API仕様](#api仕様)
- [サンプルコード](#サンプルコード)
- [セットアップ](#セットアップ)
- [使用例](#使用例)
- [トラブルシューティング](#トラブルシューティング)

## 🚀 クイックスタート

### 1. 環境セットアップ
```bash
# 必要なパッケージをインストール
python setup_api.py
```

### 2. PostgreSQLの準備
```bash
# Dockerサービス起動
docker-compose -f docker-compose.mcp-demo.yml up -d postgres

# テストデータ投入
python setup_test_data.py
```

### 3. APIサーバー起動
```bash
# APIサーバーを起動
python mcp_api_server.py

# または uvicornで起動
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 4. クライアント実行
```bash
# 完全なデモを実行
python mcp_api_client.py

# 簡単なテスト
python quick_test.py
```

## 📖 API仕様

### ベースURL
```
http://localhost:8000
```

### 認証
現在は認証なし（開発・学習用）

### エンドポイント一覧

#### 🏥 ヘルスチェック
```http
GET /health
```
APIサーバーとデータベースの状態を確認

#### 👥 顧客管理

```http
# 顧客一覧取得
GET /api/customers?city=東京&limit=100

# 特定顧客取得
GET /api/customers/{customer_id}

# 新規顧客作成
POST /api/customers
Content-Type: application/json

{
  "name": "田中太郎",
  "email": "tanaka@example.com",
  "city": "東京"
}
```

#### 🛍️ 商品管理

```http
# 商品一覧取得
GET /api/products?category=エレクトロニクス&min_price=1000&max_price=50000&limit=100

# 特定商品取得
GET /api/products/{product_id}
```

#### 📦 注文管理

```http
# 注文一覧取得
GET /api/orders?customer_id=1&product_name=ノートパソコン&limit=100

# 新規注文作成
POST /api/orders
Content-Type: application/json

{
  "customer_id": 1,
  "product_name": "ノートパソコン",
  "quantity": 1,
  "price": 89800,
  "order_date": "2024-01-15"
}
```

#### 📊 統計・分析

```http
# 売上統計
GET /api/stats/sales

# 顧客別注文統計
GET /api/stats/customers/{customer_id}/orders
```

## 💻 サンプルコード

### 基本的な使用方法

```python
from mcp_api_client import MCPAPIClient

# クライアント初期化
client = MCPAPIClient("http://localhost:8000")

# 顧客一覧取得
customers = client.get_customers(limit=10)
print(f"顧客数: {len(customers)}")

# 東京の顧客のみ取得
tokyo_customers = client.get_customers(city="東京")

# 新規顧客作成
new_customer = client.create_customer(
    name="API太郎",
    email="api.taro@example.com",
    city="東京"
)

# 売上統計取得
stats = client.get_sales_stats()
print(f"総売上: ¥{stats['total_sales']:,}")
```

### Pandas連携

```python
import pandas as pd
from mcp_api_client import MCPAPIClient

client = MCPAPIClient()

# 顧客データをDataFrameに変換
customers = client.get_customers()
df_customers = pd.DataFrame(customers)

# 都市別顧客数
city_counts = df_customers['city'].value_counts()
print(city_counts)

# 注文データの分析
orders = client.get_orders()
df_orders = pd.DataFrame(orders)

# 日別売上
df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])
daily_sales = df_orders.groupby('order_date')['total_amount'].sum()
```

### エラーハンドリング

```python
import requests
from mcp_api_client import MCPAPIClient

client = MCPAPIClient()

try:
    customer = client.get_customer(99999)  # 存在しないID
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("顧客が見つかりません")
    else:
        print(f"APIエラー: {e}")
```

## 🔧 セットアップ詳細

### 必要なパッケージ

```txt
# APIサーバー用
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
pydantic>=2.0.0

# データベース
psycopg2-binary>=2.9.0

# クライアント用
requests>=2.31.0
pandas>=2.0.0

# 既存パッケージ
streamlit>=1.28.0
openai>=1.3.0
python-dotenv>=1.0.0
```

### 環境変数

```bash
# PostgreSQL接続文字列
export PG_CONN_STR="postgresql://testuser:testpass@localhost:5432/testdb"

# OpenAI API Key（既存のStreamlitアプリ用）
export OPENAI_API_KEY="sk-..."
```

## 🎯 使用例

### 1. 顧客管理システム

```python
# 新規顧客登録
def register_customer(name, email, city):
    client = MCPAPIClient()
    try:
        customer = client.create_customer(name, email, city)
        print(f"顧客登録完了: {customer['name']} (ID: {customer['id']})")
        return customer
    except Exception as e:
        print(f"登録失敗: {e}")
        return None

# 顧客検索
def search_customers_by_city(city):
    client = MCPAPIClient()
    customers = client.get_customers(city=city)
    return customers
```

### 2. 売上レポート生成

```python
def generate_sales_report():
    client = MCPAPIClient()
    stats = client.get_sales_stats()

    report = f"""
    📊 売上レポート
    ================
    総売上: ¥{stats['total_sales']:,}
    注文数: {stats['total_orders']:,}件
    平均注文額: ¥{stats['avg_order_value']:,}

    🏆 人気商品:
    """

    for i, product in enumerate(stats['top_products'][:3], 1):
        report += f"\n{i}. {product['product_name']} - ¥{product['total_sales']:,}"

    return report
```

### 3. 注文処理システム

```python
def process_order(customer_email, product_name, quantity, price):
    client = MCPAPIClient()

    # 顧客を検索
    customers = client.get_customers()
    customer = next((c for c in customers if c['email'] == customer_email), None)

    if not customer:
        return {"error": "顧客が見つかりません"}

    # 注文作成
    try:
        order = client.create_order(
            customer_id=customer['id'],
            product_name=product_name,
            quantity=quantity,
            price=price
        )
        return {"success": True, "order_id": order['id']}
    except Exception as e:
        return {"error": str(e)}
```

## 🔍 API レスポンス例

### 顧客一覧

```json
[
  {
    "id": 1,
    "name": "田中太郎",
    "email": "tanaka@example.com",
    "city": "東京",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### 売上統計

```json
{
  "total_sales": 1500000.0,
  "total_orders": 125,
  "avg_order_value": 12000.0,
  "top_products": [
    {
      "product_name": "ノートパソコン",
      "total_quantity": 15,
      "total_sales": 1347000.0,
      "order_count": 15
    }
  ],
  "sales_by_city": [
    {
      "city": "東京",
      "customer_count": 4,
      "total_sales": 800000.0,
      "order_count": 65
    }
  ]
}
```

## 🛠️ トラブルシューティング

### よくある問題

#### 1. APIサーバーが起動しない

```bash
# ポートが使用中の場合
lsof -i :8000
kill -9 <PID>

# 別のポートで起動
uvicorn mcp_api_server:app --port 8001
```

#### 2. データベース接続エラー

```bash
# PostgreSQLサービスの状態確認
docker-compose -f docker-compose.mcp-demo.yml ps postgres

# サービス再起動
docker-compose -f docker-compose.mcp-demo.yml restart postgres

# ログ確認
docker-compose -f docker-compose.mcp-demo.yml logs postgres
```

#### 3. パッケージ不足エラー

```bash
# 必要なパッケージを個別インストール
pip install fastapi uvicorn psycopg2-binary requests pandas

# または一括インストール
pip install -r requirements.txt
```

### デバッグモード

```bash
# デバッグ情報付きでサーバー起動
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

### ログ確認

```python
import logging

# ログレベルを設定
logging.basicConfig(level=logging.DEBUG)

# APIクライアントでデバッグ情報を表示
client = MCPAPIClient()
# リクエスト詳細がコンソールに出力される
```

## 📚 追加リソース

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [PostgreSQL公式ドキュメント](https://www.postgresql.org/docs/)
- [Requests ライブラリ](https://docs.python-requests.org/)
- [Pandas ドキュメント](https://pandas.pydata.org/docs/)

## 🤝 貢献

バグ報告や機能要望は Issues にお寄せください。

## 📄 ライセンス

MIT License - 学習・開発目的での使用を前提としています。

---

**注意**: この API は学習・開発目的で作成されており、本番環境での使用には適していません。本番環境では適切な認証・認可・バリデーションを実装してください。
