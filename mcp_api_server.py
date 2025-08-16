# mcp_api_server.py
# MCP API Server - FastAPIベースのRESTful APIサーバー
# README_api.mdとmcp_api_client.pyの内容から推測した実装

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, date
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="MCP API Server",
    description="Model Context Protocol API Server for OpenAI integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# データベース接続設定
PG_CONN_STR = os.getenv('PG_CONN_STR', 'postgresql://testuser:testpass@localhost:5432/testdb')


# Pydanticモデル定義
class CustomerCreate(BaseModel):
    name: str
    email: EmailStr
    city: str


class CustomerResponse(BaseModel):
    id: int
    name: str
    email: str
    city: str
    created_at: datetime


class OrderCreate(BaseModel):
    customer_id: int
    product_name: str
    quantity: int
    price: float
    order_date: Optional[date] = None


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    product_name: str
    quantity: int
    price: float
    order_date: date
    total_amount: float
    customer_name: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    price: float
    stock_quantity: int


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime


# データベース接続関数
def get_db_connection():
    """PostgreSQL接続を取得"""
    try:
        conn = psycopg2.connect(PG_CONN_STR)
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


# ルートエンドポイント
@app.get("/")
async def root():
    """API情報を返す"""
    return {
        "name"       : "MCP API Server",
        "version"    : "1.0.0",
        "description": "Model Context Protocol API Server",
        "docs"       : "/docs",
        "health"     : "/health"
    }


# ヘルスチェックエンドポイント
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """APIサーバーとデータベースの状態をチェック"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()

        return HealthResponse(
            status="healthy",
            database="connected",
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database="disconnected",
            timestamp=datetime.now()
        )


# 顧客関連エンドポイント
@app.get("/api/customers", response_model=List[CustomerResponse])
async def get_customers(city: Optional[str] = None, limit: int = 100):
    """顧客一覧を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        if city:
            cursor.execute(
                "SELECT * FROM customers WHERE city = %s ORDER BY id LIMIT %s",
                (city, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM customers ORDER BY id LIMIT %s",
                (limit,)
            )

        customers = cursor.fetchall()
        conn.close()

        return [CustomerResponse(**customer) for customer in customers]

    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customers")


@app.get("/api/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int):
    """特定の顧客を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        conn.close()

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return CustomerResponse(**customer)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer")


@app.post("/api/customers", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate):
    """新規顧客を作成"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute(
            """
            INSERT INTO customers (name, email, city)
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (customer.name, customer.email, customer.city)
        )

        new_customer = cursor.fetchone()
        conn.commit()
        conn.close()

        return CustomerResponse(**new_customer)

    except psycopg2.IntegrityError as e:
        logger.error(f"Integrity error creating customer: {e}")
        raise HTTPException(status_code=422, detail="Email already exists")
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create customer")


# 商品関連エンドポイント
@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 100
):
    """商品一覧を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = "SELECT * FROM products WHERE 1=1"
        params = []

        if category:
            query += " AND category = %s"
            params.append(category)

        if min_price is not None:
            query += " AND price >= %s"
            params.append(min_price)

        if max_price is not None:
            query += " AND price <= %s"
            params.append(max_price)

        query += " ORDER BY id LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        products = cursor.fetchall()
        conn.close()

        return [ProductResponse(**product) for product in products]

    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch products")


@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int):
    """特定の商品を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        conn.close()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return ProductResponse(**product)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch product")


# 注文関連エンドポイント
@app.get("/api/orders", response_model=List[OrderResponse])
async def get_orders(
        customer_id: Optional[int] = None,
        product_name: Optional[str] = None,
        limit: int = 100
):
    """注文一覧を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        query = """
                SELECT o.*, c.name as customer_name, (o.price * o.quantity) as total_amount
                FROM orders o
                         JOIN customers c ON o.customer_id = c.id
                WHERE 1 = 1 \
                """
        params = []

        if customer_id:
            query += " AND o.customer_id = %s"
            params.append(customer_id)

        if product_name:
            query += " AND o.product_name ILIKE %s"
            params.append(f"%{product_name}%")

        query += " ORDER BY o.order_date DESC, o.id DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        orders = cursor.fetchall()
        conn.close()

        return [OrderResponse(**order) for order in orders]

    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")


@app.post("/api/orders", response_model=OrderResponse)
async def create_order(order: OrderCreate):
    """新規注文を作成"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 顧客存在確認
        cursor.execute("SELECT name FROM customers WHERE id = %s", (order.customer_id,))
        customer = cursor.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # 注文日の設定
        order_date = order.order_date or date.today()

        # 注文作成
        cursor.execute(
            """
            INSERT INTO orders (customer_id, product_name, quantity, price, order_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (order.customer_id, order.product_name, order.quantity, order.price, order_date)
        )

        new_order = cursor.fetchone()
        new_order['customer_name'] = customer['name']
        new_order['total_amount'] = new_order['price'] * new_order['quantity']

        conn.commit()
        conn.close()

        return OrderResponse(**new_order)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create order")


# 統計・分析エンドポイント
@app.get("/api/stats/sales")
async def get_sales_stats():
    """売上統計を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 基本統計
        cursor.execute("""
                       SELECT COALESCE(SUM(price * quantity), 0) as total_sales,
                              COUNT(*)                           as total_orders,
                              COALESCE(AVG(price * quantity), 0) as avg_order_value
                       FROM orders
                       """)
        basic_stats = cursor.fetchone()

        # 人気商品
        cursor.execute("""
                       SELECT product_name,
                              SUM(quantity)         as total_quantity,
                              SUM(price * quantity) as total_sales,
                              COUNT(*)              as order_count
                       FROM orders
                       GROUP BY product_name
                       ORDER BY total_sales DESC
                       LIMIT 10
                       """)
        top_products = cursor.fetchall()

        # 都市別売上
        cursor.execute("""
                       SELECT c.city,
                              COUNT(DISTINCT c.id)                   as customer_count,
                              COALESCE(SUM(o.price * o.quantity), 0) as total_sales,
                              COALESCE(COUNT(o.id), 0)               as order_count
                       FROM customers c
                                LEFT JOIN orders o ON c.id = o.customer_id
                       GROUP BY c.city
                       ORDER BY total_sales DESC
                       """)
        sales_by_city = cursor.fetchall()

        conn.close()

        return {
            "total_sales"    : float(basic_stats['total_sales']),
            "total_orders"   : basic_stats['total_orders'],
            "avg_order_value": float(basic_stats['avg_order_value']),
            "top_products"   : [dict(product) for product in top_products],
            "sales_by_city"  : [dict(city) for city in sales_by_city]
        }

    except Exception as e:
        logger.error(f"Error fetching sales stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sales statistics")


@app.get("/api/stats/customers/{customer_id}/orders")
async def get_customer_order_stats(customer_id: int):
    """特定顧客の注文統計を取得"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # 顧客情報
        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cursor.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # 注文統計
        cursor.execute("""
                       SELECT COUNT(*)                           as total_orders,
                              COALESCE(SUM(price * quantity), 0) as total_spent,
                              COALESCE(AVG(price * quantity), 0) as avg_order_value,
                              MIN(order_date)                    as first_order_date,
                              MAX(order_date)                    as last_order_date
                       FROM orders
                       WHERE customer_id = %s
                       """, (customer_id,))
        order_stats = cursor.fetchone()

        # 商品別購入履歴
        cursor.execute("""
                       SELECT product_name,
                              SUM(quantity)         as total_quantity,
                              SUM(price * quantity) as total_spent,
                              COUNT(*)              as order_count
                       FROM orders
                       WHERE customer_id = %s
                       GROUP BY product_name
                       ORDER BY total_spent DESC
                       """, (customer_id,))
        product_preferences = cursor.fetchall()

        conn.close()

        return {
            "customer"           : dict(customer),
            "order_stats"        : dict(order_stats),
            "product_preferences": [dict(product) for product in product_preferences]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer stats for {customer_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch customer statistics")


# CORSミドルウェア（必要に応じて）
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# エラーハンドラー
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# サーバー起動用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "mcp_api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
