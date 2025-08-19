# python mcp_api_client.py
# MCP API サーバーにアクセスするクライアントサンプル

import requests
import json
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import time
import sys
import traceback


class MCPAPIClient:
    """MCP APIクライアント"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        print(f"🔗 APIクライアントを初期化中... ({self.base_url})")

        # ヘルスチェック
        if not self.check_health():
            print(f"⚠️ APIサーバー ({self.base_url}) に接続できません")
            print("💡 解決方法:")
            print("1. APIサーバーが起動しているか確認: python mcp_api_server.py")
            print("2. ポートが正しいか確認: netstat -an | grep 8000")
            print("3. ファイアウォールの設定を確認")
        else:
            print(f"✅ APIサーバーへの接続を確認しました")

    def check_health(self) -> bool:
        """APIサーバーのヘルスチェック"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"   🏥 ヘルス状態: {health_data.get('status', 'unknown')}")
                print(f"   🐘 データベース: {health_data.get('database', 'unknown')}")
                return True
            else:
                print(f"   ❌ ヘルスチェック失敗: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ 接続エラー: {e}")
            return False

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """共通のHTTPリクエスト処理"""
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()

            # JSON レスポンスの場合
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json()
            else:
                return {"text": response.text, "status_code": response.status_code}

        except requests.exceptions.Timeout:
            print(f"⏰ タイムアウトエラー: {method} {url}")
            raise
        except requests.exceptions.ConnectionError:
            print(f"🔌 接続エラー: {method} {url}")
            print("💡 APIサーバーが起動しているか確認してください")
            raise
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTPエラー: {method} {url} - {e}")
            if e.response.status_code == 404:
                print("   リソースが見つかりません")
            elif e.response.status_code == 422:
                print("   リクエストデータが無効です")
                try:
                    error_detail = e.response.json()
                    print(f"   詳細: {error_detail}")
                except:
                    pass
            elif e.response.status_code == 500:
                print("   サーバー内部エラーです")
            raise
        except requests.exceptions.RequestException as e:
            print(f"❌ リクエストエラー: {method} {url} - {e}")
            raise

    # =====================================
    # 顧客関連メソッド
    # =====================================

    def get_customers(self, city: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """顧客一覧を取得
        Args:
            city: 都市名でフィルタ（オプション）
            limit: 取得件数上限（デフォルト: 100）
        Returns:
            顧客データのリスト
        """
        params = {"limit": limit}
        if city:
            params["city"] = city

        return self._make_request("GET", "/api/customers", params=params)

    def get_customer(self, customer_id: int) -> Dict:
        """特定の顧客を取得
        Args:
            customer_id: 顧客ID
        Returns:
            顧客データ
        """
        return self._make_request("GET", f"/api/customers/{customer_id}")

    def create_customer(self, name: str, email: str, city: str) -> Dict:
        """新規顧客を作成
        Args:
            name: 顧客名
            email: メールアドレス
            city: 都市名
        Returns:
            作成された顧客データ
        """
        data = {
            "name" : name,
            "email": email,
            "city" : city
        }
        return self._make_request("POST", "/api/customers", json=data)

    # =====================================
    # 商品関連メソッド
    # =====================================

    def get_products(self, category: Optional[str] = None,
                     min_price: Optional[float] = None,
                     max_price: Optional[float] = None,
                     limit: int = 100) -> List[Dict]:
        """商品一覧を取得
        Args:
            category: カテゴリでフィルタ（オプション）
            min_price: 最低価格（オプション）
            max_price: 最高価格（オプション）
            limit: 取得件数上限（デフォルト: 100）
        Returns:
            商品データのリスト
        """
        params = {"limit": limit}
        if category:
            params["category"] = category
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        return self._make_request("GET", "/api/products", params=params)

    def get_product(self, product_id: int) -> Dict:
        """特定の商品を取得
        Args:
            product_id: 商品ID
        Returns:
            商品データ
        """
        return self._make_request("GET", f"/api/products/{product_id}")

    # =====================================
    # 注文関連メソッド
    # =====================================

    def get_orders(self, customer_id: Optional[int] = None,
                   product_name: Optional[str] = None,
                   limit: int = 100) -> List[Dict]:
        """注文一覧を取得
        Args:
            customer_id: 顧客IDでフィルタ（オプション）
            product_name: 商品名でフィルタ（オプション）
            limit: 取得件数上限（デフォルト: 100）
        Returns:
            注文データのリスト（顧客情報含む）
        """
        params = {"limit": limit}
        if customer_id:
            params["customer_id"] = customer_id
        if product_name:
            params["product_name"] = product_name

        return self._make_request("GET", "/api/orders", params=params)

    def create_order(self, customer_id: int, product_name: str,
                     quantity: int, price: float,
                     order_date: Optional[str] = None) -> Dict:
        """新規注文を作成
        Args:
            customer_id: 顧客ID
            product_name: 商品名
            quantity: 数量
            price: 価格
            order_date: 注文日（YYYY-MM-DD形式、オプション）
        Returns:
            作成された注文データ
        """
        data = {
            "customer_id" : customer_id,
            "product_name": product_name,
            "quantity"    : quantity,
            "price"       : price
        }
        if order_date:
            data["order_date"] = order_date

        return self._make_request("POST", "/api/orders", json=data)

    # =====================================
    # 統計・分析メソッド
    # =====================================

    def get_sales_stats(self) -> Dict:
        """売上統計を取得

        Returns:
            売上統計データ（総売上、注文数、人気商品、都市別売上など）
        """
        return self._make_request("GET", "/api/stats/sales")

    def get_customer_order_stats(self, customer_id: int) -> Dict:
        """特定顧客の注文統計を取得

        Args:
            customer_id: 顧客ID

        Returns:
            顧客の注文統計データ
        """
        return self._make_request("GET", f"/api/stats/customers/{customer_id}/orders")

    # =====================================
    # ユーティリティメソッド
    # =====================================

    def get_api_info(self) -> Dict:
        """API情報を取得"""
        return self._make_request("GET", "/")

    def ping(self) -> bool:
        """サーバーの生存確認"""
        try:
            self.check_health()
            return True
        except:
            return False


# =====================================
# デモ関数群
# =====================================

def demo_basic_operations():
    """基本操作のデモ"""
    print("=" * 60)
    print("🔍 基本操作デモ")
    print("=" * 60)

    try:
        client = MCPAPIClient()

        # 1. 顧客一覧取得
        print("\n📋 1. 顧客一覧を取得")
        customers = client.get_customers(limit=5)
        print(f"   取得件数: {len(customers)}")

        if customers:
            print("   顧客サンプル:")
            for i, customer in enumerate(customers[:3], 1):
                print(f"   {i}. {customer['name']} ({customer['city']}) - {customer['email']}")
        else:
            print("   ⚠️ 顧客データがありません")

        # 2. 東京の顧客のみ取得
        print("\n🗼 2. 東京の顧客のみ取得")
        tokyo_customers = client.get_customers(city="東京")
        print(f"   東京の顧客数: {len(tokyo_customers)}")

        if tokyo_customers:
            for customer in tokyo_customers[:2]:
                print(f"   - {customer['name']} ({customer['email']})")

        # 3. 商品一覧取得
        print("\n🛍️ 3. 商品一覧を取得")
        products = client.get_products(limit=5)
        print(f"   取得件数: {len(products)}")

        if products:
            print("   商品サンプル:")
            for i, product in enumerate(products[:3], 1):
                print(f"   {i}. {product['name']} ({product['category']}) - ¥{product['price']:,}")
        else:
            print("   ⚠️ 商品データがありません")

        # 4. エレクトロニクス商品のみ取得
        print("\n💻 4. エレクトロニクス商品のみ取得")
        electronics = client.get_products(category="エレクトロニクス")
        print(f"   エレクトロニクス商品数: {len(electronics)}")

        if electronics:
            for product in electronics[:2]:
                print(f"   - {product['name']}: ¥{product['price']:,} (在庫: {product['stock_quantity']})")

        # 5. 価格帯フィルタ
        print("\n💰 5. 10,000円以下の商品")
        affordable_products = client.get_products(max_price=10000)
        print(f"   10,000円以下の商品数: {len(affordable_products)}")

        if affordable_products:
            for product in affordable_products[:3]:
                print(f"   - {product['name']}: ¥{product['price']:,}")

        # 6. 注文一覧取得
        print("\n📦 6. 最新の注文を取得")
        orders = client.get_orders(limit=5)
        print(f"   注文件数: {len(orders)}")

        if orders:
            print("   注文サンプル:")
            for i, order in enumerate(orders[:3], 1):
                print(f"   {i}. {order['customer_name']}: {order['product_name']} "
                      f"x{order['quantity']} = ¥{order['total_amount']:,}")
        else:
            print("   ⚠️ 注文データがありません")

    except Exception as e:
        print(f"❌ 基本操作デモでエラーが発生: {e}")
        traceback.print_exc()


def demo_sales_analytics():
    """売上分析のデモ"""
    print("\n" + "=" * 60)
    print("📈 売上分析デモ")
    print("=" * 60)

    try:
        client = MCPAPIClient()

        # 売上統計取得
        stats = client.get_sales_stats()

        print(f"\n💰 売上概要:")
        print(f"   総売上: ¥{stats['total_sales']:,.0f}")
        print(f"   総注文数: {stats['total_orders']:,}件")
        print(f"   平均注文額: ¥{stats['avg_order_value']:,.0f}")

        # 人気商品ランキング
        if stats['top_products']:
            print(f"\n🏆 人気商品 Top 5:")
            for i, product in enumerate(stats['top_products'], 1):
                print(f"   {i}. {product['product_name']}")
                print(f"      📊 売上: ¥{product['total_sales']:,}")
                print(f"      📦 販売数: {product['total_quantity']}個")
                print(f"      🔄 注文回数: {product['order_count']}回")
        else:
            print("\n⚠️ 人気商品データがありません")

        # 都市別売上
        if stats['sales_by_city']:
            print(f"\n🌆 都市別売上:")
            for city_data in stats['sales_by_city']:
                if city_data['total_sales'] > 0:
                    print(f"   🏙️ {city_data['city']}:")
                    print(f"      💰 売上: ¥{city_data['total_sales']:,}")
                    print(f"      👥 顧客数: {city_data['customer_count']}人")
                    print(f"      📦 注文数: {city_data['order_count']}件")
        else:
            print("\n⚠️ 都市別売上データがありません")

    except Exception as e:
        print(f"❌ 売上分析デモでエラーが発生: {e}")
        traceback.print_exc()


def demo_customer_analysis():
    """顧客分析のデモ"""
    print("\n" + "=" * 60)
    print("👥 顧客分析デモ")
    print("=" * 60)

    try:
        client = MCPAPIClient()

        # 顧客一覧から最初の顧客を分析
        customers = client.get_customers(limit=3)
        if not customers:
            print("⚠️ 顧客データがありません")
            return

        # 複数の顧客を分析
        for i, customer in enumerate(customers[:2], 1):
            customer_id = customer['id']
            customer_name = customer['name']

            print(f"\n🔍 {i}. {customer_name} さんの分析 (ID: {customer_id})")

            try:
                # 顧客別統計取得
                customer_stats = client.get_customer_order_stats(customer_id)

                order_stats = customer_stats['order_stats']
                customer_info = customer_stats['customer']

                print(f"   📋 基本情報:")
                print(f"      名前: {customer_info['name']}")
                print(f"      都市: {customer_info['city']}")
                print(f"      メール: {customer_info['email']}")

                print(f"   📊 注文統計:")
                print(f"      総注文数: {order_stats['total_orders']}件")
                print(f"      総購入額: ¥{order_stats['total_spent']:,}")

                if order_stats['total_orders'] > 0:
                    print(f"      平均注文額: ¥{order_stats['avg_order_value']:,}")
                    print(f"      初回注文日: {order_stats['first_order_date']}")
                    print(f"      最終注文日: {order_stats['last_order_date']}")

                    # 購入商品ランキング
                    if customer_stats['product_preferences']:
                        print(f"   🛍️ 購入商品ランキング:")
                        for j, product in enumerate(customer_stats['product_preferences'][:3], 1):
                            print(f"      {j}. {product['product_name']}")
                            print(f"         購入額: ¥{product['total_spent']:,}")
                            print(f"         購入数: {product['total_quantity']}個")
                            print(f"         注文回数: {product['order_count']}回")
                    else:
                        print("   🛍️ 購入履歴がありません")
                else:
                    print("      まだ注文をしていません")

            except Exception as e:
                print(f"   ❌ {customer_name} さんの統計取得に失敗: {e}")

    except Exception as e:
        print(f"❌ 顧客分析デモでエラーが発生: {e}")
        traceback.print_exc()


def demo_create_data():
    """データ作成のデモ"""
    print("\n" + "=" * 60)
    print("✨ データ作成デモ")
    print("=" * 60)

    try:
        client = MCPAPIClient()

        # 現在の時刻を使ってユニークなデータを作成
        timestamp = int(time.time())

        # 新規顧客作成
        print("\n👤 新規顧客を作成")
        new_customer_data = {
            "name" : f"API太郎{timestamp % 1000}",
            "email": f"api.taro.{timestamp}@example.com",
            "city" : "東京"
        }

        print(f"   作成データ: {new_customer_data}")
        new_customer = client.create_customer(**new_customer_data)

        print(f"   ✅ 顧客作成成功!")
        print(f"   📋 作成された顧客:")
        print(f"      ID: {new_customer['id']}")
        print(f"      名前: {new_customer['name']}")
        print(f"      メール: {new_customer['email']}")
        print(f"      都市: {new_customer['city']}")
        print(f"      作成日時: {new_customer['created_at']}")

        # 新規注文作成
        print("\n📦 新規注文を作成")
        new_order_data = {
            "customer_id" : new_customer['id'],
            "product_name": "ノートパソコン",
            "quantity"    : 1,
            "price"       : 89800
        }

        print(f"   注文データ: {new_order_data}")
        new_order = client.create_order(**new_order_data)

        print(f"   ✅ 注文作成成功!")
        print(f"   📋 作成された注文:")
        print(f"      注文ID: {new_order['id']}")
        print(f"      顧客ID: {new_order['customer_id']}")
        print(f"      商品: {new_order['product_name']}")
        print(f"      数量: {new_order['quantity']}")
        print(f"      価格: ¥{new_order['price']:,}")
        print(f"      注文日: {new_order['order_date']}")
        print(f"      総額: ¥{new_order['price'] * new_order['quantity']:,}")

        # 作成したデータの確認
        print("\n🔍 作成したデータの確認")

        # 顧客情報を再取得
        retrieved_customer = client.get_customer(new_customer['id'])
        print(f"   顧客再取得: {retrieved_customer['name']} - OK")

        # その顧客の注文一覧を取得
        customer_orders = client.get_orders(customer_id=new_customer['id'])
        print(f"   顧客の注文数: {len(customer_orders)}件")

        return new_customer, new_order

    except Exception as e:
        print(f"❌ データ作成デモでエラーが発生: {e}")
        traceback.print_exc()
        return None, None


def demo_pandas_integration():
    """Pandas連携のデモ"""
    print("\n" + "=" * 60)
    print("🐼 Pandas連携デモ")
    print("=" * 60)

    try:
        client = MCPAPIClient()

        # 顧客データをDataFrameに変換
        print("\n📊 顧客データをPandas DataFrameで分析")
        customers = client.get_customers()

        if not customers:
            print("⚠️ 顧客データがありません")
            return

        df_customers = pd.DataFrame(customers)

        print("   顧客データの概要:")
        print(f"   📏 データ形状: {df_customers.shape}")
        print(f"   📋 カラム: {list(df_customers.columns)}")

        print("\n   顧客データサンプル:")
        print(df_customers[['name', 'city', 'email']].head())

        print(f"\n🏙️ 都市別顧客数:")
        city_counts = df_customers['city'].value_counts()
        print(city_counts)

        # 注文データの分析
        print(f"\n📦 注文データをPandas DataFrameで分析")
        orders = client.get_orders()

        if not orders:
            print("⚠️ 注文データがありません")
            return

        df_orders = pd.DataFrame(orders)

        print("   注文データの概要:")
        print(f"   📏 データ形状: {df_orders.shape}")
        print(f"   📋 カラム: {list(df_orders.columns)}")

        # 日別売上分析
        if 'order_date' in df_orders.columns:
            print(f"\n📅 日別売上分析:")
            df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])
            daily_sales = df_orders.groupby('order_date')['total_amount'].sum().sort_index()

            print(f"   📊 日別売上 (最新5日):")
            print(daily_sales.tail().apply(lambda x: f"¥{x:,.0f}"))

            # 統計情報
            print(f"\n📈 売上統計:")
            print(f"   平均日販: ¥{daily_sales.mean():,.0f}")
            print(f"   最大日販: ¥{daily_sales.max():,.0f}")
            print(f"   最小日販: ¥{daily_sales.min():,.0f}")

        # 商品別売上分析
        if 'product_name' in df_orders.columns and 'total_amount' in df_orders.columns:
            print(f"\n🛍️ 商品別売上分析:")
            product_sales = df_orders.groupby('product_name').agg({
                'total_amount': 'sum',
                'quantity'    : 'sum',
                'id'          : 'count'
            }).rename(columns={'id': 'order_count'}).sort_values('total_amount', ascending=False)

            print(f"   🏆 商品別売上 Top 5:")
            for i, (product, stats) in enumerate(product_sales.head().iterrows(), 1):
                print(f"   {i}. {product}")
                print(f"      売上: ¥{stats['total_amount']:,.0f}")
                print(f"      販売数: {stats['quantity']}個")
                print(f"      注文回数: {stats['order_count']}回")

        # 顧客別分析
        if 'customer_name' in df_orders.columns:
            print(f"\n👥 顧客別購入分析:")
            customer_stats = df_orders.groupby('customer_name').agg({
                'total_amount': ['sum', 'mean', 'count']
            }).round(0)

            customer_stats.columns = ['総購入額', '平均注文額', '注文回数']
            customer_stats = customer_stats.sort_values('総購入額', ascending=False)

            print(f"   💰 上位顧客 Top 3:")
            for i, (customer, stats) in enumerate(customer_stats.head(3).iterrows(), 1):
                print(f"   {i}. {customer}")
                print(f"      総購入額: ¥{stats['総購入額']:,.0f}")
                print(f"      平均注文額: ¥{stats['平均注文額']:,.0f}")
                print(f"      注文回数: {stats['注文回数']}回")

    except ImportError:
        print("❌ pandas ライブラリが必要です")
        print("💡 インストール: pip install pandas")
    except Exception as e:
        print(f"❌ Pandas連携デモでエラーが発生: {e}")
        traceback.print_exc()


def demo_error_handling():
    """エラーハンドリングのデモ"""
    print("\n" + "=" * 60)
    print("⚠️ エラーハンドリングデモ")
    print("=" * 60)

    client = MCPAPIClient()

    # 存在しない顧客を取得
    print("\n❌ 1. 存在しない顧客を取得")
    try:
        customer = client.get_customer(99999)
        print(f"   予期しない成功: {customer}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"   ✅ 期待通り404エラーが発生: 顧客が見つかりません")
        else:
            print(f"   ⚠️ 予期しないHTTPエラー: {e}")
    except Exception as e:
        print(f"   ❌ 予期しないエラー: {e}")

    # 存在しない商品を取得
    print("\n❌ 2. 存在しない商品を取得")
    try:
        product = client.get_product(99999)
        print(f"   予期しない成功: {product}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"   ✅ 期待通り404エラーが発生: 商品が見つかりません")
        else:
            print(f"   ⚠️ 予期しないHTTPエラー: {e}")
    except Exception as e:
        print(f"   ❌ 予期しないエラー: {e}")

    # 無効な注文を作成
    print("\n❌ 3. 存在しない顧客IDで注文作成")
    try:
        order = client.create_order(
            customer_id=99999,
            product_name="テスト商品",
            quantity=1,
            price=1000
        )
        print(f"   予期しない成功: {order}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"   ✅ 期待通り404エラーが発生: 顧客が見つかりません")
        else:
            print(f"   ⚠️ 予期しないHTTPエラー: {e}")
    except Exception as e:
        print(f"   ❌ 予期しないエラー: {e}")

    # 無効なデータで顧客作成
    print("\n❌ 4. 無効なデータで顧客作成")
    try:
        # 空の名前で顧客作成
        customer = client.create_customer(
            name="",  # 空の名前
            email="invalid-email",  # 無効なメールアドレス
            city=""  # 空の都市名
        )
        print(f"   予期しない成功: {customer}")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 422:
            print(f"   ✅ 期待通り422エラーが発生: バリデーションエラー")
            try:
                error_detail = e.response.json()
                print(f"   📋 エラー詳細: {error_detail}")
            except:
                print(f"   📋 エラー詳細: {e.response.text}")
        else:
            print(f"   ⚠️ 予期しないHTTPエラー: {e}")
    except Exception as e:
        print(f"   ❌ 予期しないエラー: {e}")

    print("\n✅ エラーハンドリングデモ完了")
    print("💡 適切なエラーハンドリングにより、アプリケーションの安定性が向上します")


def demo_performance_test():
    """パフォーマンステストのデモ"""
    print("\n" + "=" * 60)
    print("⚡ パフォーマンステストデモ")
    print("=" * 60)

    try:
        client = MCPAPIClient()

        # レスポンス時間計測
        print("\n⏱️ レスポンス時間計測")

        endpoints = [
            ("顧客一覧", lambda: client.get_customers(limit=10)),
            ("商品一覧", lambda: client.get_products(limit=10)),
            ("注文一覧", lambda: client.get_orders(limit=10)),
            ("売上統計", lambda: client.get_sales_stats()),
        ]

        for name, func in endpoints:
            start_time = time.time()
            try:
                result = func()
                end_time = time.time()
                duration = end_time - start_time

                if isinstance(result, list):
                    count = len(result)
                    print(f"   📊 {name}: {duration:.3f}秒 ({count}件取得)")
                else:
                    print(f"   📊 {name}: {duration:.3f}秒")

            except Exception as e:
                end_time = time.time()
                duration = end_time - start_time
                print(f"   ❌ {name}: {duration:.3f}秒 (エラー: {e})")

        # 連続リクエストテスト
        print(f"\n🔄 連続リクエストテスト (顧客一覧を5回取得)")

        times = []
        for i in range(5):
            start_time = time.time()
            try:
                customers = client.get_customers(limit=5)
                end_time = time.time()
                duration = end_time - start_time
                times.append(duration)
                print(f"   {i + 1}回目: {duration:.3f}秒 ({len(customers)}件)")
            except Exception as e:
                print(f"   {i + 1}回目: エラー - {e}")

        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)

            print(f"\n📈 連続リクエスト統計:")
            print(f"   平均時間: {avg_time:.3f}秒")
            print(f"   最短時間: {min_time:.3f}秒")
            print(f"   最長時間: {max_time:.3f}秒")

    except Exception as e:
        print(f"❌ パフォーマンステストでエラーが発生: {e}")
        traceback.print_exc()


def interactive_demo():
    """インタラクティブデモ"""
    print("\n" + "=" * 60)
    print("🎮 インタラクティブデモ")
    print("=" * 60)

    try:
        client = MCPAPIClient()

        while True:
            print("\n🎯 何をしますか？")
            print("1. 顧客を検索")
            print("2. 商品を検索")
            print("3. 注文を検索")
            print("4. 新規顧客を作成")
            print("5. 新規注文を作成")
            print("6. 売上統計を表示")
            print("0. 終了")

            choice = input("\n選択してください (0-6): ").strip()

            if choice == "0":
                print("👋 インタラクティブデモを終了します")
                break
            elif choice == "1":
                # 顧客検索
                city = input("都市名を入力 (空白で全て): ").strip()
                city = city if city else None

                customers = client.get_customers(city=city, limit=10)
                print(f"\n📋 検索結果: {len(customers)}件")

                for i, customer in enumerate(customers, 1):
                    print(f"{i}. {customer['name']} ({customer['city']}) - {customer['email']}")

            elif choice == "2":
                # 商品検索
                category = input("カテゴリを入力 (空白で全て): ").strip()
                category = category if category else None

                try:
                    max_price_str = input("最大価格を入力 (空白で制限なし): ").strip()
                    max_price = float(max_price_str) if max_price_str else None
                except ValueError:
                    max_price = None

                products = client.get_products(category=category, max_price=max_price, limit=10)
                print(f"\n🛍️ 検索結果: {len(products)}件")

                for i, product in enumerate(products, 1):
                    print(f"{i}. {product['name']} - ¥{product['price']:,} "
                          f"({product['category']}, 在庫: {product['stock_quantity']})")

            elif choice == "3":
                # 注文検索
                try:
                    customer_id_str = input("顧客ID (空白で全て): ").strip()
                    customer_id = int(customer_id_str) if customer_id_str else None
                except ValueError:
                    customer_id = None

                orders = client.get_orders(customer_id=customer_id, limit=10)
                print(f"\n📦 検索結果: {len(orders)}件")

                for i, order in enumerate(orders, 1):
                    print(f"{i}. {order['customer_name']}: {order['product_name']} "
                          f"x{order['quantity']} = ¥{order['total_amount']:,} ({order['order_date']})")

            elif choice == "4":
                # 新規顧客作成
                name = input("顧客名: ").strip()
                email = input("メールアドレス: ").strip()
                city = input("都市名: ").strip()

                if name and email and city:
                    try:
                        new_customer = client.create_customer(name, email, city)
                        print(f"\n✅ 顧客作成成功!")
                        print(f"ID: {new_customer['id']}, 名前: {new_customer['name']}")
                    except Exception as e:
                        print(f"\n❌ 顧客作成失敗: {e}")
                else:
                    print("\n⚠️ 全ての項目を入力してください")

            elif choice == "5":
                # 新規注文作成
                try:
                    customer_id = int(input("顧客ID: ").strip())
                    product_name = input("商品名: ").strip()
                    quantity = int(input("数量: ").strip())
                    price = float(input("価格: ").strip())

                    new_order = client.create_order(customer_id, product_name, quantity, price)
                    print(f"\n✅ 注文作成成功!")
                    print(f"注文ID: {new_order['id']}, 総額: ¥{price * quantity:,}")
                except ValueError:
                    print("\n❌ 数値項目は正しい数値を入力してください")
                except Exception as e:
                    print(f"\n❌ 注文作成失敗: {e}")

            elif choice == "6":
                # 売上統計表示
                stats = client.get_sales_stats()
                print(f"\n📊 売上統計:")
                print(f"総売上: ¥{stats['total_sales']:,}")
                print(f"注文数: {stats['total_orders']:,}件")
                print(f"平均注文額: ¥{stats['avg_order_value']:,}")

                if stats['top_products']:
                    print(f"\n🏆 人気商品:")
                    for i, product in enumerate(stats['top_products'][:3], 1):
                        print(f"{i}. {product['product_name']} - ¥{product['total_sales']:,}")

            else:
                print("❌ 無効な選択です")

    except KeyboardInterrupt:
        print("\n👋 インタラクティブデモを終了します")
    except Exception as e:
        print(f"❌ インタラクティブデモでエラーが発生: {e}")
        traceback.print_exc()


def main():
    """メインデモ実行"""
    print("🚀 MCP API クライアントデモを開始")
    print(f"📅 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        # APIサーバーの接続確認
        print("🔍 APIサーバーの接続確認中...")
        client = MCPAPIClient()
        if not client.ping():
            print("❌ APIサーバーに接続できません")
            print("\n💡 解決方法:")
            print("1. APIサーバーを起動: python mcp_api_server.py")
            print("2. PostgreSQLを起動: docker-compose -f docker-compose.mcp-demo.yml up -d postgres")
            print("3. テストデータ投入: python setup_test_data.py")
            return

        # デモメニュー
        print("\n🎮 実行するデモを選択してください:")
        print("1. 基本操作デモ")
        print("2. 売上分析デモ")
        print("3. 顧客分析デモ")
        print("4. データ作成デモ")
        print("5. Pandas連携デモ")
        print("6. エラーハンドリングデモ")
        print("7. パフォーマンステストデモ")
        print("8. インタラクティブデモ")
        print("9. 全てのデモを順番に実行")
        print("0. 簡単なテストのみ実行")

        try:
            choice = input("\n選択してください (0-9): ").strip()
        except KeyboardInterrupt:
            print("\n👋 デモを終了します")
            return

        if choice == "1":
            demo_basic_operations()
        elif choice == "2":
            demo_sales_analytics()
        elif choice == "3":
            demo_customer_analysis()
        elif choice == "4":
            demo_create_data()
        elif choice == "5":
            demo_pandas_integration()
        elif choice == "6":
            demo_error_handling()
        elif choice == "7":
            demo_performance_test()
        elif choice == "8":
            interactive_demo()
        elif choice == "9":
            print("🎯 全てのデモを順番に実行します...")
            demo_basic_operations()
            demo_sales_analytics()
            demo_customer_analysis()
            new_customer, new_order = demo_create_data()
            demo_pandas_integration()
            demo_error_handling()
            demo_performance_test()
        elif choice == "0":
            print("🧪 簡単なテストを実行...")
            client = MCPAPIClient()

            # ヘルスチェック
            health_ok = client.ping()
            print(f"ヘルスチェック: {'✅ OK' if health_ok else '❌ NG'}")

            # 基本的なデータ取得
            customers = client.get_customers(limit=1)
            print(f"顧客取得: {'✅ OK' if customers else '⚠️ データなし'} ({len(customers)}件)")

            products = client.get_products(limit=1)
            print(f"商品取得: {'✅ OK' if products else '⚠️ データなし'} ({len(products)}件)")

            orders = client.get_orders(limit=1)
            print(f"注文取得: {'✅ OK' if orders else '⚠️ データなし'} ({len(orders)}件)")

            stats = client.get_sales_stats()
            print(f"統計取得: {'✅ OK' if stats else '❌ NG'}")
            if stats:
                print(f"  総売上: ¥{stats['total_sales']:,}")
        else:
            print("❌ 無効な選択です")

        print("\n" + "=" * 70)
        print("🎉 デモ完了!")
        print("\n💡 次のステップ:")
        print("📖 APIドキュメント: http://localhost:8000/docs")
        print("🔧 詳細なテスト: python quick_test.py")
        print("🎮 対話型テスト: 再度このスクリプトを実行してメニュー8を選択")

    except KeyboardInterrupt:
        print("\n👋 デモを終了します")
    except Exception as e:
        print(f"\n❌ デモ実行エラー: {e}")
        print("\n🔍 デバッグ情報:")
        traceback.print_exc()
        print("\n💡 解決方法:")
        print("1. APIサーバーが起動しているか確認: http://localhost:8000/health")
        print("2. PostgreSQLが起動しているか確認")
        print("3. 必要なパッケージがインストールされているか確認")


if __name__ == "__main__":
    main()
