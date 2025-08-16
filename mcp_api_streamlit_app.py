# MCP API クライアントの9つのデモ機能をStreamlit化
# streamlit run mcp_api_streamlit_app.py --server.port=8502

import streamlit as st
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

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
        
        selected_page = st.sidebar.selectbox(
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
        st.sidebar.info("このアプリはmcp_api_client.pyの9つのデモ機能をStreamlit化したものです。")
        
        # 開発者向け情報
        if st.sidebar.expander("🛠️ 開発者情報"):
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
                    st.error(f"❌ エラーが発生しました: {str(e)}")
    
    def _render_order_creation_form(self, client: MCPAPIClient):
        """注文作成フォームの描画"""
        st.markdown("### 🛒 新規注文登録")
        
        # まず顧客と商品のリストを取得
        try:
            with st.spinner("顧客・商品データ読み込み中..."):
                customers_data = client._make_request("GET", "/api/customers", params={"limit": 100})
                products_data = client._make_request("GET", "/api/products", params={"limit": 100})
                
                customers = customers_data.get("customers", []) if customers_data else []
                products = products_data.get("products", []) if products_data else []
                
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
        st.info("🚧 実装中... データ分析機能を準備しています")
    
    def _render_error_handling_page(self):
        """エラーハンドリングページの描画（デモ機能6）"""
        st.markdown("## 🚨 エラーテストデモ")
        st.info("🚧 実装中... エラーテスト機能を準備しています")
    
    def _render_performance_page(self):
        """パフォーマンスページの描画（デモ機能7）"""
        st.markdown("## ⚡ パフォーマンステストデモ")
        st.info("🚧 実装中... パフォーマンステスト機能を準備しています")
    
    def _render_interactive_page(self):
        """対話機能ページの描画（デモ機能8&9）"""
        st.markdown("## 🔄 対話機能デモ")
        st.info("🚧 実装中... 対話機能を準備しています")
    
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