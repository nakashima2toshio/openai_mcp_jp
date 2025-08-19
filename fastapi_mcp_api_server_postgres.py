# MCP API クライアントの9つのデモ機能をStreamlit化
# streamlit run fastapi_mcp_api_server_postgres.py --server.port=8502

import streamlit as st
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import pandas as pd
import time
import json
import plotly.express as px
import plotly.graph_objects as go

# ヘルパーモジュールからインポート
from helper_mcp import MCPSessionManager, ServerStatusManager, PageManager
from helper_st import UIHelper, SessionStateManager
from mcp_api_client import MCPAPIClient


class MCPDemoApplication:
    """MCP APIデモアプリケーションのメインクラス"""
    
    def __init__(self):
        # 環境変数を読み込み
        load_dotenv()
        
        # セッション状態の初期化
        MCPSessionManager.init_session()
        self._init_demo_session_state()
        
        # API クライアントの初期化
        self.api_base_url = os.getenv('MCP_API_BASE_URL', 'http://localhost:8000')
        
        # ステータス管理（helper_mcpから）
        self.status_manager = ServerStatusManager()
    
    def _init_demo_session_state(self):
        """デモ固有のセッション状態を初期化"""
        defaults = {
            'mcp_api_client': None,
            'selected_demo_page': 'ホーム',
            'api_connected': False,
            'last_api_check': 0,
            'demo_data_cache': {},
            'performance_results': [],
            'created_customers': [],
            'created_orders': []
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def get_api_client(self) -> Optional[MCPAPIClient]:
        """APIクライアントを取得（キャッシュ付き）"""
        if st.session_state.mcp_api_client is None:
            try:
                st.session_state.mcp_api_client = MCPAPIClient(self.api_base_url)
                st.session_state.api_connected = True
            except Exception as e:
                st.error(f"⚠️ API サーバーに接続できません: {e}")
                st.session_state.api_connected = False
                return None
        
        return st.session_state.mcp_api_client
    
    def render_sidebar(self):
        """サイドバーの描画"""
        st.sidebar.markdown("## 🤖 MCP API デモアプリ")
        
        # API接続状態の表示
        client = self.get_api_client()
        if client and st.session_state.api_connected:
            st.sidebar.success("✅ API サーバー接続済み")
            st.sidebar.info(f"🔗 {self.api_base_url}")
        else:
            st.sidebar.error("❌ API サーバー未接続")
            st.sidebar.warning("💡 解決方法:\n1. `python mcp_api_server.py` で起動\n2. ポート8000が空いているか確認")
        
        st.sidebar.markdown("---")
        
        # ページ選択
        demo_pages = [
            "ホーム",
            "基本操作",
            "売上分析", 
            "顧客分析",
            "データ作成",
            "データ分析",
            "エラーテスト",
            "パフォーマンス",
            "対話機能"
        ]
        
        selected_page = st.sidebar.radio(
            "📋 デモページ選択",
            demo_pages,
            index=demo_pages.index(st.session_state.selected_demo_page) if st.session_state.selected_demo_page in demo_pages else 0
        )
        
        if selected_page != st.session_state.selected_demo_page:
            st.session_state.selected_demo_page = selected_page
            st.rerun()
        
        # 追加情報
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ℹ️ 情報")

        # 開発者向け情報
        if st.sidebar.expander("🛠️ 開発者情報"):
                st.write("Toshioakashima")
            st.sidebar.code(f"API URL: {self.api_base_url}")
            st.sidebar.code(f"接続状態: {st.session_state.api_connected}")
            st.sidebar.code(f"選択ページ: {st.session_state.selected_demo_page}")
    
    def render_main_content(self):
        """メインコンテンツの描画"""
        page_name = st.session_state.selected_demo_page
        
        # ページヘッダー
        st.markdown(f"# 📊 {page_name}")
        st.markdown("---")
        
        # 各ページの描画
        if page_name == "ホーム":
            self._render_home_page()
        elif page_name == "基本操作":
            self._render_basic_operations_page()
        elif page_name == "売上分析":
            self._render_sales_analytics_page()
        elif page_name == "顧客分析":
            self._render_customer_analysis_page()
        elif page_name == "データ作成":
            self._render_data_creation_page()
        elif page_name == "データ分析":
            self._render_data_analysis_page()
        elif page_name == "エラーテスト":
            self._render_error_handling_page()
        elif page_name == "パフォーマンス":
            self._render_performance_page()
        elif page_name == "対話機能":
            self._render_interactive_page()
        else:
            st.error(f"未実装のページ: {page_name}")
    
    def _render_home_page(self):
        """ホームページの描画"""
        st.markdown("## 🏠 ホーム・概要")
        
        # API接続テスト
        client = self.get_api_client()
        if not client:
            st.error("🚨 API サーバーに接続できません。")
            st.markdown("### 🔧 セットアップ手順")
            st.markdown("""
            1. **APIサーバーを起動**: `python mcp_api_server.py`
            2. **データベースを起動**: `docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d`
            3. **テストデータを投入**: `python setup_test_data.py`
            4. **ページをリフレッシュ**: ブラウザでF5キーを押下
            """)
            return
        
        # ヘルスチェック実行
        st.markdown("### 🏥 システム状態")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 ヘルスチェック実行", type="primary"):
                with st.spinner("ヘルスチェック実行中..."):
                    try:
                        health_result = client.check_health()
                        if health_result:
                            st.success("✅ システム正常")
                        else:
                            st.error("❌ システム異常")
                    except Exception as e:
                        st.error(f"❌ ヘルスチェック失敗: {e}")
        
        with col2:
            st.metric("API接続", "✅ 接続済み" if st.session_state.api_connected else "❌ 未接続")
        
        with col3:
            st.metric("ベースURL", self.api_base_url)
        
        # 機能概要
        st.markdown("### 🎯 利用可能なデモ機能")
        
        demo_info = [
            {"name": "基本操作", "icon": "🔍", "desc": "顧客・商品・注文データの表示・検索"},
            {"name": "売上分析", "icon": "📈", "desc": "売上統計とビジネス指標のダッシュボード"},
            {"name": "顧客分析", "icon": "👥", "desc": "個別顧客の購買行動分析"},
            {"name": "データ作成", "icon": "📝", "desc": "新しい顧客・注文データの作成"},
            {"name": "データ分析", "icon": "🐼", "desc": "Pandas を使った高度なデータ分析"},
            {"name": "エラーテスト", "icon": "🚨", "desc": "エラーハンドリングの動作確認"},
            {"name": "パフォーマンス", "icon": "⚡", "desc": "API応答時間とパフォーマンス測定"},
            {"name": "対話機能", "icon": "🔄", "desc": "リアルタイムでのデータ操作"}
        ]
        
        for i in range(0, len(demo_info), 2):
            col1, col2 = st.columns(2)
            
            with col1:
                info = demo_info[i]
                st.markdown(f"""
                **{info['icon']} {info['name']}**  
                {info['desc']}
                """)
            
            if i + 1 < len(demo_info):
                with col2:
                    info = demo_info[i + 1]
                    st.markdown(f"""
                    **{info['icon']} {info['name']}**  
                    {info['desc']}
                    """)
        
        st.markdown("### 🚀 使用方法")
        st.markdown("""
        1. **サイドバー**から利用したいデモ機能を選択
        2. 各ページで**フォームやボタン**を使って操作
        3. **結果やグラフ**でデータを確認
        4. **エラーが発生**した場合は画面の指示に従って対処
        """)
    
    def _render_basic_operations_page(self):
        """基本操作ページの描画（デモ機能1）"""
        st.markdown("## 🔍 基本操作デモ")
        st.markdown("顧客・商品・注文データの表示と検索機能")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # タブで機能を分割
        tab1, tab2, tab3 = st.tabs(["👥 顧客データ", "🛍️ 商品データ", "📦 注文データ"])
        
        with tab1:
            self._render_customers_section(client)
        
        with tab2:
            self._render_products_section(client)
            
        with tab3:
            self._render_orders_section(client)
    
    def _render_customers_section(self, client: MCPAPIClient):
        """顧客データセクションの描画"""
        st.markdown("### 👥 顧客データ管理")
        
        # フィルタオプション
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            city_filter = st.selectbox(
                "🏙️ 都市フィルタ", 
                ["すべて", "東京", "大阪", "名古屋", "福岡", "札幌"],
                key="customer_city_filter"
            )
        
        with col2:
            limit = st.number_input("表示件数", min_value=1, max_value=100, value=20, key="customer_limit")
        
        with col3:
            if st.button("🔍 検索", key="search_customers"):
                st.session_state.demo_data_cache.pop('customers', None)  # キャッシュクリア
        
        # データ取得と表示
        try:
            with st.spinner("顧客データ読み込み中..."):
                # APIパラメータ準備
                params = {"limit": limit}
                if city_filter != "すべて":
                    params["city"] = city_filter
                
                # データ取得
                customers_data = client._make_request("GET", "/api/customers", params=params)
                
                # レスポンス形式を統一的に処理
                if customers_data:
                    if isinstance(customers_data, list):
                        # 直接配列が返された場合
                        customers = customers_data
                    elif isinstance(customers_data, dict) and "customers" in customers_data:
                        # オブジェクト内のcustomersキーから取得
                        customers = customers_data["customers"]
                    else:
                        customers = []
                else:
                    customers = []
                
                if customers:
                    
                    # 統計情報表示
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("総顧客数", len(customers))
                    with col2:
                        cities = set(c.get("city", "") for c in customers)
                        st.metric("都市数", len(cities))
                    with col3:
                        tokyo_customers = len([c for c in customers if c.get("city") == "東京"])
                        st.metric("東京の顧客", tokyo_customers)
                    with col4:
                        with_email = len([c for c in customers if c.get("email")])
                        st.metric("メール登録済み", with_email)
                    
                    # データテーブル表示
                    if customers:
                        st.markdown("#### 📋 顧客一覧")
                        
                        # DataFrameに変換して表示
                        import pandas as pd
                        df = pd.DataFrame(customers)
                        
                        # 列の並び替えと日本語化
                        if not df.empty:
                            column_mapping = {
                                "id": "ID",
                                "name": "名前", 
                                "email": "メールアドレス",
                                "city": "都市",
                                "created_at": "登録日"
                            }
                            
                            display_cols = [col for col in ["id", "name", "email", "city", "created_at"] if col in df.columns]
                            df_display = df[display_cols].rename(columns=column_mapping)
                            
                            st.dataframe(
                                df_display,
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # CSVダウンロード
                            csv = df_display.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📥 CSVダウンロード",
                                data=csv,
                                file_name=f"customers_{city_filter}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("条件に合う顧客データが見つかりませんでした。")
                    else:
                        st.info("表示する顧客データがありません。")
                else:
                    st.error("顧客データの取得に失敗しました。")
                    
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
    
    def _render_products_section(self, client: MCPAPIClient):
        """商品データセクションの描画"""
        st.markdown("### 🛍️ 商品データ管理")
        
        # フィルタオプション
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            category_filter = st.selectbox(
                "📂 カテゴリフィルタ",
                ["すべて", "Electronics", "Books", "Clothing", "Home", "Sports"],
                key="product_category_filter"
            )
        
        with col2:
            min_price = st.number_input("最低価格", min_value=0, value=0, key="product_min_price")
        
        with col3:
            max_price = st.number_input("最高価格", min_value=0, value=50000, key="product_max_price")
        
        with col4:
            if st.button("🔍 検索", key="search_products"):
                st.session_state.demo_data_cache.pop('products', None)
        
        # データ取得と表示
        try:
            with st.spinner("商品データ読み込み中..."):
                params = {}
                if category_filter != "すべて":
                    params["category"] = category_filter
                if min_price > 0:
                    params["min_price"] = min_price
                if max_price > 0 and max_price != 50000:
                    params["max_price"] = max_price
                
                products_data = client._make_request("GET", "/api/products", params=params)
                
                # レスポンス形式を統一的に処理
                if products_data:
                    if isinstance(products_data, list):
                        # 直接配列が返された場合
                        products = products_data
                    elif isinstance(products_data, dict) and "products" in products_data:
                        # オブジェクト内のproductsキーから取得
                        products = products_data["products"]
                    else:
                        products = []
                else:
                    products = []
                
                if products:
                    
                    # 統計情報
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("商品数", len(products))
                    with col2:
                        if products:
                            avg_price = sum(p.get("price", 0) for p in products) / len(products)
                            st.metric("平均価格", f"¥{avg_price:,.0f}")
                    with col3:
                        categories = set(p.get("category", "") for p in products)
                        st.metric("カテゴリ数", len(categories))
                    with col4:
                        electronics = len([p for p in products if p.get("category") == "Electronics"])
                        st.metric("Electronics", electronics)
                    
                    # データ表示
                    if products:
                        import pandas as pd
                        df = pd.DataFrame(products)
                        
                        column_mapping = {
                            "id": "ID",
                            "name": "商品名",
                            "category": "カテゴリ", 
                            "price": "価格",
                            "created_at": "登録日"
                        }
                        
                        display_cols = [col for col in ["id", "name", "category", "price", "created_at"] if col in df.columns]
                        df_display = df[display_cols].rename(columns=column_mapping)
                        
                        # 価格列のフォーマット
                        if "価格" in df_display.columns:
                            df_display["価格"] = df_display["価格"].apply(lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "")
                        
                        st.dataframe(
                            df_display,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # ダウンロード
                        csv = df_display.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 CSVダウンロード",
                            data=csv,
                            file_name=f"products_{category_filter}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("表示する商品データがありません。")
                        
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
    
    def _render_orders_section(self, client: MCPAPIClient):
        """注文データセクションの描画"""
        st.markdown("### 📦 注文データ管理")
        
        # フィルタオプション
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            customer_id_filter = st.number_input(
                "👤 顧客IDフィルタ（0=全顧客）", 
                min_value=0, 
                value=0,
                key="order_customer_filter"
            )
        
        with col2:
            limit = st.number_input("表示件数", min_value=1, max_value=50, value=20, key="order_limit")
        
        with col3:
            if st.button("🔍 検索", key="search_orders"):
                st.session_state.demo_data_cache.pop('orders', None)
        
        # データ取得と表示
        try:
            with st.spinner("注文データ読み込み中..."):
                params = {"limit": limit}
                if customer_id_filter > 0:
                    params["customer_id"] = customer_id_filter
                
                orders_data = client._make_request("GET", "/api/orders", params=params)
                
                # レスポンス形式を統一的に処理
                if orders_data:
                    if isinstance(orders_data, list):
                        # 直接配列が返された場合
                        orders = orders_data
                    elif isinstance(orders_data, dict) and "orders" in orders_data:
                        # オブジェクト内のordersキーから取得
                        orders = orders_data["orders"]
                    else:
                        orders = []
                else:
                    orders = []
                
                if orders:
                    
                    # 統計情報
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("注文数", len(orders))
                    with col2:
                        if orders:
                            total_amount = sum(o.get("price", 0) * o.get("quantity", 0) for o in orders)
                            st.metric("総売上", f"¥{total_amount:,.0f}")
                    with col3:
                        if orders:
                            total_quantity = sum(o.get("quantity", 0) for o in orders)
                            st.metric("総数量", f"{total_quantity:,}")
                    with col4:
                        customers = set(o.get("customer_id") for o in orders if o.get("customer_id"))
                        st.metric("顧客数", len(customers))
                    
                    # データ表示
                    if orders:
                        import pandas as pd
                        df = pd.DataFrame(orders)
                        
                        # 合計金額を計算
                        if "price" in df.columns and "quantity" in df.columns:
                            df["total"] = df["price"] * df["quantity"]
                        
                        column_mapping = {
                            "id": "注文ID",
                            "customer_id": "顧客ID",
                            "customer_name": "顧客名",
                            "product_name": "商品名",
                            "quantity": "数量",
                            "price": "単価",
                            "total": "合計",
                            "created_at": "注文日"
                        }
                        
                        display_cols = [col for col in ["id", "customer_id", "customer_name", "product_name", "quantity", "price", "total", "created_at"] if col in df.columns]
                        df_display = df[display_cols].rename(columns=column_mapping)
                        
                        # 金額列のフォーマット
                        for money_col in ["単価", "合計"]:
                            if money_col in df_display.columns:
                                df_display[money_col] = df_display[money_col].apply(
                                    lambda x: f"¥{x:,.0f}" if pd.notnull(x) else ""
                                )
                        
                        st.dataframe(
                            df_display,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # ダウンロード
                        csv = df_display.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 CSVダウンロード", 
                            data=csv,
                            file_name=f"orders_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("表示する注文データがありません。")
                        
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
        
    def _render_sales_analytics_page(self):
        """売上分析ページの描画（デモ機能2）"""
        st.markdown("## 📈 売上分析デモ")
        st.markdown("売上統計とビジネス指標のダッシュボード")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # 自動更新オプション
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 💰 売上統計ダッシュボード")
        with col2:
            auto_refresh = st.checkbox("🔄 自動更新", value=False, key="sales_auto_refresh")
            if st.button("🔄 更新", type="primary"):
                st.session_state.demo_data_cache.pop('sales_stats', None)
        
        try:
            with st.spinner("売上データ分析中..."):
                # 売上統計データを取得
                stats_data = client._make_request("GET", "/api/stats/sales")
                
                if stats_data:
                    # 基本統計指標
                    st.markdown("#### 📊 基本統計")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_sales = stats_data.get("total_sales", 0)
                        st.metric(
                            "💰 総売上",
                            f"¥{total_sales:,.0f}",
                            delta=f"+¥{total_sales*0.12:,.0f}" if total_sales > 0 else None
                        )
                    
                    with col2:
                        total_orders = stats_data.get("total_orders", 0)
                        st.metric(
                            "📦 総注文数", 
                            f"{total_orders:,}件",
                            delta=f"+{int(total_orders*0.08):,}" if total_orders > 0 else None
                        )
                    
                    with col3:
                        avg_order_value = stats_data.get("average_order_value", 0)
                        st.metric(
                            "📈 平均注文額",
                            f"¥{avg_order_value:,.0f}",
                            delta=f"+¥{avg_order_value*0.05:,.0f}" if avg_order_value > 0 else None
                        )
                    
                    with col4:
                        customer_count = len(stats_data.get("sales_by_city", []))
                        st.metric("👥 都市数", f"{customer_count}都市")
                    
                    # 人気商品ランキング
                    st.markdown("#### 🏆 人気商品ランキング TOP 5")
                    popular_products = stats_data.get("popular_products", [])
                    
                    if popular_products:
                        # グラフ用データ準備
                        import pandas as pd
                        import plotly.express as px
                        import plotly.graph_objects as go
                        
                        df_products = pd.DataFrame(popular_products[:5])
                        
                        # 商品売上グラフ
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            if not df_products.empty:
                                fig = px.bar(
                                    df_products,
                                    x="product_name",
                                    y="total_sales",
                                    title="商品別売上 (TOP 5)",
                                    labels={
                                        "product_name": "商品名",
                                        "total_sales": "売上額 (¥)"
                                    },
                                    color="total_sales",
                                    color_continuous_scale="viridis"
                                )
                                fig.update_layout(height=400)
                                st.plotly_chart(fig, use_container_width=True)
                        
                        with col2:
                            # 商品詳細テーブル
                            st.markdown("**商品詳細**")
                            for i, product in enumerate(popular_products[:5], 1):
                                with st.container():
                                    st.markdown(f"""
                                    **{i}. {product.get('product_name', 'Unknown')}**
                                    - 売上: ¥{product.get('total_sales', 0):,.0f}
                                    - 数量: {product.get('total_quantity', 0):,}個
                                    - 注文数: {product.get('order_count', 0):,}件
                                    """)
                    
                    # 都市別売上分析
                    st.markdown("#### 🌍 都市別売上分析")
                    sales_by_city = stats_data.get("sales_by_city", [])
                    
                    if sales_by_city:
                        import pandas as pd
                        import plotly.express as px
                        df_cities = pd.DataFrame(sales_by_city)
                        
                        # 都市別売上グラフ
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 棒グラフ
                            fig_bar = px.bar(
                                df_cities,
                                x="city",
                                y="total_sales",
                                title="都市別総売上",
                                labels={
                                    "city": "都市",
                                    "total_sales": "売上額 (¥)"
                                },
                                color="total_sales"
                            )
                            fig_bar.update_layout(height=350)
                            st.plotly_chart(fig_bar, use_container_width=True)
                        
                        with col2:
                            # 円グラフ
                            fig_pie = px.pie(
                                df_cities,
                                values="total_sales",
                                names="city",
                                title="都市別売上比率"
                            )
                            fig_pie.update_layout(height=350)
                            st.plotly_chart(fig_pie, use_container_width=True)
                        
                        # 都市別詳細テーブル
                        st.markdown("#### 📋 都市別詳細データ")
                        
                        # データフレーム整形
                        df_cities_display = df_cities.copy()
                        df_cities_display["total_sales"] = df_cities_display["total_sales"].apply(
                            lambda x: f"¥{x:,.0f}"
                        )
                        df_cities_display = df_cities_display.rename(columns={
                            "city": "都市",
                            "total_sales": "総売上",
                            "customer_count": "顧客数",
                            "order_count": "注文数"
                        })
                        
                        # ランキング追加
                        df_cities_display = df_cities_display.sort_values("総売上", key=lambda x: x.str.replace("¥", "").str.replace(",", "").astype(float), ascending=False)
                        df_cities_display.insert(0, "順位", range(1, len(df_cities_display) + 1))
                        
                        st.dataframe(
                            df_cities_display,
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # CSVダウンロード
                        csv = df_cities_display.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 都市別データをCSVダウンロード",
                            data=csv,
                            file_name=f"sales_by_city_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    
                    # 追加の分析指標
                    st.markdown("#### 🔍 詳細分析")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📈 成長指標**")
                        if total_sales > 0 and total_orders > 0:
                            efficiency = total_sales / total_orders
                            st.metric("効率性指標", f"¥{efficiency:,.0f}/注文")
                            
                            if popular_products:
                                top_product_share = popular_products[0].get("total_sales", 0) / total_sales * 100
                                st.metric("トップ商品シェア", f"{top_product_share:.1f}%")
                    
                    with col2:
                        st.markdown("**🎯 マーケット情報**")
                        if sales_by_city:
                            top_city = max(sales_by_city, key=lambda x: x.get("total_sales", 0))
                            st.metric("最大マーケット", top_city.get("city", "Unknown"))
                            
                            market_concentration = top_city.get("total_sales", 0) / total_sales * 100
                            st.metric("市場集中度", f"{market_concentration:.1f}%")
                    
                else:
                    st.error("売上データの取得に失敗しました。")
                    st.markdown("### 🔧 トラブルシューティング")
                    st.markdown("""
                    1. **データベースの確認**: PostgreSQLが起動しているか確認
                    2. **テストデータの投入**: `python setup_test_data.py` を実行
                    3. **API サーバーの再起動**: `python mcp_api_server.py` を再実行
                    """)
                    
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
            
            # エラーの詳細情報
            with st.expander("🔍 エラー詳細"):
                import traceback
                st.code(traceback.format_exc())
    
    def _render_customer_analysis_page(self):
        """顧客分析ページの描画（デモ機能3）"""
        st.markdown("## 👥 顧客分析デモ")
        st.markdown("個別顧客の購買行動と統計分析")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # 顧客選択セクション
        st.markdown("### 🔍 顧客選択")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 顧客リストを取得
            try:
                with st.spinner("顧客データ読み込み中..."):
                    customers_data = client._make_request("GET", "/api/customers", params={"limit": 100})
                    
                    # レスポンス形式を統一的に処理
                    if customers_data:
                        if isinstance(customers_data, list):
                            # 直接配列が返された場合
                            customers = customers_data
                        elif isinstance(customers_data, dict) and "customers" in customers_data:
                            # オブジェクト内のcustomersキーから取得
                            customers = customers_data["customers"]
                        else:
                            customers = []
                    else:
                        customers = []
                    
                    if not customers:
                        st.warning("⚠️ 顧客データが見つかりません。")
                        return
                    
                    # 顧客選択ボックス
                    customer_options = {f"{c['name']} (ID: {c['id']}) - {c.get('city', 'Unknown')}": c['id'] for c in customers}
                    selected_customer_label = st.selectbox(
                        "📋 分析対象の顧客を選択",
                        list(customer_options.keys()),
                        help="購買行動を分析したい顧客を選択してください"
                    )
                    selected_customer_id = customer_options[selected_customer_label]
                    
            except Exception as e:
                st.error(f"❌ 顧客データの読み込みに失敗しました: {str(e)}")
                return
        
        with col2:
            if st.button("🔄 データ更新", type="primary"):
                st.session_state.demo_data_cache.pop('customer_analysis', None)
        
        # 選択された顧客の分析
        if selected_customer_id:
            try:
                with st.spinner("顧客分析データ取得中..."):
                    # 顧客の詳細情報を取得
                    selected_customer = next((c for c in customers if c['id'] == selected_customer_id), None)
                    
                    # 顧客の注文履歴を取得
                    orders_data = client._make_request("GET", "/api/orders", params={"customer_id": selected_customer_id, "limit": 100})
                    
                    # レスポンス形式を統一的に処理
                    if orders_data:
                        if isinstance(orders_data, list):
                            # 直接配列が返された場合
                            orders = orders_data
                        elif isinstance(orders_data, dict) and "orders" in orders_data:
                            # オブジェクト内のordersキーから取得
                            orders = orders_data["orders"]
                        else:
                            orders = []
                    else:
                        orders = []
                
                # 顧客基本情報
                st.markdown("### 👤 顧客基本情報")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("顧客ID", selected_customer.get('id', 'N/A'))
                with col2:
                    st.metric("氏名", selected_customer.get('name', 'N/A'))
                with col3:
                    st.metric("都市", selected_customer.get('city', 'N/A'))
                with col4:
                    st.metric("登録日", selected_customer.get('created_at', 'N/A')[:10] if selected_customer.get('created_at') else 'N/A')
                
                if orders:
                    # 購買統計
                    st.markdown("### 📊 購買統計")
                    
                    import pandas as pd
                    import plotly.express as px
                    import plotly.graph_objects as go
                    
                    df_orders = pd.DataFrame(orders)
                    
                    # 合計金額を計算
                    if 'price' in df_orders.columns and 'quantity' in df_orders.columns:
                        df_orders['total'] = df_orders['price'] * df_orders['quantity']
                    
                    # 基本統計指標
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_orders = len(orders)
                        st.metric("🛒 総注文数", f"{total_orders}件")
                    
                    with col2:
                        if 'total' in df_orders.columns:
                            total_spent = df_orders['total'].sum()
                            st.metric("💰 総購入額", f"¥{total_spent:,.0f}")
                    
                    with col3:
                        if 'total' in df_orders.columns and total_orders > 0:
                            avg_order_value = df_orders['total'].mean()
                            st.metric("📈 平均注文額", f"¥{avg_order_value:,.0f}")
                    
                    with col4:
                        if 'quantity' in df_orders.columns:
                            total_items = df_orders['quantity'].sum()
                            st.metric("📦 総購入数", f"{total_items}個")
                    
                    # 商品別購買分析
                    st.markdown("### 🛍️ 商品別購買分析")
                    
                    if 'product_name' in df_orders.columns:
                        # 商品別集計
                        product_stats = df_orders.groupby('product_name').agg({
                            'quantity': 'sum',
                            'total': 'sum' if 'total' in df_orders.columns else 'count',
                            'id': 'count'
                        }).reset_index()
                        product_stats.columns = ['product_name', 'total_quantity', 'total_spent', 'order_count']
                        product_stats = product_stats.sort_values('total_spent', ascending=False)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 商品別支出グラフ
                            if not product_stats.empty:
                                fig_bar = px.bar(
                                    product_stats.head(10),
                                    x='product_name',
                                    y='total_spent',
                                    title="商品別支出額 TOP 10",
                                    labels={
                                        'product_name': '商品名',
                                        'total_spent': '支出額 (¥)'
                                    },
                                    color='total_spent',
                                    color_continuous_scale='viridis'
                                )
                                fig_bar.update_layout(height=400, xaxis_tickangle=-45)
                                st.plotly_chart(fig_bar, use_container_width=True)
                        
                        with col2:
                            # 商品別数量グラフ
                            fig_quantity = px.pie(
                                product_stats.head(8),
                                values='total_quantity',
                                names='product_name',
                                title="商品別購入数量比率"
                            )
                            fig_quantity.update_layout(height=400)
                            st.plotly_chart(fig_quantity, use_container_width=True)
                        
                        # 商品別詳細テーブル
                        st.markdown("#### 📋 商品別詳細データ")
                        
                        product_display = product_stats.copy()
                        product_display['total_spent'] = product_display['total_spent'].apply(lambda x: f"¥{x:,.0f}")
                        product_display = product_display.rename(columns={
                            'product_name': '商品名',
                            'total_quantity': '購入数量',
                            'total_spent': '支出額',
                            'order_count': '注文回数'
                        })
                        
                        # ランキング追加
                        product_display.insert(0, '順位', range(1, len(product_display) + 1))
                        
                        st.dataframe(
                            product_display,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # 購買時系列分析
                    st.markdown("### 📅 購買時系列分析")
                    
                    if 'created_at' in df_orders.columns:
                        # 日付を変換
                        df_orders['order_date'] = pd.to_datetime(df_orders['created_at']).dt.date
                        
                        # 日別集計
                        daily_stats = df_orders.groupby('order_date').agg({
                            'total': 'sum' if 'total' in df_orders.columns else 'count',
                            'id': 'count'
                        }).reset_index()
                        daily_stats.columns = ['date', 'daily_spent', 'daily_orders']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # 日別支出グラフ
                            fig_timeline = px.line(
                                daily_stats,
                                x='date',
                                y='daily_spent',
                                title="日別支出額推移",
                                labels={
                                    'date': '日付',
                                    'daily_spent': '支出額 (¥)'
                                },
                                markers=True
                            )
                            fig_timeline.update_layout(height=350)
                            st.plotly_chart(fig_timeline, use_container_width=True)
                        
                        with col2:
                            # 日別注文数グラフ
                            fig_orders = px.bar(
                                daily_stats,
                                x='date',
                                y='daily_orders',
                                title="日別注文数推移",
                                labels={
                                    'date': '日付',
                                    'daily_orders': '注文数'
                                }
                            )
                            fig_orders.update_layout(height=350)
                            st.plotly_chart(fig_orders, use_container_width=True)
                    
                    # 最近の注文履歴
                    st.markdown("### 📝 最近の注文履歴 (直近10件)")
                    
                    # created_at列の存在確認
                    if 'created_at' in df_orders.columns:
                        recent_orders = df_orders.sort_values('created_at', ascending=False).head(10)
                    else:
                        recent_orders = df_orders.head(10)
                    
                    # 表示用に整形
                    display_cols = ['id', 'product_name', 'quantity', 'price', 'total', 'created_at']
                    recent_display = recent_orders[[col for col in display_cols if col in recent_orders.columns]].copy()
                    
                    if 'created_at' in recent_display.columns:
                        recent_display['created_at'] = pd.to_datetime(recent_display['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                    
                    # 金額フォーマット
                    for col in ['price', 'total']:
                        if col in recent_display.columns:
                            recent_display[col] = recent_display[col].apply(lambda x: f"¥{x:,.0f}" if pd.notnull(x) else "")
                    
                    recent_display = recent_display.rename(columns={
                        'id': '注文ID',
                        'product_name': '商品名',
                        'quantity': '数量',
                        'price': '単価',
                        'total': '合計',
                        'created_at': '注文日時'
                    })
                    
                    st.dataframe(
                        recent_display,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # CSV ダウンロード
                    st.markdown("### 📥 データダウンロード")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 商品別データダウンロード
                        if 'product_display' in locals():
                            csv_products = product_display.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📊 商品別分析データをCSVダウンロード",
                                data=csv_products,
                                file_name=f"customer_{selected_customer_id}_products_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                    
                    with col2:
                        # 注文履歴ダウンロード
                        csv_orders = recent_display.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📋 注文履歴をCSVダウンロード",
                            data=csv_orders,
                            file_name=f"customer_{selected_customer_id}_orders_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                
                else:
                    st.info("📭 この顧客の注文履歴がありません。")
                    st.markdown("**💡 ヒント**: データ作成ページから新しい注文を作成してみてください。")
                    
            except Exception as e:
                st.error(f"❌ 顧客分析データの取得に失敗しました: {str(e)}")
                
                # エラーの詳細情報
                with st.expander("🔍 エラー詳細"):
                    import traceback
                    st.code(traceback.format_exc())
    
    def _render_data_creation_page(self):
        """データ作成ページの描画（デモ機能4）"""
        st.markdown("## 📝 データ作成デモ")
        st.markdown("新しい顧客・注文データの作成と管理")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # タブで機能を分割
        tab1, tab2, tab3 = st.tabs(["👤 顧客作成", "🛒 注文作成", "📋 作成履歴"])
        
        with tab1:
            self._render_customer_creation_form(client)
        
        with tab2:
            self._render_order_creation_form(client)
            
        with tab3:
            self._render_creation_history()
    
    def _render_customer_creation_form(self, client: MCPAPIClient):
        """顧客作成フォームの描画"""
        st.markdown("### 👤 新規顧客登録")
        
        # 既存のメールアドレス確認ボタン
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📧 既存メール確認", help="登録済みのメールアドレスを確認"):
                try:
                    customers_data = client._make_request("GET", "/api/customers", params={"limit": 50})
                    if customers_data and isinstance(customers_data, list):
                        emails = [c.get("email", "") for c in customers_data if c.get("email")]
                        st.info(f"**登録済みメールアドレス例:**\n" + "\n".join(emails[:10]))
                    else:
                        st.info("顧客データが見つかりません。")
                except Exception as e:
                    st.warning(f"メール確認に失敗: {str(e)}")
        
        with st.form("customer_creation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                customer_name = st.text_input(
                    "顧客名 *", 
                    placeholder="例: 山田太郎",
                    help="顧客の氏名を入力してください"
                )
                
                customer_city = st.selectbox(
                    "都市 *",
                    ["東京", "大阪", "名古屋", "福岡", "札幌", "横浜", "京都"],
                    help="居住都市を選択してください"
                )
            
            with col2:
                customer_email = st.text_input(
                    "メールアドレス *",
                    placeholder="例: yamada@example.com",
                    help="有効なメールアドレスを入力してください"
                )
                
                st.markdown("**必須項目には * が付いています**")
            
            # 送信ボタン
            submitted = st.form_submit_button("👤 顧客を作成", type="primary", use_container_width=True)
            
            if submitted:
                # バリデーション
                if not customer_name or not customer_email or not customer_city:
                    st.error("❌ すべての必須項目を入力してください。")
                    return
                
                if "@" not in customer_email or "." not in customer_email:
                    st.error("❌ 有効なメールアドレスを入力してください。")
                    return
                
                try:
                    with st.spinner("顧客を作成中..."):
                        # API呼び出し
                        customer_data = {
                            "name": customer_name,
                            "email": customer_email,
                            "city": customer_city
                        }
                        
                        result = client._make_request("POST", "/api/customers", json=customer_data)
                        
                        if result:
                            # セッション状態に保存
                            if 'created_customers' not in st.session_state:
                                st.session_state.created_customers = []
                            st.session_state.created_customers.append(result)
                            
                            # 成功メッセージ
                            st.success("✅ 顧客が正常に作成されました！")
                            
                            # 作成された顧客情報を表示
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("顧客ID", result.get("id", "N/A"))
                            with col2:
                                st.metric("氏名", result.get("name", "N/A"))
                            with col3:
                                st.metric("都市", result.get("city", "N/A"))
                            with col4:
                                st.metric("登録日", result.get("created_at", "N/A"))
                                
                        else:
                            st.error("❌ 顧客の作成に失敗しました。")
                
                except Exception as e:
                    error_message = str(e)
                    if "422" in error_message and "Email already exists" in error_message:
                        st.error("❌ このメールアドレスは既に登録されています。別のメールアドレスを使用してください。")
                        st.info("💡 ヒント: 一意のメールアドレスが必要です。例: tanaka2@example.com")
                    elif "422" in error_message:
                        st.error("❌ 入力データに問題があります。入力内容を確認してください。")
                    else:
                        st.error(f"❌ エラーが発生しました: {error_message}")
                    
                    # エラーの詳細情報を展開可能セクションで表示
                    with st.expander("🔍 エラー詳細"):
                        st.code(error_message)
    
    def _render_order_creation_form(self, client: MCPAPIClient):
        """注文作成フォームの描画"""
        st.markdown("### 🛒 新規注文登録")
        
        # まず顧客と商品のリストを取得
        try:
            with st.spinner("顧客・商品データ読み込み中..."):
                customers_data = client._make_request("GET", "/api/customers", params={"limit": 100})
                products_data = client._make_request("GET", "/api/products", params={"limit": 100})
                
                # レスポンス形式を統一的に処理
                if customers_data:
                    if isinstance(customers_data, list):
                        customers = customers_data
                    elif isinstance(customers_data, dict) and "customers" in customers_data:
                        customers = customers_data["customers"]
                    else:
                        customers = []
                else:
                    customers = []
                
                if products_data:
                    if isinstance(products_data, list):
                        products = products_data
                    elif isinstance(products_data, dict) and "products" in products_data:
                        products = products_data["products"]
                    else:
                        products = []
                else:
                    products = []
                
                if not customers:
                    st.warning("⚠️ 顧客データが見つかりません。先に顧客を作成してください。")
                    return
                
                if not products:
                    st.warning("⚠️ 商品データが見つかりません。システム管理者にお問い合わせください。")
                    return
            
            with st.form("order_creation_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # 顧客選択
                    customer_options = {f"{c['name']} (ID: {c['id']})": c['id'] for c in customers}
                    selected_customer_label = st.selectbox(
                        "顧客 *",
                        list(customer_options.keys()),
                        help="注文を行う顧客を選択してください"
                    )
                    selected_customer_id = customer_options[selected_customer_label]
                    
                    # 商品選択
                    product_options = {f"{p['name']} (¥{p['price']:,})": p for p in products}
                    selected_product_label = st.selectbox(
                        "商品 *",
                        list(product_options.keys()),
                        help="注文する商品を選択してください"
                    )
                    selected_product = product_options[selected_product_label]
                
                with col2:
                    # 数量
                    quantity = st.number_input(
                        "数量 *",
                        min_value=1,
                        max_value=100,
                        value=1,
                        help="注文する商品の数量を指定してください"
                    )
                    
                    # 合計金額の表示
                    total_price = selected_product['price'] * quantity
                    st.metric("合計金額", f"¥{total_price:,}")
                
                # 注文詳細の確認
                st.markdown("#### 📋 注文詳細確認")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**顧客**: {selected_customer_label}")
                with col2:
                    st.info(f"**商品**: {selected_product['name']}")
                with col3:
                    st.info(f"**数量**: {quantity}個")
                
                # 送信ボタン
                submitted = st.form_submit_button("🛒 注文を作成", type="primary", use_container_width=True)
                
                if submitted:
                    try:
                        with st.spinner("注文を作成中..."):
                            # API呼び出し
                            order_data = {
                                "customer_id": selected_customer_id,
                                "product_name": selected_product['name'],
                                "quantity": quantity,
                                "price": selected_product['price']
                            }
                            
                            result = client._make_request("POST", "/api/orders", json=order_data)
                            
                            if result:
                                # セッション状態に保存
                                if 'created_orders' not in st.session_state:
                                    st.session_state.created_orders = []
                                st.session_state.created_orders.append(result)
                                
                                # 成功メッセージ
                                st.success("✅ 注文が正常に作成されました！")
                                
                                # 作成された注文情報を表示
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("注文ID", result.get("id", "N/A"))
                                with col2:
                                    st.metric("顧客ID", result.get("customer_id", "N/A"))
                                with col3:
                                    st.metric("数量", f"{result.get('quantity', 0)}個")
                                with col4:
                                    order_total = result.get('price', 0) * result.get('quantity', 0)
                                    st.metric("合計", f"¥{order_total:,}")
                                    
                            else:
                                st.error("❌ 注文の作成に失敗しました。")
                    
                    except Exception as e:
                        st.error(f"❌ エラーが発生しました: {str(e)}")
                        
        except Exception as e:
            st.error(f"❌ データ読み込みエラー: {str(e)}")
    
    def _render_creation_history(self):
        """作成履歴の表示"""
        st.markdown("### 📋 作成履歴")
        
        # 顧客作成履歴
        if st.session_state.get('created_customers'):
            st.markdown("#### 👥 作成した顧客")
            
            import pandas as pd
            df_customers = pd.DataFrame(st.session_state.created_customers)
            
            # 表示用に整形
            display_cols = ["id", "name", "email", "city", "created_at"]
            df_display = df_customers[[col for col in display_cols if col in df_customers.columns]]
            df_display = df_display.rename(columns={
                "id": "ID",
                "name": "氏名",
                "email": "メール",
                "city": "都市",
                "created_at": "作成日時"
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # CSVダウンロード
            csv = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 顧客データをCSVダウンロード",
                data=csv,
                file_name=f"created_customers_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("まだ顧客を作成していません。")
        
        # 注文作成履歴
        if st.session_state.get('created_orders'):
            st.markdown("#### 🛒 作成した注文")
            
            df_orders = pd.DataFrame(st.session_state.created_orders)
            
            # 合計金額を計算
            if 'price' in df_orders.columns and 'quantity' in df_orders.columns:
                df_orders['total'] = df_orders['price'] * df_orders['quantity']
            
            # 表示用に整形
            display_cols = ["id", "customer_id", "product_name", "quantity", "price", "total", "created_at"]
            df_display = df_orders[[col for col in display_cols if col in df_orders.columns]]
            df_display = df_display.rename(columns={
                "id": "注文ID",
                "customer_id": "顧客ID",
                "product_name": "商品名",
                "quantity": "数量",
                "price": "単価",
                "total": "合計",
                "created_at": "作成日時"
            })
            
            # 金額をフォーマット
            for col in ["単価", "合計"]:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: f"¥{x:,}" if pd.notnull(x) else "")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # 統計情報
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("作成注文数", len(st.session_state.created_orders))
            with col2:
                if 'total' in df_orders.columns:
                    total_amount = df_orders['total'].sum()
                    st.metric("総売上", f"¥{total_amount:,}")
            with col3:
                if 'quantity' in df_orders.columns:
                    total_quantity = df_orders['quantity'].sum()
                    st.metric("総数量", f"{total_quantity}個")
            
            # CSVダウンロード
            csv = df_display.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 注文データをCSVダウンロード",
                data=csv,
                file_name=f"created_orders_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("まだ注文を作成していません。")
        
        # データクリアオプション
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 顧客履歴をクリア", help="作成した顧客の履歴を消去します"):
                st.session_state.created_customers = []
                st.success("顧客履歴をクリアしました。")
                st.rerun()
        
        with col2:
            if st.button("🗑️ 注文履歴をクリア", help="作成した注文の履歴を消去します"):
                st.session_state.created_orders = []
                st.success("注文履歴をクリアしました。")
                st.rerun()
    
    def _render_data_analysis_page(self):
        """データ分析ページの描画（デモ機能5）"""
        st.markdown("## 🐼 データ分析デモ")
        st.markdown("データベース内のデータを分析し、洞察を得るための高度な分析機能")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # タブで分析機能を分類
        tab1, tab2, tab3, tab4 = st.tabs(["📊 売上分析", "👥 顧客分析", "📈 トレンド分析", "🎯 相関分析"])
        
        with tab1:
            self._render_sales_analysis(client)
        
        with tab2:
            self._render_customer_analysis(client)
            
        with tab3:
            self._render_trend_analysis(client)
            
        with tab4:
            self._render_correlation_analysis(client)
    
    def _render_sales_analysis(self, client: MCPAPIClient):
        """売上分析タブの描画"""
        st.markdown("### 📊 売上データ分析")
        st.markdown("詳細な売上パターンと収益性の分析")
        
        try:
            # 売上統計データを取得
            with st.spinner("売上データを分析中..."):
                stats_data = client._make_request("GET", "/api/stats/sales")
                orders_data = client._make_request("GET", "/api/orders", params={"limit": 1000})
                
                if not stats_data or not orders_data:
                    st.warning("分析に必要なデータが取得できませんでした。")
                    return
                
                # データ前処理
                import pandas as pd
                import plotly.express as px
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                df_orders = pd.DataFrame(orders_data)
                if 'price' in df_orders.columns and 'quantity' in df_orders.columns:
                    df_orders['total_amount'] = df_orders['price'] * df_orders['quantity']
                
                # 基本統計
                col1, col2, col3, col4 = st.columns(4)
                
                total_sales = stats_data.get('total_sales', 0)
                total_orders = stats_data.get('total_orders', 0)
                avg_order_value = stats_data.get('avg_order_value', 0)
                
                with col1:
                    st.metric("💰 総売上", f"¥{total_sales:,.0f}")
                with col2:
                    st.metric("📦 注文数", f"{total_orders:,}件")
                with col3:
                    st.metric("📊 平均単価", f"¥{avg_order_value:,.0f}")
                with col4:
                    if total_orders > 0:
                        conversion_rate = (total_orders / 1000) * 100  # 仮想的な変換率
                        st.metric("📈 変換率", f"{conversion_rate:.1f}%")
                
                # 売上分布分析
                st.markdown("#### 💹 売上分布分析")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 注文金額分布
                    if 'total_amount' in df_orders.columns:
                        fig_dist = px.histogram(
                            df_orders,
                            x='total_amount',
                            nbins=20,
                            title="注文金額分布",
                            labels={'total_amount': '注文金額 (¥)', 'count': '注文数'},
                            color_discrete_sequence=['#1f77b4']
                        )
                        fig_dist.update_layout(height=350)
                        st.plotly_chart(fig_dist, use_container_width=True)
                
                with col2:
                    # 商品別売上分析
                    if 'product_name' in df_orders.columns and 'total_amount' in df_orders.columns:
                        product_sales = df_orders.groupby('product_name')['total_amount'].sum().sort_values(ascending=False).head(10)
                        
                        fig_products = px.bar(
                            x=product_sales.values,
                            y=product_sales.index,
                            orientation='h',
                            title="商品別売上TOP10",
                            labels={'x': '売上額 (¥)', 'y': '商品名'},
                            color=product_sales.values,
                            color_continuous_scale='viridis'
                        )
                        fig_products.update_layout(height=350)
                        st.plotly_chart(fig_products, use_container_width=True)
                
                # 時系列分析
                # 日付列の確認
                date_column = None
                for col in ['created_at', 'order_date', 'date']:
                    if col in df_orders.columns:
                        date_column = col
                        break
                
                if date_column:
                    st.markdown("#### 📅 時系列売上分析")
                    
                    # 日付を変換
                    try:
                        df_orders['order_date'] = pd.to_datetime(df_orders[date_column]).dt.date
                        daily_sales = df_orders.groupby('order_date').agg({
                            'total_amount': 'sum',
                            'id': 'count'
                        }).reset_index()
                        daily_sales.columns = ['date', 'daily_sales', 'order_count']
                    except:
                        # 日付変換に失敗した場合はスキップ
                        daily_sales = None
                    
                    # 時系列グラフ
                    fig_timeline = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=('日別売上推移', '日別注文数推移'),
                        vertical_spacing=0.12
                    )
                    
                    fig_timeline.add_trace(
                        go.Scatter(x=daily_sales['date'], y=daily_sales['daily_sales'],
                                 mode='lines+markers', name='売上額', line=dict(color='#1f77b4')),
                        row=1, col=1
                    )
                    
                    fig_timeline.add_trace(
                        go.Bar(x=daily_sales['date'], y=daily_sales['order_count'],
                              name='注文数', marker_color='#ff7f0e'),
                        row=2, col=1
                    )
                    
                    fig_timeline.update_layout(height=500, showlegend=True)
                    fig_timeline.update_xaxes(title_text="日付", row=2, col=1)
                    fig_timeline.update_yaxes(title_text="売上額 (¥)", row=1, col=1)
                    fig_timeline.update_yaxes(title_text="注文数", row=2, col=1)
                    
                    st.plotly_chart(fig_timeline, use_container_width=True)
                
                # パフォーマンス指標
                st.markdown("#### 📈 パフォーマンス指標")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # RFM分析（簡易版）
                    if 'customer_id' in df_orders.columns and 'total_amount' in df_orders.columns:
                        # 日付列の確認
                        date_column = None
                        for col in ['created_at', 'order_date', 'date']:
                            if col in df_orders.columns:
                                date_column = col
                                break
                        
                        if date_column:
                            customer_metrics = df_orders.groupby('customer_id').agg({
                                'total_amount': ['sum', 'mean', 'count'],
                                date_column: 'max'
                            }).round(2)
                            customer_metrics.columns = ['total_spent', 'avg_order', 'frequency', 'last_order']
                        else:
                            customer_metrics = df_orders.groupby('customer_id').agg({
                                'total_amount': ['sum', 'mean', 'count']
                            }).round(2)
                            customer_metrics.columns = ['total_spent', 'avg_order', 'frequency']
                        
                        customer_metrics = customer_metrics.reset_index()
                        
                        # 顧客セグメント分析
                        high_value = customer_metrics[customer_metrics['total_spent'] > customer_metrics['total_spent'].quantile(0.8)]
                        frequent_buyers = customer_metrics[customer_metrics['frequency'] > customer_metrics['frequency'].quantile(0.8)]
                        
                        st.markdown("**🎯 顧客セグメント分析**")
                        st.metric("💎 高価値顧客", f"{len(high_value)}人")
                        st.metric("🔄 常連顧客", f"{len(frequent_buyers)}人")
                        
                        if not customer_metrics.empty:
                            st.metric("👥 平均顧客価値", f"¥{customer_metrics['total_spent'].mean():,.0f}")
                
                with col2:
                    # 売上集中度分析
                    if 'total_amount' in df_orders.columns:
                        top_20_percent = int(len(df_orders) * 0.2)
                        df_sorted = df_orders.sort_values('total_amount', ascending=False)
                        top_20_sales = df_sorted.head(top_20_percent)['total_amount'].sum()
                        pareto_ratio = (top_20_sales / total_sales) * 100 if total_sales > 0 else 0
                        
                        st.markdown("**📊 パレート分析 (80/20ルール)**")
                        st.metric("🏆 上位20%の注文が占める売上", f"{pareto_ratio:.1f}%")
                        
                        # 季節性分析（月別）
                        if 'order_date' in df_orders.columns:
                            df_orders['month'] = pd.to_datetime(df_orders['created_at']).dt.month
                            monthly_sales = df_orders.groupby('month')['total_amount'].sum()
                            
                            peak_month = monthly_sales.idxmax()
                            peak_sales = monthly_sales.max()
                            
                            st.metric("📅 ピーク月", f"{peak_month}月")
                            st.metric("💰 ピーク月売上", f"¥{peak_sales:,.0f}")
                
                # CSV出力オプション
                st.markdown("#### 📥 分析データ出力")
                
                analysis_summary = {
                    "総売上": f"¥{total_sales:,.0f}",
                    "総注文数": f"{total_orders:,}件",
                    "平均注文額": f"¥{avg_order_value:,.0f}",
                    "分析日時": pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                summary_df = pd.DataFrame(list(analysis_summary.items()), columns=['指標', '値'])
                
                csv_data = summary_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📊 売上分析サマリーをダウンロード",
                    data=csv_data,
                    file_name=f"sales_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"❌ 売上分析でエラーが発生しました: {str(e)}")
            with st.expander("🔍 エラー詳細"):
                import traceback
                st.code(traceback.format_exc())
    
    def _render_customer_analysis(self, client: MCPAPIClient):
        """顧客分析タブの描画"""
        st.markdown("### 👥 顧客行動分析")
        st.markdown("顧客の購買パターンと行動特性の詳細分析")
        
        try:
            with st.spinner("顧客データを分析中..."):
                # データ取得
                customers_data = client._make_request("GET", "/api/customers", params={"limit": 1000})
                orders_data = client._make_request("GET", "/api/orders", params={"limit": 1000})
                
                if not customers_data or not orders_data:
                    st.warning("分析に必要なデータが取得できませんでした。")
                    return
                
                import pandas as pd
                import plotly.express as px
                import plotly.graph_objects as go
                
                df_customers = pd.DataFrame(customers_data)
                df_orders = pd.DataFrame(orders_data)
                
                if 'price' in df_orders.columns and 'quantity' in df_orders.columns:
                    df_orders['total_amount'] = df_orders['price'] * df_orders['quantity']
                
                # 顧客基本統計
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("👥 総顧客数", f"{len(df_customers):,}人")
                with col2:
                    if 'city' in df_customers.columns:
                        unique_cities = df_customers['city'].nunique()
                        st.metric("🏙️ 展開都市数", f"{unique_cities}都市")
                with col3:
                    if 'customer_id' in df_orders.columns:
                        active_customers = df_orders['customer_id'].nunique()
                        st.metric("🛒 購買経験者", f"{active_customers}人")
                with col4:
                    if active_customers > 0 and len(df_customers) > 0:
                        activation_rate = (active_customers / len(df_customers)) * 100
                        st.metric("📈 アクティブ率", f"{activation_rate:.1f}%")
                
                # 地域分析
                st.markdown("#### 🗺️ 地域別顧客分析")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 都市別顧客分布
                    if 'city' in df_customers.columns:
                        city_counts = df_customers['city'].value_counts()
                        
                        fig_city_dist = px.pie(
                            values=city_counts.values,
                            names=city_counts.index,
                            title="都市別顧客分布"
                        )
                        fig_city_dist.update_layout(height=350)
                        st.plotly_chart(fig_city_dist, use_container_width=True)
                
                with col2:
                    # 都市別購買力分析
                    if 'customer_id' in df_orders.columns and 'total_amount' in df_orders.columns:
                        # 顧客データと注文データをマージ
                        customer_orders = df_orders.merge(df_customers, left_on='customer_id', right_on='id', how='left')
                        
                        if 'city' in customer_orders.columns:
                            city_purchasing = customer_orders.groupby('city')['total_amount'].agg(['sum', 'mean', 'count']).reset_index()
                            city_purchasing.columns = ['city', 'total_sales', 'avg_order', 'order_count']
                            
                            fig_city_power = px.bar(
                                city_purchasing,
                                x='city',
                                y='total_sales',
                                title="都市別総購買力",
                                labels={'city': '都市', 'total_sales': '総購買額 (¥)'},
                                color='total_sales',
                                color_continuous_scale='viridis'
                            )
                            fig_city_power.update_layout(height=350)
                            st.plotly_chart(fig_city_power, use_container_width=True)
                
                # 顧客ライフサイクル分析
                st.markdown("#### 📊 顧客ライフサイクル分析")
                
                if 'customer_id' in df_orders.columns and 'created_at' in df_orders.columns:
                    # 顧客別購買履歴分析
                    customer_lifecycle = df_orders.groupby('customer_id').agg({
                        'total_amount': ['sum', 'mean', 'count'],
                        'created_at': ['min', 'max']
                    }).round(2)
                    
                    customer_lifecycle.columns = ['total_spent', 'avg_order_value', 'order_frequency', 'first_order', 'last_order']
                    customer_lifecycle = customer_lifecycle.reset_index()
                    
                    # 顧客価値分散
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 顧客価値分布
                        fig_value_dist = px.histogram(
                            customer_lifecycle,
                            x='total_spent',
                            nbins=20,
                            title="顧客生涯価値分布",
                            labels={'total_spent': '生涯価値 (¥)', 'count': '顧客数'},
                            color_discrete_sequence=['#2E86C1']
                        )
                        fig_value_dist.update_layout(height=350)
                        st.plotly_chart(fig_value_dist, use_container_width=True)
                    
                    with col2:
                        # 購買頻度分布
                        fig_freq_dist = px.histogram(
                            customer_lifecycle,
                            x='order_frequency',
                            nbins=15,
                            title="購買頻度分布",
                            labels={'order_frequency': '注文回数', 'count': '顧客数'},
                            color_discrete_sequence=['#E74C3C']
                        )
                        fig_freq_dist.update_layout(height=350)
                        st.plotly_chart(fig_freq_dist, use_container_width=True)
                    
                    # 顧客セグメンテーション
                    st.markdown("#### 🎯 顧客セグメンテーション")
                    
                    # RFM分析
                    today = pd.Timestamp.now()
                    customer_lifecycle['last_order'] = pd.to_datetime(customer_lifecycle['last_order'])
                    customer_lifecycle['recency'] = (today - customer_lifecycle['last_order']).dt.days
                    
                    # セグメント分類
                    high_value_threshold = customer_lifecycle['total_spent'].quantile(0.8)
                    high_freq_threshold = customer_lifecycle['order_frequency'].quantile(0.8)
                    recent_threshold = customer_lifecycle['recency'].quantile(0.2)  # 最近の20%
                    
                    customer_lifecycle['segment'] = 'Regular'
                    customer_lifecycle.loc[
                        (customer_lifecycle['total_spent'] >= high_value_threshold) &
                        (customer_lifecycle['order_frequency'] >= high_freq_threshold) &
                        (customer_lifecycle['recency'] <= recent_threshold), 'segment'
                    ] = 'VIP'
                    customer_lifecycle.loc[
                        (customer_lifecycle['total_spent'] >= high_value_threshold) &
                        (customer_lifecycle['recency'] <= recent_threshold), 'segment'
                    ] = 'High Value'
                    customer_lifecycle.loc[
                        (customer_lifecycle['order_frequency'] >= high_freq_threshold) &
                        (customer_lifecycle['recency'] <= recent_threshold), 'segment'
                    ] = 'Loyal'
                    customer_lifecycle.loc[
                        customer_lifecycle['recency'] > customer_lifecycle['recency'].quantile(0.8), 'segment'
                    ] = 'At Risk'
                    
                    # セグメント分布
                    segment_counts = customer_lifecycle['segment'].value_counts()
                    
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        fig_segments = px.pie(
                            values=segment_counts.values,
                            names=segment_counts.index,
                            title="顧客セグメント分布",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        fig_segments.update_layout(height=300)
                        st.plotly_chart(fig_segments, use_container_width=True)
                    
                    with col2:
                        st.markdown("**🏆 VIP顧客**")
                        vip_count = segment_counts.get('VIP', 0)
                        st.metric("人数", f"{vip_count}人")
                        if vip_count > 0:
                            vip_avg_value = customer_lifecycle[customer_lifecycle['segment'] == 'VIP']['total_spent'].mean()
                            st.metric("平均価値", f"¥{vip_avg_value:,.0f}")
                    
                    with col3:
                        st.markdown("**⚠️ リスク顧客**")
                        risk_count = segment_counts.get('At Risk', 0)
                        st.metric("人数", f"{risk_count}人")
                        if risk_count > 0:
                            risk_ratio = (risk_count / len(customer_lifecycle)) * 100
                            st.metric("割合", f"{risk_ratio:.1f}%")
                
                # コホート分析（簡易版）
                st.markdown("#### 📅 コホート分析")
                
                if 'created_at' in df_customers.columns:
                    df_customers['registration_month'] = pd.to_datetime(df_customers['created_at']).dt.to_period('M')
                    cohort_counts = df_customers['registration_month'].value_counts().sort_index()
                    
                    fig_cohort = px.bar(
                        x=cohort_counts.index.astype(str),
                        y=cohort_counts.values,
                        title="月別新規顧客登録数",
                        labels={'x': '登録月', 'y': '新規顧客数'},
                        color=cohort_counts.values,
                        color_continuous_scale='Blues'
                    )
                    fig_cohort.update_layout(height=300)
                    st.plotly_chart(fig_cohort, use_container_width=True)
                
                # データ出力
                st.markdown("#### 📥 顧客分析データ出力")
                
                if 'customer_lifecycle' in locals() and not customer_lifecycle.empty:
                    segment_summary = customer_lifecycle.groupby('segment').agg({
                        'total_spent': ['count', 'mean', 'sum'],
                        'avg_order_value': 'mean',
                        'order_frequency': 'mean'
                    }).round(2)
                    
                    csv_data = segment_summary.to_csv().encode('utf-8-sig')
                    st.download_button(
                        label="👥 顧客セグメント分析をダウンロード",
                        data=csv_data,
                        file_name=f"customer_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                
        except Exception as e:
            st.error(f"❌ 顧客分析でエラーが発生しました: {str(e)}")
            with st.expander("🔍 エラー詳細"):
                import traceback
                st.code(traceback.format_exc())
    
    def _render_trend_analysis(self, client: MCPAPIClient):
        """トレンド分析タブの描画"""
        st.markdown("### 📈 トレンド分析")
        st.markdown("時系列データから読み取るビジネストレンドと予測")
        
        try:
            with st.spinner("トレンドデータを分析中..."):
                # データ取得
                orders_data = client._make_request("GET", "/api/orders", params={"limit": 1000})
                customers_data = client._make_request("GET", "/api/customers", params={"limit": 1000})
                
                if not orders_data:
                    st.warning("分析に必要な注文データが取得できませんでした。")
                    return
                
                import pandas as pd
                import plotly.express as px
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                import numpy as np
                
                df_orders = pd.DataFrame(orders_data)
                if 'price' in df_orders.columns and 'quantity' in df_orders.columns:
                    df_orders['total_amount'] = df_orders['price'] * df_orders['quantity']
                
                # 日付処理
                df_orders['created_at'] = pd.to_datetime(df_orders['created_at'])
                df_orders['date'] = df_orders['created_at'].dt.date
                df_orders['hour'] = df_orders['created_at'].dt.hour
                df_orders['day_of_week'] = df_orders['created_at'].dt.day_name()
                df_orders['month'] = df_orders['created_at'].dt.month
                
                # 基本トレンド指標
                col1, col2, col3, col4 = st.columns(4)
                
                # 日別統計
                daily_stats = df_orders.groupby('date').agg({
                    'total_amount': 'sum',
                    'id': 'count'
                }).reset_index()
                
                with col1:
                    if not daily_stats.empty:
                        avg_daily_sales = daily_stats['total_amount'].mean()
                        st.metric("📊 日次平均売上", f"¥{avg_daily_sales:,.0f}")
                
                with col2:
                    if not daily_stats.empty:
                        avg_daily_orders = daily_stats['id'].mean()
                        st.metric("📦 日次平均注文", f"{avg_daily_orders:.1f}件")
                
                with col3:
                    if len(daily_stats) >= 2:
                        # 成長率計算（直近vs最初）
                        recent_avg = daily_stats.tail(3)['total_amount'].mean()
                        initial_avg = daily_stats.head(3)['total_amount'].mean()
                        growth_rate = ((recent_avg - initial_avg) / initial_avg * 100) if initial_avg > 0 else 0
                        st.metric("📈 売上成長率", f"{growth_rate:+.1f}%")
                
                with col4:
                    if 'product_name' in df_orders.columns:
                        unique_products = df_orders['product_name'].nunique()
                        st.metric("🛍️ 商品多様性", f"{unique_products}種類")
                
                # 時系列トレンド分析
                st.markdown("#### 📅 時系列売上トレンド")
                
                if len(daily_stats) > 1:
                    # 移動平均の計算
                    daily_stats['ma_3'] = daily_stats['total_amount'].rolling(window=3, min_periods=1).mean()
                    daily_stats['ma_7'] = daily_stats['total_amount'].rolling(window=7, min_periods=1).mean()
                    
                    # トレンドライン
                    fig_trend = go.Figure()
                    
                    # 実データ
                    fig_trend.add_trace(go.Scatter(
                        x=daily_stats['date'],
                        y=daily_stats['total_amount'],
                        mode='lines+markers',
                        name='実績売上',
                        line=dict(color='#1f77b4', width=2),
                        marker=dict(size=6)
                    ))
                    
                    # 3日移動平均
                    fig_trend.add_trace(go.Scatter(
                        x=daily_stats['date'],
                        y=daily_stats['ma_3'],
                        mode='lines',
                        name='3日移動平均',
                        line=dict(color='#ff7f0e', width=2, dash='dash')
                    ))
                    
                    # 7日移動平均
                    if len(daily_stats) >= 7:
                        fig_trend.add_trace(go.Scatter(
                            x=daily_stats['date'],
                            y=daily_stats['ma_7'],
                            mode='lines',
                            name='7日移動平均',
                            line=dict(color='#2ca02c', width=3)
                        ))
                    
                    fig_trend.update_layout(
                        title="日次売上トレンドと移動平均",
                        xaxis_title="日付",
                        yaxis_title="売上額 (¥)",
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_trend, use_container_width=True)
                
                # パターン分析
                st.markdown("#### 🔄 売上パターン分析")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 曜日別パターン
                    if 'day_of_week' in df_orders.columns:
                        dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        dow_stats = df_orders.groupby('day_of_week')['total_amount'].sum().reindex(dow_order)
                        
                        fig_dow = px.bar(
                            x=['月', '火', '水', '木', '金', '土', '日'],
                            y=dow_stats.values,
                            title="曜日別売上パターン",
                            labels={'x': '曜日', 'y': '売上額 (¥)'},
                            color=dow_stats.values,
                            color_continuous_scale='viridis'
                        )
                        fig_dow.update_layout(height=350)
                        st.plotly_chart(fig_dow, use_container_width=True)
                
                with col2:
                    # 時間帯別パターン
                    if 'hour' in df_orders.columns:
                        hourly_stats = df_orders.groupby('hour')['total_amount'].sum()
                        
                        fig_hourly = px.line(
                            x=hourly_stats.index,
                            y=hourly_stats.values,
                            title="時間帯別売上パターン",
                            labels={'x': '時間', 'y': '売上額 (¥)'},
                            markers=True
                        )
                        fig_hourly.update_layout(height=350)
                        st.plotly_chart(fig_hourly, use_container_width=True)
                
                # 商品トレンド分析
                st.markdown("#### 🏆 商品別トレンド分析")
                
                if 'product_name' in df_orders.columns:
                    # 商品別日次売上
                    product_daily = df_orders.groupby(['date', 'product_name'])['total_amount'].sum().reset_index()
                    
                    # 上位5商品の取得
                    top_products = df_orders.groupby('product_name')['total_amount'].sum().sort_values(ascending=False).head(5)
                    
                    # 上位商品のトレンド
                    fig_product_trend = go.Figure()
                    
                    colors = px.colors.qualitative.Set1
                    for i, product in enumerate(top_products.index):
                        product_data = product_daily[product_daily['product_name'] == product]
                        
                        fig_product_trend.add_trace(go.Scatter(
                            x=product_data['date'],
                            y=product_data['total_amount'],
                            mode='lines+markers',
                            name=product,
                            line=dict(color=colors[i % len(colors)], width=2),
                            marker=dict(size=6)
                        ))
                    
                    fig_product_trend.update_layout(
                        title="上位5商品の売上トレンド",
                        xaxis_title="日付",
                        yaxis_title="売上額 (¥)",
                        height=400,
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_product_trend, use_container_width=True)
                
                # 予測分析（簡易版）
                st.markdown("#### 🔮 簡易予測分析")
                
                if len(daily_stats) >= 5:
                    # 線形回帰による簡易予測
                    from sklearn.linear_model import LinearRegression
                    import warnings
                    warnings.filterwarnings('ignore')
                    
                    # 過去データで予測モデル作成
                    X = np.arange(len(daily_stats)).reshape(-1, 1)
                    y = daily_stats['total_amount'].values
                    
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    # 未来3日間を予測
                    future_days = 3
                    future_X = np.arange(len(daily_stats), len(daily_stats) + future_days).reshape(-1, 1)
                    future_predictions = model.predict(future_X)
                    
                    # 予測日付
                    last_date = daily_stats['date'].max()
                    future_dates = [last_date + pd.Timedelta(days=i+1) for i in range(future_days)]
                    
                    col1, col2, col3 = st.columns(3)
                    
                    for i, (date, pred) in enumerate(zip(future_dates, future_predictions)):
                        with [col1, col2, col3][i]:
                            st.metric(
                                f"📅 {date.strftime('%m/%d')} 予測",
                                f"¥{max(0, pred):,.0f}",
                                delta=f"{((pred - daily_stats['total_amount'].mean()) / daily_stats['total_amount'].mean() * 100):+.1f}%"
                            )
                    
                    # R²スコア
                    from sklearn.metrics import r2_score
                    r2 = r2_score(y, model.predict(X))
                    st.caption(f"📊 予測精度 (R²): {r2:.3f}")
                    
                    # 予測グラフ
                    fig_prediction = go.Figure()
                    
                    # 実績データ
                    fig_prediction.add_trace(go.Scatter(
                        x=daily_stats['date'],
                        y=daily_stats['total_amount'],
                        mode='lines+markers',
                        name='実績',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    
                    # 予測データ
                    fig_prediction.add_trace(go.Scatter(
                        x=future_dates,
                        y=future_predictions,
                        mode='lines+markers',
                        name='予測',
                        line=dict(color='#ff7f0e', width=2, dash='dash'),
                        marker=dict(size=8, symbol='diamond')
                    ))
                    
                    fig_prediction.update_layout(
                        title="売上予測（線形回帰）",
                        xaxis_title="日付",
                        yaxis_title="売上額 (¥)",
                        height=350
                    )
                    
                    st.plotly_chart(fig_prediction, use_container_width=True)
                
                # トレンド分析サマリー
                st.markdown("#### 📋 トレンド分析サマリー")
                
                insights = []
                
                if not daily_stats.empty:
                    # 最高売上日
                    best_day = daily_stats.loc[daily_stats['total_amount'].idxmax()]
                    insights.append(f"📈 最高売上日: {best_day['date']} (¥{best_day['total_amount']:,.0f})")
                    
                    # 売上変動
                    volatility = daily_stats['total_amount'].std() / daily_stats['total_amount'].mean()
                    insights.append(f"📊 売上変動係数: {volatility:.2f} ({'高変動' if volatility > 0.3 else '低変動' if volatility < 0.1 else '中変動'})")
                
                if 'day_of_week' in df_orders.columns:
                    best_dow = df_orders.groupby('day_of_week')['total_amount'].sum().idxmax()
                    dow_map = {'Monday': '月曜', 'Tuesday': '火曜', 'Wednesday': '水曜', 'Thursday': '木曜', 
                              'Friday': '金曜', 'Saturday': '土曜', 'Sunday': '日曜'}
                    insights.append(f"🗓️ 最も売上の高い曜日: {dow_map.get(best_dow, best_dow)}")
                
                for insight in insights:
                    st.info(insight)
                
                # データ出力
                st.markdown("#### 📥 トレンド分析データ出力")
                
                if not daily_stats.empty:
                    csv_data = daily_stats.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📈 日次売上トレンドをダウンロード",
                        data=csv_data,
                        file_name=f"sales_trend_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                
        except Exception as e:
            st.error(f"❌ トレンド分析でエラーが発生しました: {str(e)}")
            with st.expander("🔍 エラー詳細"):
                import traceback
                st.code(traceback.format_exc())
    
    def _render_correlation_analysis(self, client: MCPAPIClient):
        """相関分析タブの描画"""
        st.markdown("### 🎯 相関分析")
        st.markdown("変数間の関係性と影響度の統計的分析")
        
        try:
            with st.spinner("相関データを分析中..."):
                # データ取得
                orders_data = client._make_request("GET", "/api/orders", params={"limit": 1000})
                customers_data = client._make_request("GET", "/api/customers", params={"limit": 1000})
                
                if not orders_data or not customers_data:
                    st.warning("分析に必要なデータが取得できませんでした。")
                    return
                
                import pandas as pd
                import plotly.express as px
                import plotly.graph_objects as go
                import numpy as np
                import seaborn as sns
                import matplotlib.pyplot as plt
                
                df_orders = pd.DataFrame(orders_data)
                df_customers = pd.DataFrame(customers_data)
                
                if 'price' in df_orders.columns and 'quantity' in df_orders.columns:
                    df_orders['total_amount'] = df_orders['price'] * df_orders['quantity']
                
                # データ結合
                merged_data = df_orders.merge(df_customers, left_on='customer_id', right_on='id', how='left', suffixes=('_order', '_customer'))
                
                # 相関分析用の数値データ準備
                correlation_vars = []
                
                if 'price' in merged_data.columns:
                    correlation_vars.append('price')
                if 'quantity' in merged_data.columns:
                    correlation_vars.append('quantity')
                if 'total_amount' in merged_data.columns:
                    correlation_vars.append('total_amount')
                
                # 顧客別集計データ作成
                customer_metrics = merged_data.groupby('customer_id').agg({
                    'total_amount': ['sum', 'mean', 'count'],
                    'quantity': ['sum', 'mean'],
                    'price': ['mean', 'max', 'min']
                }).round(2)
                
                customer_metrics.columns = [
                    'total_spent', 'avg_order_value', 'order_frequency',
                    'total_quantity', 'avg_quantity',
                    'avg_price', 'max_price', 'min_price'
                ]
                customer_metrics = customer_metrics.reset_index()
                
                # 基本相関統計
                col1, col2, col3, col4 = st.columns(4)
                
                if len(customer_metrics) > 1:
                    # 相関係数計算
                    corr_total_freq = customer_metrics['total_spent'].corr(customer_metrics['order_frequency'])
                    corr_avg_freq = customer_metrics['avg_order_value'].corr(customer_metrics['order_frequency'])
                    corr_price_quantity = merged_data['price'].corr(merged_data['quantity']) if 'price' in merged_data.columns and 'quantity' in merged_data.columns else 0
                    
                    with col1:
                        st.metric("📊 支出×頻度相関", f"{corr_total_freq:.3f}")
                    with col2:
                        st.metric("💰 単価×頻度相関", f"{corr_avg_freq:.3f}")
                    with col3:
                        st.metric("🔄 価格×数量相関", f"{corr_price_quantity:.3f}")
                    with col4:
                        # 相関の強さを評価
                        avg_correlation = abs(np.mean([corr_total_freq, corr_avg_freq, corr_price_quantity]))
                        correlation_strength = "強" if avg_correlation > 0.7 else "中" if avg_correlation > 0.3 else "弱"
                        st.metric("🎯 平均相関強度", correlation_strength)
                
                # 相関行列の可視化
                st.markdown("#### 🔍 相関行列ヒートマップ")
                
                if len(customer_metrics) > 5:  # 十分なデータがある場合
                    # 相関行列計算
                    correlation_matrix = customer_metrics.select_dtypes(include=[np.number]).corr()
                    
                    # ヒートマップ作成
                    fig_heatmap = px.imshow(
                        correlation_matrix,
                        x=correlation_matrix.columns,
                        y=correlation_matrix.columns,
                        color_continuous_scale='RdBu_r',
                        aspect='auto',
                        title="顧客メトリクス相関行列"
                    )
                    
                    # 相関値をテキストで表示
                    fig_heatmap.update_traces(
                        text=correlation_matrix.round(3),
                        texttemplate="%{text}",
                        textfont={"size": 10}
                    )
                    
                    fig_heatmap.update_layout(height=500)
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # 散布図分析
                st.markdown("#### 📈 変数間散布図分析")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # 支出 vs 頻度
                    if len(customer_metrics) > 1:
                        fig_scatter1 = px.scatter(
                            customer_metrics,
                            x='order_frequency',
                            y='total_spent',
                            title="注文頻度 vs 総支出額",
                            labels={'order_frequency': '注文回数', 'total_spent': '総支出額 (¥)'},
                            trendline='ols',
                            color='avg_order_value',
                            size='total_quantity',
                            hover_data=['customer_id']
                        )
                        fig_scatter1.update_layout(height=400)
                        st.plotly_chart(fig_scatter1, use_container_width=True)
                
                with col2:
                    # 平均単価 vs 数量
                    if len(customer_metrics) > 1:
                        fig_scatter2 = px.scatter(
                            customer_metrics,
                            x='avg_quantity',
                            y='avg_price',
                            title="平均購入数量 vs 平均単価",
                            labels={'avg_quantity': '平均購入数量', 'avg_price': '平均単価 (¥)'},
                            trendline='ols',
                            color='total_spent',
                            size='order_frequency',
                            hover_data=['customer_id']
                        )
                        fig_scatter2.update_layout(height=400)
                        st.plotly_chart(fig_scatter2, use_container_width=True)
                
                # 地域別相関分析
                if 'city' in merged_data.columns:
                    st.markdown("#### 🏙️ 地域別相関分析")
                    
                    city_analysis = merged_data.groupby('city_customer').agg({
                        'total_amount': ['sum', 'mean', 'count'],
                        'quantity': 'mean',
                        'price': 'mean'
                    }).round(2)
                    
                    city_analysis.columns = ['total_sales', 'avg_order_value', 'order_count', 'avg_quantity', 'avg_price']
                    city_analysis = city_analysis.reset_index()
                    
                    if len(city_analysis) > 1:
                        # 都市別バブルチャート
                        fig_bubble = px.scatter(
                            city_analysis,
                            x='avg_order_value',
                            y='avg_quantity',
                            size='total_sales',
                            color='order_count',
                            hover_name='city_customer',
                            title="都市別：平均注文額 vs 平均数量（バブルサイズ=総売上）",
                            labels={
                                'avg_order_value': '平均注文額 (¥)',
                                'avg_quantity': '平均購入数量',
                                'total_sales': '総売上',
                                'order_count': '注文数'
                            }
                        )
                        fig_bubble.update_layout(height=400)
                        st.plotly_chart(fig_bubble, use_container_width=True)
                
                # 商品別相関分析
                if 'product_name' in merged_data.columns:
                    st.markdown("#### 🛍️ 商品別相関分析")
                    
                    product_analysis = merged_data.groupby('product_name').agg({
                        'total_amount': ['sum', 'mean', 'count'],
                        'quantity': ['sum', 'mean'],
                        'price': ['mean', 'std']
                    }).round(2)
                    
                    product_analysis.columns = ['total_sales', 'avg_order_value', 'order_count', 'total_quantity', 'avg_quantity', 'avg_price', 'price_std']
                    product_analysis = product_analysis.reset_index()
                    
                    # 上位10商品で分析
                    top_products = product_analysis.nlargest(10, 'total_sales')
                    
                    if len(top_products) > 1:
                        fig_product_corr = px.scatter(
                            top_products,
                            x='avg_price',
                            y='total_quantity',
                            size='total_sales',
                            color='order_count',
                            hover_name='product_name',
                            title="商品別：平均価格 vs 総販売数量（上位10商品）",
                            labels={
                                'avg_price': '平均価格 (¥)',
                                'total_quantity': '総販売数量',
                                'total_sales': '総売上',
                                'order_count': '注文回数'
                            }
                        )
                        fig_product_corr.update_layout(height=400)
                        st.plotly_chart(fig_product_corr, use_container_width=True)
                
                # 統計的有意性テスト
                st.markdown("#### 📊 統計的有意性分析")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # ピアソン相関係数の有意性テスト
                    if len(customer_metrics) > 5:
                        from scipy.stats import pearsonr
                        
                        correlations = []
                        
                        # 主要な相関ペア
                        pairs = [
                            ('total_spent', 'order_frequency', '総支出×注文頻度'),
                            ('avg_order_value', 'avg_quantity', '平均単価×平均数量'),
                            ('total_spent', 'avg_order_value', '総支出×平均単価')
                        ]
                        
                        for var1, var2, label in pairs:
                            if var1 in customer_metrics.columns and var2 in customer_metrics.columns:
                                corr, p_value = pearsonr(customer_metrics[var1], customer_metrics[var2])
                                significance = "有意" if p_value < 0.05 else "非有意"
                                correlations.append({
                                    '変数ペア': label,
                                    '相関係数': f"{corr:.3f}",
                                    'p値': f"{p_value:.3f}",
                                    '有意性': significance
                                })
                        
                        if correlations:
                            df_correlations = pd.DataFrame(correlations)
                            st.dataframe(df_correlations, use_container_width=True, hide_index=True)
                
                with col2:
                    # 相関の解釈
                    st.markdown("**🔍 相関の解釈ガイド**")
                    st.markdown("""
                    - **|r| > 0.7**: 強い相関
                    - **0.3 < |r| ≤ 0.7**: 中程度の相関
                    - **|r| ≤ 0.3**: 弱い相関
                    
                    **統計的有意性**
                    - **p < 0.05**: 統計的に有意
                    - **p ≥ 0.05**: 統計的に非有意
                    """)
                
                # ビジネス洞察
                st.markdown("#### 💡 ビジネス洞察")
                
                insights = []
                
                if len(customer_metrics) > 1:
                    # 最も強い正の相関
                    corr_matrix = customer_metrics.select_dtypes(include=[np.number]).corr()
                    # 対角成分（自己相関）を除外
                    corr_matrix = corr_matrix.where(~np.eye(corr_matrix.shape[0], dtype=bool))
                    
                    max_corr = corr_matrix.max().max()
                    max_corr_pair = corr_matrix.stack().idxmax()
                    
                    if not pd.isna(max_corr):
                        insights.append(f"📈 最強の正の相関: {max_corr_pair[0]} と {max_corr_pair[1]} (r={max_corr:.3f})")
                    
                    # 顧客セグメンテーションの提案
                    high_freq_customers = customer_metrics[customer_metrics['order_frequency'] > customer_metrics['order_frequency'].quantile(0.8)]
                    high_value_customers = customer_metrics[customer_metrics['total_spent'] > customer_metrics['total_spent'].quantile(0.8)]
                    
                    overlap = len(set(high_freq_customers['customer_id']) & set(high_value_customers['customer_id']))
                    overlap_ratio = overlap / len(high_freq_customers) if len(high_freq_customers) > 0 else 0
                    
                    insights.append(f"🎯 高頻度顧客と高価値顧客の重複率: {overlap_ratio:.1%}")
                    
                    if overlap_ratio > 0.7:
                        insights.append("💡 提案: 頻度向上施策が売上向上に直結する可能性が高い")
                    elif overlap_ratio < 0.3:
                        insights.append("💡 提案: 高頻度顧客の単価向上施策を検討")
                
                for insight in insights:
                    st.info(insight)
                
                # データ出力
                st.markdown("#### 📥 相関分析データ出力")
                
                if len(customer_metrics) > 1:
                    # 相関行列のCSV出力
                    correlation_csv = correlation_matrix.to_csv().encode('utf-8-sig')
                    st.download_button(
                        label="🔗 相関行列をダウンロード",
                        data=correlation_csv,
                        file_name=f"correlation_matrix_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
                
        except Exception as e:
            st.error(f"❌ 相関分析でエラーが発生しました: {str(e)}")
            with st.expander("🔍 エラー詳細"):
                import traceback
                st.code(traceback.format_exc())
    
    def _render_error_handling_page(self):
        """エラーハンドリングページの描画（デモ機能6）"""
        st.markdown("## 🚨 エラーテストデモ")
        st.markdown("APIエラーハンドリングとシステムの堅牢性を検証するテスト機能")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # タブでエラーテストを分類
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 基本エラーテスト", "📝 データ投入エラー", "🌐 ネットワークエラー", "📊 エラー履歴"])
        
        with tab1:
            self._render_basic_error_tests(client)
        
        with tab2:
            self._render_data_error_tests(client)
            
        with tab3:
            self._render_network_error_tests(client)
            
        with tab4:
            self._render_error_history()
    
    def _render_basic_error_tests(self, client: MCPAPIClient):
        """基本的なエラーテスト"""
        st.markdown("### 🔍 基本エラーテスト")
        st.markdown("一般的なAPIエラーを意図的に発生させてハンドリングを確認")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 404 エラーテスト")
            if st.button("存在しない顧客を取得", key="test_404_customer"):
                with st.spinner("エラーテスト実行中..."):
                    try:
                        result = client._make_request("GET", "/api/customers/99999")
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "404" in error_msg:
                            st.success("✅ 404エラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("404エラー", "顧客取得", "成功", error_msg)
                        else:
                            st.error(f"❌ 予期しないエラー: {error_msg}")
            
            if st.button("存在しない商品を取得", key="test_404_product"):
                with st.spinner("エラーテスト実行中..."):
                    try:
                        result = client._make_request("GET", "/api/products/99999")
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "404" in error_msg:
                            st.success("✅ 404エラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("404エラー", "商品取得", "成功", error_msg)
                        else:
                            st.error(f"❌ 予期しないエラー: {error_msg}")
        
        with col2:
            st.markdown("#### 400/422 エラーテスト")
            if st.button("無効なデータで顧客作成", key="test_422_customer"):
                with st.spinner("エラーテスト実行中..."):
                    try:
                        # 無効なメールアドレスでテスト
                        invalid_data = {
                            "name": "",  # 空の名前
                            "email": "invalid-email",  # 無効なメール
                            "city": ""  # 空の都市
                        }
                        result = client._make_request("POST", "/api/customers", json=invalid_data)
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "422" in error_msg or "400" in error_msg:
                            st.success("✅ バリデーションエラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("422エラー", "顧客作成", "成功", error_msg)
                        else:
                            st.error(f"❌ 予期しないエラー: {error_msg}")
            
            if st.button("重複メールで顧客作成", key="test_duplicate_email"):
                with st.spinner("エラーテスト実行中..."):
                    try:
                        # 既存のメールアドレスでテスト
                        duplicate_data = {
                            "name": "テストユーザー",
                            "email": "yamada@example.com",  # 既存のメール
                            "city": "東京"
                        }
                        result = client._make_request("POST", "/api/customers", json=duplicate_data)
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "422" in error_msg:
                            st.success("✅ 重複メールエラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("重複エラー", "顧客作成", "成功", error_msg)
                        else:
                            st.error(f"❌ 予期しないエラー: {error_msg}")
    
    def _render_data_error_tests(self, client: MCPAPIClient):
        """データ投入関連のエラーテスト"""
        st.markdown("### 📝 データ投入エラーテスト")
        st.markdown("不正なデータ形式や制約違反のテスト")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 注文データエラー")
            if st.button("存在しない顧客で注文作成", key="test_invalid_customer_order"):
                with st.spinner("エラーテスト実行中..."):
                    try:
                        invalid_order = {
                            "customer_id": 99999,  # 存在しない顧客ID
                            "product_name": "テスト商品",
                            "quantity": 1,
                            "price": 1000
                        }
                        result = client._make_request("POST", "/api/orders", json=invalid_order)
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "404" in error_msg:
                            st.success("✅ 存在しない顧客エラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("外部キーエラー", "注文作成", "成功", error_msg)
                        else:
                            st.error(f"❌ 予期しないエラー: {error_msg}")
            
            if st.button("負の値で注文作成", key="test_negative_order"):
                with st.spinner("エラーテスト実行中..."):
                    try:
                        negative_order = {
                            "customer_id": 1,
                            "product_name": "テスト商品",
                            "quantity": -5,  # 負の数量
                            "price": -1000   # 負の価格
                        }
                        result = client._make_request("POST", "/api/orders", json=negative_order)
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "422" in error_msg or "400" in error_msg:
                            st.success("✅ 負の値エラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("バリデーションエラー", "注文作成", "成功", error_msg)
                        else:
                            st.warning(f"⚠️ エラーが検出されませんでした（API仕様要確認）: {error_msg}")
        
        with col2:
            st.markdown("#### 大量データエラー")
            if st.button("大量データで負荷テスト", key="test_bulk_data"):
                with st.spinner("大量データテスト実行中..."):
                    try:
                        # 100個の顧客データを一度に作成試行
                        success_count = 0
                        error_count = 0
                        
                        for i in range(10):  # 簡略化して10件
                            try:
                                bulk_customer = {
                                    "name": f"テストユーザー{i}",
                                    "email": f"bulk_test_{i}@example.com",
                                    "city": "東京"
                                }
                                result = client._make_request("POST", "/api/customers", json=bulk_customer)
                                success_count += 1
                            except Exception:
                                error_count += 1
                        
                        st.success(f"✅ 大量データテスト完了")
                        st.metric("成功", success_count)
                        st.metric("エラー", error_count)
                        self._log_error_test("大量データ", "顧客作成", f"成功{success_count}/エラー{error_count}", "")
                        
                    except Exception as e:
                        st.error(f"❌ 大量データテスト失敗: {str(e)}")
            
            if st.button("長すぎる文字列でテスト", key="test_long_string"):
                with st.spinner("長文字列テスト実行中..."):
                    try:
                        long_string_data = {
                            "name": "A" * 1000,  # 1000文字の名前
                            "email": f"{'a' * 100}@{'b' * 100}.com",  # 長いメール
                            "city": "C" * 500  # 500文字の都市名
                        }
                        result = client._make_request("POST", "/api/customers", json=long_string_data)
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "422" in error_msg or "400" in error_msg:
                            st.success("✅ 長文字列エラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg[:200]}...")
                            self._log_error_test("文字列長エラー", "顧客作成", "成功", error_msg)
                        else:
                            st.warning(f"⚠️ エラーが検出されませんでした: {error_msg}")
    
    def _render_network_error_tests(self, client: MCPAPIClient):
        """ネットワーク関連のエラーテスト"""
        st.markdown("### 🌐 ネットワークエラーテスト")
        st.markdown("接続エラーやタイムアウトのシミュレーション")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 存在しないエンドポイント")
            if st.button("無効なURLでアクセス", key="test_invalid_url"):
                with st.spinner("無効URLテスト実行中..."):
                    try:
                        result = client._make_request("GET", "/api/nonexistent")
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "404" in error_msg:
                            st.success("✅ 無効URLエラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("URLエラー", "アクセス", "成功", error_msg)
                        else:
                            st.error(f"❌ 予期しないエラー: {error_msg}")
            
            if st.button("無効なHTTPメソッド", key="test_invalid_method"):
                with st.spinner("無効メソッドテスト実行中..."):
                    try:
                        # DELETEメソッドでcustomersにアクセス（未サポート）
                        result = client._make_request("DELETE", "/api/customers")
                        st.success(f"予期しない成功: {result}")
                    except Exception as e:
                        error_msg = str(e)
                        if "405" in error_msg or "404" in error_msg:
                            st.success("✅ 無効メソッドエラーが正常にハンドリングされました")
                            st.code(f"エラー詳細: {error_msg}")
                            self._log_error_test("メソッドエラー", "アクセス", "成功", error_msg)
                        else:
                            st.error(f"❌ 予期しないエラー: {error_msg}")
        
        with col2:
            st.markdown("#### サーバー状態テスト")
            if st.button("ヘルスチェック確認", key="test_health_check"):
                with st.spinner("ヘルスチェック実行中..."):
                    try:
                        result = client.check_health()
                        if result:
                            st.success("✅ サーバーは正常に動作しています")
                            self._log_error_test("ヘルスチェック", "サーバー状態", "正常", "")
                        else:
                            st.error("❌ サーバーに問題があります")
                            self._log_error_test("ヘルスチェック", "サーバー状態", "異常", "")
                    except Exception as e:
                        st.error(f"❌ ヘルスチェック失敗: {str(e)}")
                        self._log_error_test("ヘルスチェック", "サーバー状態", "エラー", str(e))
            
            st.markdown("#### 接続テスト")
            if st.button("APIベースURL確認", key="test_base_url"):
                st.info(f"**現在のAPIベースURL**: {client.base_url}")
                st.info(f"**アクセス可能**: {'✅' if st.session_state.api_connected else '❌'}")
    
    def _render_error_history(self):
        """エラーテスト履歴の表示"""
        st.markdown("### 📊 エラーテスト履歴")
        
        if 'error_test_history' in st.session_state and st.session_state.error_test_history:
            import pandas as pd
            
            df = pd.DataFrame(st.session_state.error_test_history)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 最新順にソート
            df = df.sort_values('timestamp', ascending=False)
            
            # テーブル表示
            st.dataframe(
                df.rename(columns={
                    'timestamp': '実行時刻',
                    'error_type': 'エラー種別',
                    'test_case': 'テストケース',
                    'result': '結果',
                    'details': '詳細'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # 統計情報
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("総テスト数", len(df))
            with col2:
                success_count = len(df[df['result'].str.contains('成功')])
                st.metric("成功テスト", success_count)
            with col3:
                error_count = len(df) - success_count
                st.metric("エラー検出", error_count)
            
            # CSVダウンロード
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 エラーテスト履歴をCSVダウンロード",
                data=csv,
                file_name=f"error_test_history_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
            # 履歴クリア
            if st.button("🗑️ 履歴をクリア"):
                st.session_state.error_test_history = []
                st.success("エラーテスト履歴をクリアしました。")
                st.rerun()
        else:
            st.info("エラーテスト履歴がありません。上記のテストを実行してください。")
    
    def _log_error_test(self, error_type: str, test_case: str, result: str, details: str):
        """エラーテスト結果をログに記録"""
        if 'error_test_history' not in st.session_state:
            st.session_state.error_test_history = []
        
        import datetime
        log_entry = {
            'timestamp': datetime.datetime.now(),
            'error_type': error_type,
            'test_case': test_case,
            'result': result,
            'details': details[:100] + "..." if len(details) > 100 else details
        }
        
        st.session_state.error_test_history.append(log_entry)
    
    def _render_performance_page(self):
        """パフォーマンスページの描画（デモ機能7）"""
        st.markdown("## ⚡ パフォーマンステストデモ")
        st.markdown("API応答時間とスループットの測定・分析")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # タブで機能を分割
        tab1, tab2, tab3, tab4 = st.tabs(["🚀 リアルタイム測定", "📊 負荷テスト", "📈 パフォーマンス分析", "📋 測定履歴"])
        
        with tab1:
            self._render_realtime_performance(client)
        
        with tab2:
            self._render_load_testing(client)
            
        with tab3:
            self._render_performance_analysis(client)
            
        with tab4:
            self._render_performance_history()
    
    def _render_realtime_performance(self, client: MCPAPIClient):
        """リアルタイムパフォーマンス測定"""
        st.markdown("### 🚀 リアルタイムAPI応答時間測定")
        st.markdown("各APIエンドポイントの応答時間をリアルタイムで測定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### API エンドポイント選択")
            endpoint_options = {
                "ヘルスチェック": "/health",
                "顧客一覧": "/api/customers?limit=10",
                "商品一覧": "/api/products?limit=10", 
                "注文一覧": "/api/orders?limit=10",
                "売上統計": "/api/stats/sales"
            }
            
            selected_endpoint = st.selectbox(
                "📡 測定対象エンドポイント",
                list(endpoint_options.keys()),
                key="performance_endpoint"
            )
            
            measurement_count = st.number_input(
                "🔢 測定回数", 
                min_value=1, 
                max_value=50, 
                value=10,
                key="measurement_count"
            )
            
            if st.button("⏱️ 応答時間測定開始", key="start_realtime_test"):
                endpoint_url = endpoint_options[selected_endpoint]
                self._run_response_time_test(client, endpoint_url, selected_endpoint, measurement_count)
        
        with col2:
            st.markdown("#### 自動継続測定")
            
            auto_test_enabled = st.checkbox("🔄 自動継続測定（10秒間隔）", key="auto_performance_test")
            
            if auto_test_enabled:
                if "auto_performance_data" not in st.session_state:
                    st.session_state.auto_performance_data = []
                
                # 自動測定の実行
                import time
                if len(st.session_state.auto_performance_data) < 20:  # 最大20回
                    try:
                        start_time = time.time()
                        result = client.check_health()
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # ミリ秒
                        
                        st.session_state.auto_performance_data.append({
                            "timestamp": pd.Timestamp.now(),
                            "response_time": response_time,
                            "status": "成功" if result else "失敗"
                        })
                        
                        # グラフ表示
                        if st.session_state.auto_performance_data:
                            df_auto = pd.DataFrame(st.session_state.auto_performance_data)
                            
                            fig_auto = px.line(
                                df_auto,
                                x="timestamp",
                                y="response_time",
                                title="リアルタイム応答時間推移",
                                labels={
                                    "timestamp": "時刻",
                                    "response_time": "応答時間 (ms)"
                                },
                                markers=True
                            )
                            fig_auto.update_layout(height=300)
                            st.plotly_chart(fig_auto, use_container_width=True)
                            
                            # 統計表示
                            avg_time = df_auto["response_time"].mean()
                            max_time = df_auto["response_time"].max()
                            min_time = df_auto["response_time"].min()
                            
                            col_stat1, col_stat2, col_stat3 = st.columns(3)
                            with col_stat1:
                                st.metric("平均応答時間", f"{avg_time:.1f}ms")
                            with col_stat2:
                                st.metric("最大応答時間", f"{max_time:.1f}ms")
                            with col_stat3:
                                st.metric("最小応答時間", f"{min_time:.1f}ms")
                        
                        # 自動更新
                        time.sleep(2)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"自動測定エラー: {str(e)}")
                else:
                    st.info("自動測定完了（最大20回）。リセットして再開してください。")
                    if st.button("🔄 自動測定リセット", key="reset_auto_test"):
                        st.session_state.auto_performance_data = []
                        st.rerun()
    
    def _run_response_time_test(self, client: MCPAPIClient, endpoint: str, endpoint_name: str, count: int):
        """応答時間測定の実行"""
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import time
        import pandas as pd
        
        for i in range(count):
            try:
                status_text.text(f"測定中... {i+1}/{count}")
                progress_bar.progress((i + 1) / count)
                
                start_time = time.time()
                
                # エンドポイントに応じた処理
                if endpoint == "/health":
                    result = client.check_health()
                    success = result
                else:
                    result = client._make_request("GET", endpoint)
                    success = True
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ミリ秒
                
                results.append({
                    "測定回": i + 1,
                    "応答時間(ms)": round(response_time, 2),
                    "ステータス": "成功" if success else "失敗",
                    "タイムスタンプ": pd.Timestamp.now()
                })
                
                # 測定間隔
                time.sleep(0.1)
                
            except Exception as e:
                results.append({
                    "測定回": i + 1,
                    "応答時間(ms)": 0,
                    "ステータス": f"エラー: {str(e)}",
                    "タイムスタンプ": pd.Timestamp.now()
                })
        
        progress_bar.empty()
        status_text.empty()
        
        # 結果の表示
        if results:
            st.success(f"✅ 測定完了: {endpoint_name}")
            
            df_results = pd.DataFrame(results)
            
            # 統計情報
            success_results = df_results[df_results["ステータス"] == "成功"]
            if not success_results.empty:
                avg_time = success_results["応答時間(ms)"].mean()
                max_time = success_results["応答時間(ms)"].max()
                min_time = success_results["応答時間(ms)"].min()
                success_rate = len(success_results) / len(df_results) * 100
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("平均応答時間", f"{avg_time:.1f}ms")
                with col2:
                    st.metric("最大応答時間", f"{max_time:.1f}ms")
                with col3:
                    st.metric("最小応答時間", f"{min_time:.1f}ms")
                with col4:
                    st.metric("成功率", f"{success_rate:.1f}%")
                
                # グラフ表示
                fig_response = px.line(
                    success_results,
                    x="測定回",
                    y="応答時間(ms)",
                    title=f"{endpoint_name} - 応答時間推移",
                    markers=True
                )
                fig_response.update_layout(height=350)
                st.plotly_chart(fig_response, use_container_width=True)
                
                # 詳細データ表示
                st.markdown("#### 📋 詳細測定データ")
                st.dataframe(df_results, use_container_width=True, hide_index=True)
                
                # セッション状態に保存
                if "performance_results" not in st.session_state:
                    st.session_state.performance_results = []
                
                st.session_state.performance_results.append({
                    "endpoint": endpoint_name,
                    "timestamp": pd.Timestamp.now(),
                    "avg_time": avg_time,
                    "max_time": max_time,
                    "min_time": min_time,
                    "success_rate": success_rate,
                    "measurement_count": count
                })
            else:
                st.error("すべての測定が失敗しました。")
    
    def _render_load_testing(self, client: MCPAPIClient):
        """負荷テスト機能"""
        st.markdown("### 📊 負荷テスト")
        st.markdown("同時リクエストによるAPI負荷テスト")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### テスト設定")
            
            concurrent_users = st.number_input(
                "👥 同時ユーザー数", 
                min_value=1, 
                max_value=20, 
                value=5,
                key="concurrent_users"
            )
            
            requests_per_user = st.number_input(
                "🔄 ユーザーあたりリクエスト数", 
                min_value=1, 
                max_value=10, 
                value=3,
                key="requests_per_user"
            )
            
            load_test_endpoint = st.selectbox(
                "📡 負荷テスト対象",
                ["ヘルスチェック", "顧客一覧", "商品一覧", "注文一覧"],
                key="load_test_endpoint"
            )
            
            if st.button("🚀 負荷テスト開始", key="start_load_test"):
                self._run_load_test(client, load_test_endpoint, concurrent_users, requests_per_user)
        
        with col2:
            st.markdown("#### 負荷テスト結果")
            
            if "load_test_results" in st.session_state and st.session_state.load_test_results:
                latest_result = st.session_state.load_test_results[-1]
                
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric("総リクエスト数", latest_result["total_requests"])
                    st.metric("成功率", f"{latest_result['success_rate']:.1f}%")
                
                with col_metric2:
                    st.metric("平均応答時間", f"{latest_result['avg_response_time']:.1f}ms")
                    st.metric("スループット", f"{latest_result['throughput']:.1f} req/s")
                
                # 応答時間分布グラフ
                if "response_times" in latest_result:
                    fig_dist = px.histogram(
                        x=latest_result["response_times"],
                        nbins=20,
                        title="応答時間分布",
                        labels={"x": "応答時間 (ms)", "y": "リクエスト数"}
                    )
                    fig_dist.update_layout(height=300)
                    st.plotly_chart(fig_dist, use_container_width=True)
    
    def _run_load_test(self, client: MCPAPIClient, endpoint_name: str, concurrent_users: int, requests_per_user: int):
        """負荷テストの実行"""
        import time
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        endpoint_map = {
            "ヘルスチェック": "/health",
            "顧客一覧": "/api/customers?limit=5",
            "商品一覧": "/api/products?limit=5",
            "注文一覧": "/api/orders?limit=5"
        }
        
        endpoint = endpoint_map[endpoint_name]
        total_requests = concurrent_users * requests_per_user
        
        st.info(f"🚀 負荷テスト実行中: {concurrent_users}同時ユーザー × {requests_per_user}リクエスト = {total_requests}総リクエスト")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        start_time = time.time()
        
        def make_request(request_id):
            """単一リクエストの実行"""
            try:
                req_start = time.time()
                
                if endpoint == "/health":
                    result = client.check_health()
                    success = result
                else:
                    result = client._make_request("GET", endpoint)
                    success = True
                
                req_end = time.time()
                response_time = (req_end - req_start) * 1000
                
                return {
                    "request_id": request_id,
                    "response_time": response_time,
                    "success": success,
                    "timestamp": req_end
                }
            except Exception as e:
                req_end = time.time()
                return {
                    "request_id": request_id,
                    "response_time": 0,
                    "success": False,
                    "error": str(e),
                    "timestamp": req_end
                }
        
        # 並列実行
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # リクエストを分散実行
            for user in range(concurrent_users):
                for req in range(requests_per_user):
                    request_id = user * requests_per_user + req + 1
                    future = executor.submit(make_request, request_id)
                    futures.append(future)
            
            # 結果収集
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1
                
                progress_bar.progress(completed / total_requests)
                status_text.text(f"完了: {completed}/{total_requests}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        progress_bar.empty()
        status_text.empty()
        
        # 結果分析
        successful_results = [r for r in results if r["success"]]
        success_rate = len(successful_results) / len(results) * 100
        
        if successful_results:
            avg_response_time = sum(r["response_time"] for r in successful_results) / len(successful_results)
            max_response_time = max(r["response_time"] for r in successful_results)
            min_response_time = min(r["response_time"] for r in successful_results)
            throughput = len(successful_results) / total_time
            
            # 結果保存
            load_result = {
                "endpoint": endpoint_name,
                "timestamp": pd.Timestamp.now(),
                "concurrent_users": concurrent_users,
                "requests_per_user": requests_per_user,
                "total_requests": total_requests,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "throughput": throughput,
                "total_time": total_time,
                "response_times": [r["response_time"] for r in successful_results]
            }
            
            if "load_test_results" not in st.session_state:
                st.session_state.load_test_results = []
            
            st.session_state.load_test_results.append(load_result)
            
            st.success(f"✅ 負荷テスト完了 - 成功率: {success_rate:.1f}%, スループット: {throughput:.1f} req/s")
        else:
            st.error("❌ すべてのリクエストが失敗しました。")
    
    def _render_performance_analysis(self, client: MCPAPIClient):
        """パフォーマンス分析"""
        st.markdown("### 📈 パフォーマンス分析")
        st.markdown("測定データの統合分析とベンチマーク比較")
        
        if "performance_results" in st.session_state and st.session_state.performance_results:
            
            df_perf = pd.DataFrame(st.session_state.performance_results)
            
            # エンドポイント別比較
            st.markdown("#### 📊 エンドポイント別パフォーマンス比較")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 平均応答時間比較
                fig_avg = px.bar(
                    df_perf,
                    x="endpoint",
                    y="avg_time",
                    title="エンドポイント別平均応答時間",
                    labels={
                        "endpoint": "エンドポイント",
                        "avg_time": "平均応答時間 (ms)"
                    },
                    color="avg_time",
                    color_continuous_scale="viridis"
                )
                fig_avg.update_layout(height=350)
                st.plotly_chart(fig_avg, use_container_width=True)
            
            with col2:
                # 成功率比較
                fig_success = px.bar(
                    df_perf,
                    x="endpoint",
                    y="success_rate",
                    title="エンドポイント別成功率",
                    labels={
                        "endpoint": "エンドポイント",
                        "success_rate": "成功率 (%)"
                    },
                    color="success_rate",
                    color_continuous_scale="RdYlGn"
                )
                fig_success.update_layout(height=350)
                st.plotly_chart(fig_success, use_container_width=True)
            
            # 時系列分析
            st.markdown("#### 📅 パフォーマンス時系列推移")
            
            fig_timeline = px.line(
                df_perf,
                x="timestamp",
                y="avg_time",
                color="endpoint",
                title="平均応答時間の時系列推移",
                labels={
                    "timestamp": "測定時刻",
                    "avg_time": "平均応答時間 (ms)",
                    "endpoint": "エンドポイント"
                },
                markers=True
            )
            fig_timeline.update_layout(height=400)
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # 統計サマリー
            st.markdown("#### 📋 統計サマリー")
            
            summary_stats = df_perf.groupby("endpoint").agg({
                "avg_time": ["mean", "std", "min", "max"],
                "success_rate": ["mean", "min"],
                "measurement_count": "sum"
            }).round(2)
            
            summary_stats.columns = ["平均応答時間", "応答時間標準偏差", "最小応答時間", "最大応答時間", "平均成功率", "最小成功率", "総測定回数"]
            
            st.dataframe(summary_stats, use_container_width=True)
            
            # ベンチマーク評価
            st.markdown("#### 🏆 パフォーマンス評価")
            
            col1, col2, col3 = st.columns(3)
            
            overall_avg = df_perf["avg_time"].mean()
            overall_success = df_perf["success_rate"].mean()
            
            with col1:
                if overall_avg < 100:
                    st.success(f"🟢 優秀: 平均応答時間 {overall_avg:.1f}ms")
                elif overall_avg < 500:
                    st.warning(f"🟡 良好: 平均応答時間 {overall_avg:.1f}ms")
                else:
                    st.error(f"🔴 要改善: 平均応答時間 {overall_avg:.1f}ms")
            
            with col2:
                if overall_success >= 99:
                    st.success(f"🟢 優秀: 成功率 {overall_success:.1f}%")
                elif overall_success >= 95:
                    st.warning(f"🟡 良好: 成功率 {overall_success:.1f}%")
                else:
                    st.error(f"🔴 要改善: 成功率 {overall_success:.1f}%")
            
            with col3:
                total_measurements = df_perf["measurement_count"].sum()
                st.info(f"📊 総測定数: {total_measurements}回")
        
        else:
            st.info("📊 パフォーマンス測定データがありません。リアルタイム測定または負荷テストを実行してください。")
    
    def _render_performance_history(self):
        """パフォーマンス測定履歴"""
        st.markdown("### 📋 測定履歴")
        st.markdown("過去のパフォーマンス測定結果の確認と管理")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 測定履歴表示
            if "performance_results" in st.session_state and st.session_state.performance_results:
                
                df_history = pd.DataFrame(st.session_state.performance_results)
                df_history["測定時刻"] = df_history["timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                display_history = df_history[[
                    "測定時刻", "endpoint", "avg_time", "max_time", "min_time", 
                    "success_rate", "measurement_count"
                ]].rename(columns={
                    "endpoint": "エンドポイント",
                    "avg_time": "平均応答時間(ms)",
                    "max_time": "最大応答時間(ms)",
                    "min_time": "最小応答時間(ms)",
                    "success_rate": "成功率(%)",
                    "measurement_count": "測定回数"
                })
                
                st.dataframe(display_history, use_container_width=True, hide_index=True)
                
                # CSVダウンロード
                csv_history = display_history.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 測定履歴をCSVダウンロード",
                    data=csv_history,
                    file_name=f"performance_history_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            
            # 負荷テスト履歴
            if "load_test_results" in st.session_state and st.session_state.load_test_results:
                st.markdown("#### 🚀 負荷テスト履歴")
                
                df_load_history = pd.DataFrame(st.session_state.load_test_results)
                df_load_history["測定時刻"] = df_load_history["timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                display_load = df_load_history[[
                    "測定時刻", "endpoint", "concurrent_users", "requests_per_user",
                    "total_requests", "success_rate", "avg_response_time", "throughput"
                ]].rename(columns={
                    "endpoint": "エンドポイント",
                    "concurrent_users": "同時ユーザー数",
                    "requests_per_user": "ユーザーあたりリクエスト",
                    "total_requests": "総リクエスト数",
                    "success_rate": "成功率(%)",
                    "avg_response_time": "平均応答時間(ms)",
                    "throughput": "スループット(req/s)"
                })
                
                st.dataframe(display_load, use_container_width=True, hide_index=True)
            
            if not ("performance_results" in st.session_state and st.session_state.performance_results) and \
               not ("load_test_results" in st.session_state and st.session_state.load_test_results):
                st.info("📭 測定履歴がありません。パフォーマンステストを実行してください。")
        
        with col2:
            st.markdown("#### 🗂️ 履歴管理")
            
            if st.button("🗑️ 履歴クリア", key="clear_performance_history"):
                if "performance_results" in st.session_state:
                    del st.session_state.performance_results
                if "load_test_results" in st.session_state:
                    del st.session_state.load_test_results
                st.success("✅ 履歴をクリアしました")
                st.rerun()
            
            if st.button("📊 統計再計算", key="recalc_performance_stats"):
                if "performance_results" in st.session_state:
                    st.success("✅ 統計を再計算しました")
                    st.rerun()
            
            # 履歴サマリー
            if "performance_results" in st.session_state:
                perf_count = len(st.session_state.performance_results)
                st.metric("📊 測定履歴数", perf_count)
            
            if "load_test_results" in st.session_state:
                load_count = len(st.session_state.load_test_results)
                st.metric("🚀 負荷テスト数", load_count)
    
    def _render_interactive_page(self):
        """対話機能ページの描画（デモ機能8&9）"""
        st.markdown("## 🔄 対話機能デモ")
        st.markdown("リアルタイムデータ操作とチャット風インターフェース")
        
        client = self.get_api_client()
        if not client:
            st.error("API サーバーに接続できません。")
            return
        
        # タブで機能を分割
        tab1, tab2, tab3, tab4 = st.tabs(["💬 チャット風操作", "🔄 リアルタイム更新", "🎮 インタラクティブ操作", "📊 ライブダッシュボード"])
        
        with tab1:
            self._render_chat_interface(client)
        
        with tab2:
            self._render_realtime_updates(client)
            
        with tab3:
            self._render_interactive_operations(client)
            
        with tab4:
            self._render_live_dashboard(client)
    
    def _render_chat_interface(self, client: MCPAPIClient):
        """チャット風インターフェース"""
        st.markdown("### 💬 チャット風データ操作")
        st.markdown("自然言語風のコマンドでデータベース操作")
        
        # チャット履歴の初期化
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [
                {"role": "assistant", "content": "👋 こんにちは！データベース操作をお手伝いします。\n\n例: 「東京の顧客を5件表示して」「新しい顧客を作成したい」「売上統計を見せて」"}
            ]
        
        # チャット履歴の表示
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
        
        # チャット入力
        if prompt := st.chat_input("何をしたいですか？（例: 東京の顧客を表示、注文データを作成、統計を確認）"):
            # ユーザーメッセージを追加
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # コマンド解析と実行
            response = self._process_chat_command(client, prompt)
            
            # アシスタントレスポンスを追加
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()
        
        # チャット履歴管理
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ 履歴クリア", key="clear_chat_history"):
                st.session_state.chat_history = [
                    {"role": "assistant", "content": "👋 こんにちは！データベース操作をお手伝いします。"}
                ]
                st.rerun()
    
    def _process_chat_command(self, client: MCPAPIClient, command: str) -> str:
        """チャットコマンドの処理"""
        command_lower = command.lower()
        
        try:
            # 顧客関連のコマンド
            if "顧客" in command_lower and ("表示" in command_lower or "見せて" in command_lower or "リスト" in command_lower):
                # 都市フィルタの検出
                cities = ["東京", "大阪", "名古屋", "福岡", "札幌"]
                city_filter = None
                for city in cities:
                    if city in command:
                        city_filter = city
                        break
                
                # 件数の検出
                import re
                numbers = re.findall(r'\d+', command)
                limit = int(numbers[0]) if numbers else 10
                limit = min(limit, 50)  # 最大50件
                
                # APIリクエスト
                params = {"limit": limit}
                if city_filter:
                    params["city"] = city_filter
                
                customers = client._make_request("GET", "/api/customers", params=params)
                
                if customers:
                    result = f"✅ 顧客データを取得しました！\n\n"
                    if city_filter:
                        result += f"🏙️ 都市: {city_filter}\n"
                    result += f"📊 件数: {len(customers)}件\n\n"
                    
                    # 最初の3件を表示
                    for i, customer in enumerate(customers[:3]):
                        result += f"**{i+1}. {customer.get('name', 'N/A')}**\n"
                        result += f"   📧 {customer.get('email', 'N/A')}\n"
                        result += f"   🏙️ {customer.get('city', 'N/A')}\n\n"
                    
                    if len(customers) > 3:
                        result += f"... 他 {len(customers) - 3}件\n\n"
                    
                    result += "💡 詳細は「基本操作」タブで確認できます。"
                    return result
                else:
                    return "❌ 顧客データの取得に失敗しました。"
            
            # 統計関連のコマンド
            elif "統計" in command_lower or "売上" in command_lower or "分析" in command_lower:
                stats = client._make_request("GET", "/api/stats/sales")
                
                if stats:
                    result = f"📊 売上統計データ\n\n"
                    result += f"💰 総売上: ¥{stats.get('total_sales', 0):,.0f}\n"
                    result += f"📦 総注文数: {stats.get('total_orders', 0)}件\n"
                    result += f"📈 平均注文額: ¥{stats.get('avg_order_value', 0):.0f}\n\n"
                    
                    # 人気商品TOP3
                    top_products = stats.get('top_products', [])[:3]
                    if top_products:
                        result += "🏆 人気商品TOP3:\n"
                        for i, product in enumerate(top_products):
                            result += f"{i+1}. {product.get('product_name', 'N/A')} (¥{product.get('total_sales', 0):,.0f})\n"
                    
                    result += "\n💡 詳細は「売上分析」タブで確認できます。"
                    return result
                else:
                    return "❌ 統計データの取得に失敗しました。"
            
            # 顧客作成のコマンド
            elif "顧客" in command_lower and ("作成" in command_lower or "追加" in command_lower or "新規" in command_lower):
                return "📝 顧客作成を開始します！\n\n" \
                       "以下の情報が必要です：\n" \
                       "• 名前\n" \
                       "• メールアドレス\n" \
                       "• 都市\n\n" \
                       "💡 「データ作成」タブで詳細な作成フォームを利用できます。"
            
            # 注文関連のコマンド
            elif "注文" in command_lower and ("表示" in command_lower or "見せて" in command_lower):
                orders = client._make_request("GET", "/api/orders", params={"limit": 5})
                
                if orders:
                    result = f"📦 最近の注文データ（5件）\n\n"
                    for i, order in enumerate(orders[:5]):
                        result += f"**注文{i+1}**: {order.get('product_name', 'N/A')}\n"
                        result += f"   💰 ¥{order.get('price', 0):,.0f} × {order.get('quantity', 0)}個\n"
                        result += f"   👤 顧客: {order.get('customer_name', 'N/A')}\n\n"
                    
                    result += "💡 詳細は「基本操作」タブで確認できます。"
                    return result
                else:
                    return "❌ 注文データの取得に失敗しました。"
            
            # ヘルプ・使い方
            elif "ヘルプ" in command_lower or "使い方" in command_lower or "help" in command_lower.lower():
                return "🤖 **チャット機能の使い方**\n\n" \
                       "以下のようなコマンドが使えます：\n\n" \
                       "**📊 データ表示**\n" \
                       "• 「東京の顧客を10件表示」\n" \
                       "• 「注文データを見せて」\n" \
                       "• 「商品を5件リスト」\n\n" \
                       "**📈 統計・分析**\n" \
                       "• 「売上統計を確認」\n" \
                       "• 「分析データを見せて」\n\n" \
                       "**📝 データ作成**\n" \
                       "• 「新しい顧客を作成したい」\n" \
                       "• 「注文を追加したい」\n\n" \
                       "💡 より詳細な操作は各タブで行えます！"
            
            # その他のコマンド
            else:
                return f"🤔 「{command}」の処理方法がわかりません。\n\n" \
                       "💡 以下を試してみてください：\n" \
                       "• 「ヘルプ」と入力して使い方を確認\n" \
                       "• 「顧客を表示」「売上統計を確認」など\n" \
                       "• 各タブで詳細な操作を実行"
        
        except Exception as e:
            return f"❌ エラーが発生しました: {str(e)}\n\n💡 「ヘルプ」と入力して使い方を確認してください。"
    
    def _render_realtime_updates(self, client: MCPAPIClient):
        """リアルタイム更新機能"""
        st.markdown("### 🔄 リアルタイムデータ更新")
        st.markdown("データの自動更新とライブ監視")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⏰ 自動更新設定")
            
            auto_refresh = st.checkbox("🔄 自動更新を有効にする", key="auto_refresh_enabled")
            
            if auto_refresh:
                refresh_interval = st.selectbox(
                    "🕐 更新間隔",
                    ["5秒", "10秒", "30秒", "1分"],
                    index=1,
                    key="refresh_interval"
                )
                
                # 更新間隔の解析
                interval_map = {"5秒": 5, "10秒": 10, "30秒": 30, "1分": 60}
                interval_seconds = interval_map[refresh_interval]
                
                st.info(f"🕐 {refresh_interval}ごとに自動更新中...")
                
                # 自動更新の実装
                if "last_refresh_time" not in st.session_state:
                    st.session_state.last_refresh_time = pd.Timestamp.now()
                
                current_time = pd.Timestamp.now()
                time_diff = (current_time - st.session_state.last_refresh_time).total_seconds()
                
                if time_diff >= interval_seconds:
                    st.session_state.last_refresh_time = current_time
                    
                    # データ更新通知
                    st.success(f"✨ データを更新しました ({current_time.strftime('%H:%M:%S')})")
                    
                    # 少し待ってからリフレッシュ
                    import time
                    time.sleep(1)
                    st.rerun()
                
                # カウントダウン表示
                remaining = interval_seconds - time_diff
                if remaining > 0:
                    st.write(f"⏱️ 次回更新まで: {remaining:.0f}秒")
                
                # プログレスバー
                progress = min(time_diff / interval_seconds, 1.0)
                st.progress(progress)
            
            else:
                st.info("自動更新は無効です。手動で更新してください。")
                
                if st.button("🔄 今すぐ更新", key="manual_refresh"):
                    st.success("✨ データを手動更新しました")
                    st.rerun()
        
        with col2:
            st.markdown("#### 📊 ライブ統計")
            
            try:
                # リアルタイムで統計を取得
                current_stats = client._make_request("GET", "/api/stats/sales")
                
                if current_stats:
                    st.metric(
                        "💰 現在の総売上",
                        f"¥{current_stats.get('total_sales', 0):,.0f}",
                        delta=None
                    )
                    
                    st.metric(
                        "📦 総注文数",
                        f"{current_stats.get('total_orders', 0)}件",
                        delta=None
                    )
                    
                    st.metric(
                        "📈 平均注文額",
                        f"¥{current_stats.get('avg_order_value', 0):.0f}",
                        delta=None
                    )
                    
                    # 最終更新時刻
                    st.caption(f"📅 最終更新: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # リアルタイム顧客数
                customers = client._make_request("GET", "/api/customers", params={"limit": 1000})
                if customers:
                    st.metric("👥 総顧客数", len(customers))
                
            except Exception as e:
                st.error(f"❌ ライブ統計の取得に失敗: {str(e)}")
        
        # リアルタイム活動ログ
        st.markdown("#### 📋 リアルタイム活動ログ")
        
        if "activity_log" not in st.session_state:
            st.session_state.activity_log = []
        
        # 新しい活動をログに追加（デモ用）
        if auto_refresh and time_diff >= interval_seconds:
            new_activity = {
                "timestamp": pd.Timestamp.now(),
                "action": "データ自動更新",
                "status": "成功",
                "details": f"統計データを更新 ({current_time.strftime('%H:%M:%S')})"
            }
            st.session_state.activity_log.append(new_activity)
            
            # ログを最新10件に制限
            if len(st.session_state.activity_log) > 10:
                st.session_state.activity_log = st.session_state.activity_log[-10:]
        
        # 活動ログの表示
        if st.session_state.activity_log:
            log_container = st.container()
            with log_container:
                for activity in reversed(st.session_state.activity_log[-5:]):  # 最新5件
                    timestamp = activity["timestamp"].strftime("%H:%M:%S")
                    status_icon = "✅" if activity["status"] == "成功" else "❌"
                    st.write(f"{status_icon} `{timestamp}` {activity['action']} - {activity['details']}")
        else:
            st.info("📭 活動ログがありません。")
    
    def _render_interactive_operations(self, client: MCPAPIClient):
        """インタラクティブ操作"""
        st.markdown("### 🎮 インタラクティブ操作")
        st.markdown("ドラッグ&ドロップ風の直感的なデータ操作")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 クイック操作パネル")
            
            # 顧客クイック作成
            with st.expander("👤 顧客クイック作成", expanded=False):
                with st.form("quick_customer_form"):
                    name = st.text_input("名前", placeholder="山田太郎")
                    email = st.text_input("メール", placeholder="yamada@example.com")
                    city = st.selectbox("都市", ["東京", "大阪", "名古屋", "福岡", "札幌"])
                    
                    submitted = st.form_submit_button("⚡ 即座に作成")
                    
                    if submitted and name and email:
                        try:
                            customer_data = {
                                "name": name,
                                "email": email,
                                "city": city
                            }
                            result = client._make_request("POST", "/api/customers", json=customer_data)
                            st.success(f"✅ 顧客「{name}」を作成しました！")
                            
                            # 活動ログに追加
                            if "activity_log" not in st.session_state:
                                st.session_state.activity_log = []
                            
                            st.session_state.activity_log.append({
                                "timestamp": pd.Timestamp.now(),
                                "action": "顧客作成",
                                "status": "成功",
                                "details": f"新規顧客「{name}」を{city}で作成"
                            })
                            
                        except Exception as e:
                            st.error(f"❌ エラー: {str(e)}")
            
            # 注文クイック作成
            with st.expander("📦 注文クイック作成", expanded=False):
                # 顧客選択のためのデータ取得
                try:
                    customers = client._make_request("GET", "/api/customers", params={"limit": 20})
                    customer_options = {f"{c['name']} ({c['city']})": c['id'] for c in customers} if customers else {}
                    
                    with st.form("quick_order_form"):
                        if customer_options:
                            selected_customer = st.selectbox("顧客選択", list(customer_options.keys()))
                            product_name = st.text_input("商品名", placeholder="ノートパソコン")
                            quantity = st.number_input("数量", min_value=1, max_value=10, value=1)
                            price = st.number_input("価格", min_value=100, max_value=100000, value=1000, step=100)
                            
                            order_submitted = st.form_submit_button("⚡ 即座に注文")
                            
                            if order_submitted and product_name:
                                try:
                                    customer_id = customer_options[selected_customer]
                                    order_data = {
                                        "customer_id": customer_id,
                                        "product_name": product_name,
                                        "quantity": quantity,
                                        "price": price
                                    }
                                    result = client._make_request("POST", "/api/orders", json=order_data)
                                    st.success(f"✅ 注文「{product_name}」を作成しました！")
                                    
                                    # 活動ログに追加
                                    if "activity_log" not in st.session_state:
                                        st.session_state.activity_log = []
                                    
                                    st.session_state.activity_log.append({
                                        "timestamp": pd.Timestamp.now(),
                                        "action": "注文作成",
                                        "status": "成功",
                                        "details": f"注文「{product_name}」(¥{price:,} × {quantity})"
                                    })
                                    
                                except Exception as e:
                                    st.error(f"❌ エラー: {str(e)}")
                        else:
                            st.warning("⚠️ 顧客データがありません。先に顧客を作成してください。")
                
                except Exception as e:
                    st.error(f"❌ 顧客データの取得に失敗: {str(e)}")
        
        with col2:
            st.markdown("#### 🔍 スマート検索")
            
            search_type = st.selectbox(
                "検索対象",
                ["顧客検索", "商品検索", "注文検索"],
                key="smart_search_type"
            )
            
            search_query = st.text_input(
                "🔍 検索キーワード",
                placeholder="名前、メール、商品名など",
                key="smart_search_query"
            )
            
            if search_query:
                try:
                    if search_type == "顧客検索":
                        # 顧客データを取得して検索
                        all_customers = client._make_request("GET", "/api/customers", params={"limit": 100})
                        if all_customers:
                            # 名前、メール、都市で検索
                            filtered_customers = [
                                c for c in all_customers 
                                if search_query.lower() in c.get('name', '').lower() or 
                                   search_query.lower() in c.get('email', '').lower() or
                                   search_query.lower() in c.get('city', '').lower()
                            ]
                            
                            if filtered_customers:
                                st.success(f"🔍 {len(filtered_customers)}件の顧客が見つかりました")
                                for customer in filtered_customers[:5]:
                                    with st.container():
                                        st.write(f"**{customer['name']}** ({customer['city']})")
                                        st.write(f"📧 {customer['email']}")
                                        st.write("---")
                            else:
                                st.info("🔍 該当する顧客が見つかりませんでした")
                        
                    elif search_type == "注文検索":
                        # 注文データを取得して検索
                        all_orders = client._make_request("GET", "/api/orders", params={"limit": 100})
                        if all_orders:
                            # 商品名で検索
                            filtered_orders = [
                                o for o in all_orders 
                                if search_query.lower() in o.get('product_name', '').lower()
                            ]
                            
                            if filtered_orders:
                                st.success(f"🔍 {len(filtered_orders)}件の注文が見つかりました")
                                for order in filtered_orders[:5]:
                                    with st.container():
                                        st.write(f"**{order['product_name']}**")
                                        st.write(f"💰 ¥{order['price']:,} × {order['quantity']}個")
                                        st.write(f"👤 {order.get('customer_name', 'N/A')}")
                                        st.write("---")
                            else:
                                st.info("🔍 該当する注文が見つかりませんでした")
                    
                except Exception as e:
                    st.error(f"❌ 検索エラー: {str(e)}")
    
    def _render_live_dashboard(self, client: MCPAPIClient):
        """ライブダッシュボード"""
        st.markdown("### 📊 ライブダッシュボード")
        st.markdown("リアルタイムデータ可視化とKPI監視")
        
        # ダッシュボード自動更新
        auto_dashboard = st.checkbox("🔄 ダッシュボード自動更新", key="auto_dashboard")
        
        if auto_dashboard:
            # 3秒ごとに更新
            import time
            if "dashboard_last_update" not in st.session_state:
                st.session_state.dashboard_last_update = pd.Timestamp.now()
            
            current_time = pd.Timestamp.now()
            time_diff = (current_time - st.session_state.dashboard_last_update).total_seconds()
            
            if time_diff >= 3:
                st.session_state.dashboard_last_update = current_time
                time.sleep(0.5)
                st.rerun()
        
        try:
            # KPIメトリクス
            col1, col2, col3, col4 = st.columns(4)
            
            # 統計データ取得
            stats = client._make_request("GET", "/api/stats/sales")
            customers = client._make_request("GET", "/api/customers", params={"limit": 1000})
            orders = client._make_request("GET", "/api/orders", params={"limit": 1000})
            
            if stats:
                with col1:
                    st.metric(
                        "💰 総売上",
                        f"¥{stats.get('total_sales', 0):,.0f}",
                        delta=f"+¥{stats.get('total_sales', 0) * 0.1:,.0f}" if auto_dashboard else None
                    )
                
                with col2:
                    st.metric(
                        "📦 総注文",
                        f"{stats.get('total_orders', 0)}件",
                        delta=f"+{max(1, stats.get('total_orders', 0) // 10)}" if auto_dashboard else None
                    )
                
                with col3:
                    if customers:
                        st.metric(
                            "👥 総顧客",
                            f"{len(customers)}人",
                            delta="+2" if auto_dashboard else None
                        )
                
                with col4:
                    avg_order = stats.get('avg_order_value', 0)
                    st.metric(
                        "📈 平均注文",
                        f"¥{avg_order:.0f}",
                        delta=f"+¥{avg_order * 0.05:.0f}" if auto_dashboard else None
                    )
            
            # グラフエリア
            col_left, col_right = st.columns(2)
            
            with col_left:
                # 都市別売上チャート
                if stats and 'sales_by_city' in stats:
                    sales_by_city = stats['sales_by_city']
                    if sales_by_city:
                        df_city = pd.DataFrame(sales_by_city)
                        
                        fig_city = px.pie(
                            df_city.head(5),
                            values='total_sales',
                            names='city',
                            title="🏙️ 都市別売上分布（リアルタイム）"
                        )
                        fig_city.update_layout(height=350)
                        st.plotly_chart(fig_city, use_container_width=True)
            
            with col_right:
                # 人気商品チャート
                if stats and 'top_products' in stats:
                    top_products = stats['top_products']
                    if top_products:
                        df_products = pd.DataFrame(top_products[:5])
                        
                        fig_products = px.bar(
                            df_products,
                            x='product_name',
                            y='total_sales',
                            title="🏆 人気商品TOP5（リアルタイム）",
                            labels={'product_name': '商品名', 'total_sales': '売上'}
                        )
                        fig_products.update_layout(height=350, xaxis_tickangle=-45)
                        st.plotly_chart(fig_products, use_container_width=True)
            
            # アクティビティフィード
            st.markdown("#### 🔔 リアルタイムアクティビティ")
            
            # サンプルアクティビティの生成（デモ用）
            if auto_dashboard and time_diff >= 3:
                if "dashboard_activities" not in st.session_state:
                    st.session_state.dashboard_activities = []
                
                import random
                activities = [
                    "新規顧客「田中花子」が東京で登録",
                    "注文「スマートフォン」¥89,800 が完了",
                    "大阪エリアで売上¥50,000達成",
                    "注文「ノートパソコン」¥120,000 が完了",
                    "新規顧客「佐藤次郎」が名古屋で登録"
                ]
                
                new_activity = {
                    "timestamp": pd.Timestamp.now(),
                    "message": random.choice(activities),
                    "type": random.choice(["success", "info", "warning"])
                }
                
                st.session_state.dashboard_activities.append(new_activity)
                
                # 最新10件に制限
                if len(st.session_state.dashboard_activities) > 10:
                    st.session_state.dashboard_activities = st.session_state.dashboard_activities[-10:]
            
            # アクティビティ表示
            if "dashboard_activities" in st.session_state and st.session_state.dashboard_activities:
                for activity in reversed(st.session_state.dashboard_activities[-5:]):
                    timestamp = activity["timestamp"].strftime("%H:%M:%S")
                    icon = {"success": "✅", "info": "ℹ️", "warning": "⚠️"}.get(activity["type"], "ℹ️")
                    st.write(f"{icon} `{timestamp}` {activity['message']}")
            else:
                st.info("📭 アクティビティがありません。")
            
            # 最終更新時刻
            st.caption(f"🕐 最終更新: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            st.error(f"❌ ダッシュボードデータの取得に失敗: {str(e)}")
    
    def run(self):
        """アプリケーションを実行"""
        # ページ設定
        st.set_page_config(
            page_title="MCP API デモアプリ",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # カスタムCSS
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                color: #1f77b4;
                text-align: center;
                margin-bottom: 2rem;
            }
            .demo-card {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 4px solid #17a2b8;
                margin: 1rem 0;
            }
            .metric-card {
                background-color: #ffffff;
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # メイン描画
        self.render_sidebar()
        self.render_main_content()


def main():
    """メイン関数"""
    app = MCPDemoApplication()
    app.run()


if __name__ == "__main__":
    main()