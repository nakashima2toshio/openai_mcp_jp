#!/usr/bin/env python3
"""
MCPデータ投入スクリプト
Usage: python data.py [--postgres] [--redis] [--elasticsearch] [--qdrant] [--all]
"""

import os
import sys
import argparse
import psycopg2
import redis
import requests
import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def setup_redis_data():
    """Redisサンプルデータの投入"""
    print("🔴 Redisデータセットアップ中...")
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        
        # 接続テスト
        r.ping()
        print("  🔌 Redis接続確認完了")
        
        # 既存データをクリア
        r.flushdb()
        print("  🧹 既存データをクリア")
        
        # セッションデータ
        print("  👤 セッションデータ投入中...")
        sessions = {
            "session:user1": json.dumps({
                "user_id": 1,
                "username": "田中太郎",
                "last_login": "2024-01-15T10:30:00Z",
                "preferences": {"theme": "dark", "lang": "ja"}
            }),
            "session:user2": json.dumps({
                "user_id": 2,
                "username": "佐藤花子",
                "last_login": "2024-01-16T09:15:00Z",
                "preferences": {"theme": "light", "lang": "ja"}
            })
        }
        
        for key, value in sessions.items():
            r.setex(key, 3600, value)  # 1時間のTTL
        
        # キャッシュデータ
        print("  🗄️ キャッシュデータ投入中...")
        cache_data = {
            "cache:products:popular": json.dumps([
                {"id": 1, "name": "ノートパソコン", "sales_count": 150},
                {"id": 2, "name": "スマートフォン", "sales_count": 200},
                {"id": 3, "name": "ワイヤレスイヤホン", "sales_count": 300}
            ]),
            "cache:stats:daily": json.dumps({
                "total_orders": 45,
                "total_revenue": 125000,
                "active_users": 23,
                "date": "2024-01-16"
            })
        }
        
        for key, value in cache_data.items():
            r.setex(key, 1800, value)  # 30分のTTL
        
        # リアルタイムデータ（リスト）
        print("  📊 リアルタイムデータ投入中...")
        recent_orders = [
            json.dumps({"order_id": 101, "customer": "田中太郎", "amount": 15800, "time": "10:30"}),
            json.dumps({"order_id": 102, "customer": "佐藤花子", "amount": 8900, "time": "10:45"}),
            json.dumps({"order_id": 103, "customer": "鈴木一郎", "amount": 12500, "time": "11:00"})
        ]
        
        for order in recent_orders:
            r.lpush("orders:recent", order)
        r.ltrim("orders:recent", 0, 99)  # 最新100件のみ保持
        
        # カウンタ
        print("  🔢 カウンタデータ投入中...")
        counters = {
            "counter:page_views": 1250,
            "counter:api_calls": 890,
            "counter:user_registrations": 156
        }
        
        for key, value in counters.items():
            r.set(key, value)
        
        # 結果確認
        total_keys = r.dbsize()
        print(f"  ✅ Redis: {total_keys}個のキーを投入")
        return True
        
    except Exception as e:
        print(f"  ❌ Redis エラー: {e}")
        return False


def setup_postgresql_data():
    """PostgreSQLテストデータの投入"""
    print("🐘 PostgreSQLデータセットアップ中...")
    
    conn_str = os.getenv('PG_CONN_STR', 'postgresql://testuser:testpass@localhost:5432/testdb')
    
    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()
        
        # テーブル作成
        print("  📋 テーブル作成中...")
        cursor.execute("""
        DROP TABLE IF EXISTS orders CASCADE;
        DROP TABLE IF EXISTS customers CASCADE;
        DROP TABLE IF EXISTS products CASCADE;
        
        CREATE TABLE customers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            age INTEGER,
            city VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE orders (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            product_name VARCHAR(100) NOT NULL,
            quantity INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            order_date DATE NOT NULL DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # 顧客データ投入
        print("  👥 顧客データ投入中...")
        customers = [
            ('田中太郎', 'tanaka@example.com', 32, '東京'),
            ('佐藤花子', 'sato@example.com', 28, '大阪'),
            ('鈴木一郎', 'suzuki@example.com', 45, '名古屋'),
            ('高橋美咲', 'takahashi@example.com', 24, '東京'),
            ('渡辺健太', 'watanabe@example.com', 38, '福岡'),
            ('山田由美', 'yamada@example.com', 31, '札幌'),
            ('中村大輔', 'nakamura@example.com', 41, '東京'),
            ('小林さくら', 'kobayashi@example.com', 27, '大阪'),
            ('加藤正雄', 'kato@example.com', 52, '名古屋'),
            ('吉田麻衣', 'yoshida@example.com', 29, '横浜')
        ]
        
        for name, email, age, city in customers:
            cursor.execute("""
            INSERT INTO customers (name, email, age, city) 
            VALUES (%s, %s, %s, %s)
            """, (name, email, age, city))
        
        # 商品データ投入
        print("  🛍️ 商品データ投入中...")
        products = [
            ('ノートパソコン', 'エレクトロニクス', 89800, 50, '高性能なビジネス向けノートパソコン'),
            ('スマートフォン', 'エレクトロニクス', 79800, 100, '最新のAndroidスマートフォン'),
            ('ワイヤレスイヤホン', 'エレクトロニクス', 15800, 200, 'ノイズキャンセリング機能付き'),
            ('コーヒーメーカー', 'キッチン家電', 12800, 30, '自動ドリップ式コーヒーメーカー'),
            ('電子レンジ', 'キッチン家電', 19800, 25, '多機能電子レンジ'),
            ('掃除機', 'キッチン家電', 28800, 40, 'サイクロン式掃除機'),
            ('Tシャツ', 'ファッション', 2980, 500, 'コットン100%のTシャツ'),
            ('ジーンズ', 'ファッション', 7980, 200, 'ストレッチ素材のジーンズ'),
            ('スニーカー', 'ファッション', 8980, 150, 'カジュアルスニーカー'),
            ('ランニングシューズ', 'スポーツ', 12800, 80, '軽量ランニングシューズ')
        ]
        
        for name, category, price, stock, description in products:
            cursor.execute("""
            INSERT INTO products (name, category, price, stock_quantity, description) 
            VALUES (%s, %s, %s, %s, %s)
            """, (name, category, price, stock, description))
        
        # 注文データ投入
        print("  📦 注文データ投入中...")
        cursor.execute("SELECT id FROM customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT name, price FROM products")
        products_data = cursor.fetchall()
        
        orders = []
        start_date = datetime.now() - timedelta(days=90)
        
        for _ in range(100):
            customer_id = random.choice(customer_ids)
            product_name, price = random.choice(products_data)
            quantity = random.randint(1, 5)
            order_date = start_date + timedelta(days=random.randint(0, 90))
            orders.append((customer_id, product_name, quantity, price, order_date.date()))
        
        for order in orders:
            cursor.execute("""
            INSERT INTO orders (customer_id, product_name, quantity, price, order_date) 
            VALUES (%s, %s, %s, %s, %s)
            """, order)
        
        conn.commit()
        
        # 結果確認
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products") 
        product_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]
        
        print(f"  ✅ PostgreSQL: 顧客{customer_count}件、商品{product_count}件、注文{order_count}件")
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ❌ PostgreSQL エラー: {e}")
        return False


def setup_elasticsearch_data():
    """Elasticsearchサンプルデータの投入"""
    print("🔍 Elasticsearchデータセットアップ中...")
    
    es_url = os.getenv('ELASTIC_URL', 'http://localhost:9200')
    
    try:
        # インデックス作成
        index_config = {
            "mappings": {
                "properties": {
                    "title": {"type": "text", "analyzer": "standard"},
                    "content": {"type": "text", "analyzer": "standard"}, 
                    "category": {"type": "keyword"},
                    "author": {"type": "keyword"},
                    "published_date": {"type": "date"},
                    "view_count": {"type": "integer"},
                    "tags": {"type": "keyword"}
                }
            }
        }
        
        response = requests.put(f"{es_url}/blog_articles", json=index_config)
        print(f"  📋 インデックス作成: {response.status_code}")
        
        # サンプル記事データ
        articles = [
            {
                "title": "Pythonプログラミング入門",
                "content": "Pythonは初心者にも学びやすいプログラミング言語です。文法がシンプルで、豊富なライブラリが特徴です。",
                "category": "プログラミング",
                "author": "田中太郎", 
                "published_date": "2024-01-15",
                "view_count": 1250,
                "tags": ["Python", "入門", "プログラミング"]
            },
            {
                "title": "機械学習の基礎",
                "content": "機械学習は人工知能の一分野で、データからパターンを学習してモデルを構築する技術です。",
                "category": "AI・機械学習",
                "author": "佐藤花子",
                "published_date": "2024-01-20", 
                "view_count": 890,
                "tags": ["機械学習", "AI", "データサイエンス"]
            },
            {
                "title": "Docker入門ガイド",
                "content": "Dockerはコンテナ技術を使ってアプリケーションを効率的にデプロイできるツールです。",
                "category": "インフラ",
                "author": "山田次郎",
                "published_date": "2024-01-25",
                "view_count": 650, 
                "tags": ["Docker", "コンテナ", "DevOps"]
            },
            {
                "title": "Streamlitでダッシュボード作成",
                "content": "Streamlitを使うと簡単にWebアプリケーションやダッシュボードを作成できます。",
                "category": "プログラミング",
                "author": "鈴木三郎",
                "published_date": "2024-02-01",
                "view_count": 430,
                "tags": ["Streamlit", "Python", "ダッシュボード"]
            },
            {
                "title": "ElasticsearchとKibanaで分析", 
                "content": "ElasticsearchとKibanaを組み合わせることで強力なデータ分析環境を構築できます。",
                "category": "データ分析",
                "author": "高橋四郎",
                "published_date": "2024-02-05",
                "view_count": 720,
                "tags": ["Elasticsearch", "Kibana", "データ分析"]
            }
        ]
        
        # データ投入
        for i, article in enumerate(articles, 1):
            response = requests.post(f"{es_url}/blog_articles/_doc/{i}", json=article)
            print(f"  📄 記事{i}: {response.status_code}")
        
        # インデックスリフレッシュ
        requests.post(f"{es_url}/blog_articles/_refresh")
        print(f"  ✅ Elasticsearch: {len(articles)}件の記事を投入")
        return True
        
    except Exception as e:
        print(f"  ❌ Elasticsearch エラー: {e}")
        return False


def setup_qdrant_data():
    """Qdrantベクトルデータの投入"""
    print("🎯 Qdrantデータセットアップ中...")
    
    qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    
    try:
        # コレクション作成
        collection_config = {
            "vectors": {
                "size": 384,
                "distance": "Cosine"
            }
        }
        
        response = requests.put(f"{qdrant_url}/collections/product_embeddings", json=collection_config)
        print(f"  📋 コレクション作成: {response.status_code}")
        
        # サンプル商品データ
        products = [
            {
                "id": 1,
                "payload": {
                    "name": "ワイヤレスヘッドホン",
                    "description": "高音質のBluetoothワイヤレスヘッドホン。ノイズキャンセリング機能付き。",
                    "category": "エレクトロニクス", 
                    "price": 15800,
                    "brand": "TechSound"
                },
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            },
            {
                "id": 2,
                "payload": {
                    "name": "コーヒーメーカー",
                    "description": "自動ドリップ式コーヒーメーカー。タイマー機能付きで朝の準備が楽に。",
                    "category": "キッチン家電",
                    "price": 8900,
                    "brand": "BrewMaster"
                },
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            },
            {
                "id": 3,
                "payload": {
                    "name": "ランニングシューズ", 
                    "description": "軽量で通気性の良いランニングシューズ。長距離走に最適。",
                    "category": "スポーツ",
                    "price": 12500,
                    "brand": "RunFast"
                },
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            },
            {
                "id": 4,
                "payload": {
                    "name": "ビジネスバッグ",
                    "description": "耐久性の高いナイロン製ビジネスバッグ。PC収納スペース付き。",
                    "category": "ファッション",
                    "price": 6800,
                    "brand": "ProBag"
                },
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            },
            {
                "id": 5,
                "payload": {
                    "name": "スマートウォッチ",
                    "description": "健康管理機能付きスマートウォッチ。心拍数や歩数を測定。",
                    "category": "エレクトロニクス",
                    "price": 22000,
                    "brand": "HealthTech"
                },
                "vector": [random.uniform(-1, 1) for _ in range(384)]
            }
        ]
        
        # データ投入
        points_data = {"points": products}
        response = requests.put(f"{qdrant_url}/collections/product_embeddings/points", json=points_data)
        print(f"  🎯 ベクトルデータ投入: {response.status_code}")
        print(f"  ✅ Qdrant: {len(products)}件のベクトルデータを投入")
        return True
        
    except Exception as e:
        print(f"  ❌ Qdrant エラー: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="MCPデータ投入")
    parser.add_argument("--postgres", action="store_true", help="PostgreSQLデータのみ投入")
    parser.add_argument("--redis", action="store_true", help="Redisデータのみ投入")
    parser.add_argument("--elasticsearch", action="store_true", help="Elasticsearchデータのみ投入")
    parser.add_argument("--qdrant", action="store_true", help="Qdrantデータのみ投入")
    parser.add_argument("--all", action="store_true", help="全てのデータを投入")
    args = parser.parse_args()
    
    # 引数がない場合は全てのデータを投入
    if not any([args.postgres, args.redis, args.elasticsearch, args.qdrant, args.all]):
        args.all = True
    
    print("🚀 MCPデータ投入を開始します")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    if args.postgres or args.all:
        total_count += 1
        if setup_postgresql_data():
            success_count += 1
    
    if args.redis or args.all:
        total_count += 1
        if setup_redis_data():
            success_count += 1
    
    if args.elasticsearch or args.all:
        total_count += 1
        if setup_elasticsearch_data():
            success_count += 1
    
    if args.qdrant or args.all:
        total_count += 1
        if setup_qdrant_data():
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 結果: {success_count}/{total_count} のデータベースにデータを投入完了")
    
    if success_count == total_count:
        print("🎉 全てのデータ投入が成功しました!")
        print("\n次のステップ:")
        print("1. サーバー起動: python server.py")
        print("2. アプリ起動: streamlit run mcp_db_show_data.py")
    else:
        print("⚠️ 一部のデータ投入に失敗しました")
        print("Dockerサービスが起動しているか確認してください:")
        print("docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d")


if __name__ == "__main__":
    main()