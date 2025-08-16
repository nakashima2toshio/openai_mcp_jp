#!/usr/bin/env python3
"""
PostgreSQLテストデータ投入スクリプト
Usage: python scripts/setup_test_data.py
"""

import os
import sys
import psycopg2
import pandas as pd
from datetime import datetime, timedelta
import random


def get_postgres_connection():
    """PostgreSQL接続の取得"""
    conn_str = os.getenv('PG_CONN_STR', 'postgresql://testuser:testpass@localhost:5432/testdb')
    try:
        conn = psycopg2.connect(conn_str)
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL接続エラー: {e}")
        print(f"接続文字列: {conn_str}")
        print("\n💡 解決方法:")
        print("1. Dockerサービスが起動しているか確認:")
        print("   docker-compose -f docker-compose.mcp-demo.yml ps postgres")
        print("2. サービスを起動:")
        print("   docker-compose -f docker-compose.mcp-demo.yml up -d postgres")
        sys.exit(1)


def create_tables(conn):
    """テーブルの作成"""
    cursor = conn.cursor()

    # customersテーブル
    cursor.execute("""
                   DROP TABLE IF EXISTS orders CASCADE;
                   DROP TABLE IF EXISTS customers CASCADE;
                   DROP TABLE IF EXISTS products CASCADE;

                   CREATE TABLE customers
                   (
                       id         SERIAL PRIMARY KEY,
                       name       VARCHAR(100)        NOT NULL,
                       email      VARCHAR(100) UNIQUE NOT NULL,
                       city       VARCHAR(50)         NOT NULL,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   );
                   """)

    # productsテーブル
    cursor.execute("""
                   CREATE TABLE products
                   (
                       id             SERIAL PRIMARY KEY,
                       name           VARCHAR(100)   NOT NULL,
                       category       VARCHAR(50)    NOT NULL,
                       price          DECIMAL(10, 2) NOT NULL,
                       stock_quantity INTEGER        NOT NULL DEFAULT 0,
                       created_at     TIMESTAMP               DEFAULT CURRENT_TIMESTAMP
                   );
                   """)

    # ordersテーブル
    cursor.execute("""
                   CREATE TABLE orders
                   (
                       id           SERIAL PRIMARY KEY,
                       customer_id  INTEGER REFERENCES customers (id),
                       product_name VARCHAR(100)   NOT NULL,
                       quantity     INTEGER        NOT NULL,
                       price        DECIMAL(10, 2) NOT NULL,
                       order_date   DATE           NOT NULL DEFAULT CURRENT_DATE,
                       created_at   TIMESTAMP               DEFAULT CURRENT_TIMESTAMP
                   );
                   """)

    conn.commit()
    print("✅ テーブルを作成しました")


def insert_customers(conn):
    """顧客データの投入"""
    cursor = conn.cursor()

    customers = [
        ('田中太郎', 'tanaka@example.com', '東京'),
        ('佐藤花子', 'sato@example.com', '大阪'),
        ('鈴木一郎', 'suzuki@example.com', '名古屋'),
        ('高橋美咲', 'takahashi@example.com', '東京'),
        ('渡辺健太', 'watanabe@example.com', '福岡'),
        ('山田由美', 'yamada@example.com', '札幌'),
        ('中村大輔', 'nakamura@example.com', '東京'),
        ('小林さくら', 'kobayashi@example.com', '大阪'),
        ('加藤正雄', 'kato@example.com', '名古屋'),
        ('吉田麻衣', 'yoshida@example.com', '横浜')
    ]

    for name, email, city in customers:
        cursor.execute("""
                       INSERT INTO customers (name, email, city)
                       VALUES (%s, %s, %s)
                       """, (name, email, city))

    conn.commit()
    print(f"✅ 顧客データ {len(customers)} 件を投入しました")


def insert_products(conn):
    """商品データの投入"""
    cursor = conn.cursor()

    products = [
        ('ノートパソコン', 'エレクトロニクス', 89800, 50),
        ('スマートフォン', 'エレクトロニクス', 79800, 100),
        ('ワイヤレスイヤホン', 'エレクトロニクス', 15800, 200),
        ('コーヒーメーカー', 'キッチン家電', 12800, 30),
        ('電子レンジ', 'キッチン家電', 19800, 25),
        ('掃除機', 'キッチン家電', 28800, 40),
        ('Tシャツ', 'ファッション', 2980, 500),
        ('ジーンズ', 'ファッション', 7980, 200),
        ('スニーカー', 'ファッション', 8980, 150),
        ('ランニングシューズ', 'スポーツ', 12800, 80)
    ]

    for name, category, price, stock in products:
        cursor.execute("""
                       INSERT INTO products (name, category, price, stock_quantity)
                       VALUES (%s, %s, %s, %s)
                       """, (name, category, price, stock))

    conn.commit()
    print(f"✅ 商品データ {len(products)} 件を投入しました")


def insert_orders(conn):
    """注文データの投入"""
    cursor = conn.cursor()

    # 顧客IDと商品名のリストを取得
    cursor.execute("SELECT id FROM customers")
    customer_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT name, price FROM products")
    products = cursor.fetchall()
    product_data = {name: price for name, price in products}

    # ランダムな注文データを生成
    orders = []
    start_date = datetime.now() - timedelta(days=90)

    for _ in range(100):  # 100件の注文を生成
        customer_id = random.choice(customer_ids)
        product_name = random.choice(list(product_data.keys()))
        quantity = random.randint(1, 5)
        price = product_data[product_name]
        order_date = start_date + timedelta(days=random.randint(0, 90))

        orders.append((customer_id, product_name, quantity, price, order_date.date()))

    for customer_id, product_name, quantity, price, order_date in orders:
        cursor.execute("""
                       INSERT INTO orders (customer_id, product_name, quantity, price, order_date)
                       VALUES (%s, %s, %s, %s, %s)
                       """, (customer_id, product_name, quantity, price, order_date))

    conn.commit()
    print(f"✅ 注文データ {len(orders)} 件を投入しました")


def main():
    """メイン処理"""
    print("🚀 PostgreSQLテストデータ投入を開始します...")

    # 環境変数の確認
    conn_str = os.getenv('PG_CONN_STR')
    if not conn_str:
        print("⚠️  PG_CONN_STR環境変数が設定されていません")
        print("デフォルト値を使用: postgresql://testuser:testpass@localhost:5432/testdb")

    # データベース接続
    conn = get_postgres_connection()

    try:
        # テーブル作成
        create_tables(conn)

        # データ投入
        insert_customers(conn)
        insert_products(conn)
        insert_orders(conn)

        # 結果確認
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]

        print("\n📊 投入結果:")
        print(f"   - 顧客: {customer_count} 件")
        print(f"   - 商品: {product_count} 件")
        print(f"   - 注文: {order_count} 件")

        print("\n✅ テストデータの投入が完了しました!")
        print("\n💡 データの確認:")
        print("   psql -h localhost -U testuser -d testdb")
        print("   SELECT COUNT(*) FROM customers;")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    main()
