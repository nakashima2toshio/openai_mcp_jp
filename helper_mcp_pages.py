# helper_mcp_pages.py
# 各ページクラスの完全実装
# 直接クエリ、データ分析、設定ページを含む

import streamlit as st
import pandas as pd
import requests
import redis
import sqlalchemy
import json
import traceback
import os
from datetime import datetime
from typing import Dict, Any, List
from helper_mcp import PageManager, ServerStatusManager


# ==================================================
# 直接クエリページ
# ==================================================
class DirectQueryPage(PageManager):
    """直接データベースクエリページ"""

    def render(self):
        st.header("📊 直接データベースクエリ")

        query_type = st.selectbox("クエリタイプを選択",
                                  ["Redis", "PostgreSQL", "Elasticsearch", "Qdrant"])

        if query_type == "Redis":
            self._render_redis_query()
        elif query_type == "PostgreSQL":
            self._render_postgresql_query()
        elif query_type == "Elasticsearch":
            self._render_elasticsearch_query()
        elif query_type == "Qdrant":
            self._render_qdrant_query()

    def _render_redis_query(self):
        """Redisクエリ機能"""
        st.subheader("🔴 Redis クエリ")

        # 事前定義されたクエリ
        redis_queries = {
            "全キー表示"  : "KEYS *",
            "セッション数": "KEYS session:*",
            "カウンタ一覧": "KEYS counter:*",
            "カテゴリ表示": "SMEMBERS categories:all",
            "検索履歴"    : "LRANGE search:recent 0 -1"
        }

        col1, col2 = st.columns([1, 2])

        with col1:
            st.write("**クイッククエリ:**")
            for name, cmd in redis_queries.items():
                if st.button(name, key=f"redis_{name}"):
                    st.session_state.redis_command = cmd

        with col2:
            redis_command = st.text_input(
                "Redisコマンド",
                value=getattr(st.session_state, 'redis_command', 'KEYS *'),
                key="redis_input"
            )

        if st.button("実行", key="redis_exec"):
            redis_manager = self.status_manager.get_manager('Redis')
            status = redis_manager.check_connection()

            if "🟢" in status["status"]:
                try:
                    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                    result = self._execute_redis_command(r, redis_command)
                    if result is not None:
                        if isinstance(result, list):
                            st.json(result)
                        else:
                            st.code(str(result))
                except Exception as e:
                    st.error(f"エラー: {e}")
            else:
                st.warning("Redis サーバーに接続できません")

    def _execute_redis_command(self, redis_client, command: str):
        """Redis コマンドの安全な実行"""
        cmd_parts = command.strip().split()
        cmd = cmd_parts[0].upper()

        if cmd == "KEYS":
            pattern = cmd_parts[1] if len(cmd_parts) > 1 else "*"
            return sorted(redis_client.keys(pattern))
        elif cmd == "GET":
            if len(cmd_parts) > 1:
                return redis_client.get(cmd_parts[1])
            else:
                st.error("GET コマンドにはキーを指定してください")
        elif cmd == "HGETALL":
            if len(cmd_parts) > 1:
                return redis_client.hgetall(cmd_parts[1])
            else:
                st.error("HGETALL コマンドにはキーを指定してください")
        elif cmd == "SMEMBERS":
            if len(cmd_parts) > 1:
                return sorted(list(redis_client.smembers(cmd_parts[1])))
            else:
                st.error("SMEMBERS コマンドにはキーを指定してください")
        elif cmd == "LRANGE":
            if len(cmd_parts) >= 4:
                key = cmd_parts[1]
                start = int(cmd_parts[2])
                stop = int(cmd_parts[3])
                return redis_client.lrange(key, start, stop)
            else:
                st.error("LRANGE コマンドの形式: LRANGE key start stop")
        else:
            st.error(f"サポートされていないコマンドです: {cmd}")
            st.info("サポートされているコマンド: KEYS, GET, HGETALL, SMEMBERS, LRANGE")
        return None

    def _render_postgresql_query(self):
        """PostgreSQLクエリ機能"""
        st.subheader("🟦 PostgreSQL クエリ")

        # PostgreSQLの接続状態確認
        pg_manager = self.status_manager.get_manager('PostgreSQL')
        status = pg_manager.check_connection()

        if "🔴" in status["status"]:
            st.warning("PostgreSQL サーバーに接続できません")
            st.write(f"状態: {status['status']}")
            st.write(f"詳細: {status['details']}")
            return

        # テーブル存在チェック
        try:
            engine = sqlalchemy.create_engine(os.getenv('PG_CONN_STR'))

            # 利用可能なテーブル一覧を取得
            available_tables = pd.read_sql("""
                                           SELECT table_name
                                           FROM information_schema.tables
                                           WHERE table_schema = 'public'
                                             AND table_type = 'BASE TABLE'
                                           ORDER BY table_name
                                           """, engine)

            table_list = available_tables['table_name'].tolist()

            engine.dispose()

            if not table_list:
                st.warning("⚠️ PostgreSQLにテーブルが存在しません")

                with st.expander("💡 セットアップ手順", expanded=True):
                    st.markdown("""
                    **テストデータの投入:**
                    ```bash
                    # テストデータスクリプトの実行
                    uv run python scripts/setup_test_data.py
                    ```

                    **手動でのテーブル作成例:**
                    ```sql
                    -- PostgreSQLに接続
                    psql -h localhost -U testuser -d testdb

                    -- サンプルテーブル作成
                    CREATE TABLE customers (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        email VARCHAR(100),
                        city VARCHAR(50)
                    );
                    ```
                    """)
                return
            else:
                st.success(f"✅ 利用可能なテーブル: {', '.join(table_list)}")

        except Exception as e:
            st.error(f"テーブル確認エラー: {e}")
            table_list = ['customers', 'orders', 'products']  # フォールバック

        # 事前定義されたクエリ（利用可能なテーブルに基づいて動的生成）
        pg_queries = {}

        if 'customers' in table_list:
            pg_queries.update({
                "全顧客"    : "SELECT * FROM customers ORDER BY id;",
                "東京の顧客": "SELECT * FROM customers WHERE city = '東京';"
            })

        if 'orders' in table_list and 'customers' in table_list:
            pg_queries.update({
                "最新注文": "SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id ORDER BY o.order_date DESC LIMIT 5;",
                "売上統計": "SELECT product_name, SUM(price * quantity) as total_sales FROM orders GROUP BY product_name ORDER BY total_sales DESC;"
            })
        elif 'orders' in table_list:
            pg_queries.update({
                "最新注文": "SELECT * FROM orders ORDER BY id DESC LIMIT 5;",
                "売上統計": "SELECT product_name, SUM(price * quantity) as total_sales FROM orders GROUP BY product_name ORDER BY total_sales DESC;"
            })

        if 'products' in table_list:
            pg_queries["商品在庫"] = "SELECT name, stock_quantity, price FROM products ORDER BY stock_quantity DESC;"

        # テーブル確認クエリ
        pg_queries["テーブル一覧"] = """
                                     SELECT table_name, table_type
                                     FROM information_schema.tables
                                     WHERE table_schema = 'public'
                                     ORDER BY table_name; \
                                     """

        if table_list:
            pg_queries["テーブル詳細"] = f"""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_list[0]}'
                ORDER BY ordinal_position;
            """

        col1, col2 = st.columns([1, 2])

        with col1:
            st.write("**クイッククエリ:**")
            for name, sql in pg_queries.items():
                if st.button(name, key=f"pg_{name}"):
                    st.session_state.sql_query = sql

        with col2:
            default_query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            if table_list:
                default_query = f"SELECT * FROM {table_list[0]} LIMIT 5;"

            sql_query = st.text_area(
                "SQLクエリ",
                value=getattr(st.session_state, 'sql_query', default_query),
                height=100,
                key="pg_input",
                help="SELECTクエリのみ実行可能です"
            )

        if st.button("実行", key="pg_exec"):
            if not sql_query.strip().upper().startswith('SELECT'):
                st.error("❌ 安全性のため、SELECTクエリのみ実行できます")
                return

            try:
                engine = sqlalchemy.create_engine(os.getenv('PG_CONN_STR'))

                with st.spinner("クエリを実行中..."):
                    df = pd.read_sql(sql_query, engine)

                if len(df) > 0:
                    st.success(f"✅ {len(df)}行のデータを取得しました")
                    st.dataframe(df, use_container_width=True)

                    # データ型情報の表示
                    with st.expander("📊 データ型情報", expanded=False):
                        dtype_info = pd.DataFrame({
                            'カラム名'  : df.columns,
                            'データ型'  : [str(dtype) for dtype in df.dtypes],
                            'NULL数'    : [df[col].isnull().sum() for col in df.columns],
                            'ユニーク数': [df[col].nunique() for col in df.columns]
                        })
                        st.dataframe(dtype_info, use_container_width=True)

                    # CSVダウンロード機能
                    csv = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label="📥 CSVダウンロード",
                        data=csv,
                        file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime='text/csv',
                        help="クエリ結果をCSVファイルとしてダウンロードします"
                    )
                else:
                    st.info("クエリの結果は空でした")

                engine.dispose()

            except Exception as e:
                st.error(f"❌ クエリ実行エラー: {e}")

                # エラーの詳細情報
                with st.expander("🔍 エラー詳細", expanded=False):
                    st.code(f"SQL: {sql_query}")
                    st.code(f"エラー: {str(e)}")

                    # よくあるエラーのヒント
                    error_str = str(e).lower()
                    if "does not exist" in error_str:
                        st.info("💡 ヒント: テーブルまたはカラムが存在しません。「テーブル一覧」クエリで確認してください。")
                    elif "syntax error" in error_str:
                        st.info("💡 ヒント: SQL構文エラーです。クエリを確認してください。")
                    elif "permission denied" in error_str:
                        st.info("💡 ヒント: 権限エラーです。データベースの権限設定を確認してください。")

    def _render_elasticsearch_query(self):
        """Elasticsearchクエリ機能"""
        st.subheader("🟡 Elasticsearch クエリ")

        search_term = st.text_input("検索キーワード", "Python")
        search_field = st.selectbox("検索対象フィールド", ["全フィールド", "title", "content", "category", "author"])

        if st.button("検索実行", key="es_exec"):
            es_manager = self.status_manager.get_manager('Elasticsearch')
            status = es_manager.check_connection()

            if "🟢" in status["status"]:
                hits = es_manager.search_articles(search_term, search_field)

                if hits:
                    st.success(f"🎯 {len(hits)}件の記事が見つかりました")

                    for hit in hits:
                        article = hit['_source']
                        score = hit['_score']

                        with st.expander(f"📝 {article['title']} (スコア: {score:.2f})"):
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write(f"**内容:** {article['content']}")

                                # ハイライト表示
                                if 'highlight' in hit:
                                    st.write("**ハイライト:**")
                                    for field, highlights in hit['highlight'].items():
                                        for highlight in highlights:
                                            st.markdown(f"• {highlight}", unsafe_allow_html=True)

                            with col2:
                                st.metric("閲覧数", f"{article['view_count']:,}")
                                st.write(f"**著者:** {article['author']}")
                                st.write(f"**カテゴリ:** {article['category']}")
                                st.write(f"**公開日:** {article['published_date']}")
                                st.write(f"**タグ:** {', '.join(article['tags'])}")
                else:
                    st.info(f"'{search_term}' に関する記事は見つかりませんでした")
            else:
                st.warning("Elasticsearch サーバーに接続できません")

    def _render_qdrant_query(self):
        """Qdrantクエリ機能"""
        st.subheader("🟠 Qdrant ベクトル検索")

        st.info("💡 実際のベクトル検索には埋め込みモデルが必要ですが、ここではテスト用の機能を提供します")

        col1, col2 = st.columns(2)

        with col1:
            search_category = st.selectbox("カテゴリで検索",
                                           ["全て", "エレクトロニクス", "キッチン家電", "ファッション", "スポーツ"])
            price_range = st.slider("価格帯", 0, 100000, (0, 100000), step=1000)

        with col2:
            limit = st.number_input("取得件数", min_value=1, max_value=20, value=5)

        if st.button("検索実行", key="qdrant_exec"):
            qdrant_manager = self.status_manager.get_manager('Qdrant')
            status = qdrant_manager.check_connection()

            if "🟢" in status["status"]:
                try:
                    # フィルター条件の構築
                    filter_conditions = []

                    if search_category != "全て":
                        filter_conditions.append({
                            "key"  : "category",
                            "match": {"value": search_category}
                        })

                    filter_conditions.extend([
                        {"key": "price", "range": {"gte": price_range[0]}},
                        {"key": "price", "range": {"lte": price_range[1]}}
                    ])

                    # 検索リクエスト
                    search_request = {
                        "filter"      : {
                            "must": filter_conditions
                        },
                        "limit"       : limit,
                        "with_payload": True
                    }

                    response = requests.post(
                        'http://localhost:6333/collections/product_embeddings/points/search',
                        json=search_request,
                        headers={'Content-Type': 'application/json'}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if 'result' in data and data['result']:
                            points = data['result']

                            st.success(f"🎯 {len(points)}件の商品が見つかりました")

                            # 商品一覧表示
                            products = []
                            for point in points:
                                product = point['payload']
                                product['id'] = point['id']
                                if 'score' in point:
                                    product['similarity_score'] = point['score']
                                products.append(product)

                            df_results = pd.DataFrame(products)
                            st.dataframe(df_results, use_container_width=True)

                            # 商品詳細カード
                            for product in products:
                                with st.expander(f"🛍️ {product['name']} - ¥{product['price']:,}"):
                                    col1, col2 = st.columns([2, 1])

                                    with col1:
                                        st.write(f"**説明:** {product['description']}")
                                        st.write(f"**カテゴリ:** {product['category']}")

                                    with col2:
                                        st.metric("価格", f"¥{product['price']:,}")
                                        if 'similarity_score' in product:
                                            st.metric("類似度スコア", f"{product['similarity_score']:.3f}")
                        else:
                            st.info("条件に合う商品は見つかりませんでした")
                    else:
                        st.error(f"検索に失敗しました (Status: {response.status_code})")

                except Exception as e:
                    st.error(f"エラー: {e}")
            else:
                st.warning("Qdrant サーバーに接続できません")


# ==================================================
# データ分析ページ
# ==================================================
class DataAnalysisPage(PageManager):
    """データ分析ダッシュボードページ"""

    def render(self):
        st.header("📈 データ分析とダッシュボード")

        # 必要なサーバーの確認
        status = self.status_manager.check_all_servers()
        required_servers = ['PostgreSQL', 'Redis']
        servers_ready = all("🟢" in status[server]["status"] for server in required_servers)

        if not servers_ready:
            st.warning("データ分析には PostgreSQL と Redis の接続が必要です")

            # 接続状況の詳細表示
            st.write("**現在の接続状況:**")
            for server in required_servers:
                if server in status:
                    st.write(f"- {server}: {status[server]['status']}")
                else:
                    st.write(f"- {server}: 状態不明")
            return

        try:
            # PostgreSQLのテーブル存在チェック
            if not self._check_postgresql_setup():
                return

            self._render_sales_analysis()
            self._render_customer_analysis()
            self._render_redis_statistics()
            self._render_advanced_analytics()
        except Exception as e:
            st.error(f"データ分析エラー: {e}")
            st.code(traceback.format_exc())

    def _check_postgresql_setup(self) -> bool:
        """PostgreSQLのセットアップ状況をチェック"""
        try:
            engine = sqlalchemy.create_engine(os.getenv('PG_CONN_STR'))

            # テーブルの存在確認
            tables_check = pd.read_sql("""
                                       SELECT table_name
                                       FROM information_schema.tables
                                       WHERE table_schema = 'public'
                                         AND table_type = 'BASE TABLE'
                                         AND table_name IN ('customers', 'orders', 'products')
                                       """, engine)

            existing_tables = set(tables_check['table_name'].tolist())
            required_tables = {'customers', 'orders', 'products'}
            missing_tables = required_tables - existing_tables

            engine.dispose()

            if missing_tables:
                st.warning(f"⚠️ データ分析に必要なテーブルが見つかりません: {', '.join(missing_tables)}")

                # セットアップ手順の表示
                with st.expander("💡 セットアップ手順", expanded=True):
                    st.markdown("""
                    **PostgreSQLテーブルの作成とテストデータ投入:**

                    1. **Dockerサービスの起動:**
                    ```bash
                    docker-compose -f docker-compose.mcp-demo.yml up -d postgres
                    ```

                    2. **テストデータの投入:**
                    ```bash
                    uv run python scripts/setup_test_data.py
                    ```

                    3. **手動でのテーブル確認:**
                    ```sql
                    -- PostgreSQLに接続
                    psql -h localhost -U testuser -d testdb

                    -- テーブル一覧表示
                    \dt

                    -- データ確認
                    SELECT COUNT(*) FROM customers;
                    SELECT COUNT(*) FROM orders;
                    SELECT COUNT(*) FROM products;
                    ```
                    """)

                # 現在の状況表示
                if existing_tables:
                    st.info(f"✅ 存在するテーブル: {', '.join(existing_tables)}")
                else:
                    st.error("❌ PostgreSQLにテーブルが1つも存在しません")

                return False
            else:
                st.success(f"✅ 全ての必要なテーブルが存在します: {', '.join(existing_tables)}")
                return True

        except Exception as e:
            st.error(f"PostgreSQLセットアップチェックエラー: {e}")

            with st.expander("🔍 詳細エラー情報", expanded=False):
                st.code(f"エラー: {str(e)}")
                st.code(f"接続文字列: {os.getenv('PG_CONN_STR', '未設定')}")

            return False

    def _table_exists(self, engine, table_name: str) -> bool:
        """テーブルの存在確認"""
        try:
            result = pd.read_sql(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """, engine)
            return result.iloc[0]['exists']
        except Exception:
            return False

    def _render_sales_analysis(self):
        """売上分析"""
        st.subheader("💰 売上分析")

        try:
            engine = sqlalchemy.create_engine(os.getenv('PG_CONN_STR'))

            # テーブルの存在を確認してからクエリ実行
            if not self._table_exists(engine, 'orders'):
                st.warning("ordersテーブルが存在しないため、売上分析をスキップします")
                engine.dispose()
                return

            col1, col2, col3 = st.columns(3)

            # 総売上
            try:
                total_sales = pd.read_sql("SELECT SUM(price * quantity) as total FROM orders", engine).iloc[0]['total']
                with col1:
                    if total_sales is not None:
                        st.metric("総売上", f"¥{total_sales:,.0f}")
                    else:
                        st.metric("総売上", "¥0")
            except Exception as e:
                with col1:
                    st.metric("総売上", f"エラー: {str(e)[:20]}")

            # 平均注文価格
            try:
                avg_order = pd.read_sql("SELECT AVG(price * quantity) as avg FROM orders", engine).iloc[0]['avg']
                with col2:
                    if avg_order is not None:
                        st.metric("平均注文価格", f"¥{avg_order:,.0f}")
                    else:
                        st.metric("平均注文価格", "¥0")
            except Exception as e:
                with col2:
                    st.metric("平均注文価格", f"エラー: {str(e)[:20]}")

            # 注文数
            try:
                order_count = pd.read_sql("SELECT COUNT(*) as count FROM orders", engine).iloc[0]['count']
                with col3:
                    st.metric("総注文数", f"{order_count:,}")
            except Exception as e:
                with col3:
                    st.metric("総注文数", f"エラー: {str(e)[:20]}")

            # 商品別売上
            try:
                st.subheader("📊 商品別売上")
                product_sales = pd.read_sql("""
                                            SELECT product_name,
                                                   SUM(price * quantity) as total_sales,
                                                   COUNT(*)              as order_count,
                                                   AVG(price * quantity) as avg_order_value
                                            FROM orders
                                            GROUP BY product_name
                                            ORDER BY total_sales DESC
                                            """, engine)

                if len(product_sales) > 0:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**売上金額**")
                        st.bar_chart(product_sales.set_index('product_name')['total_sales'])

                    with col2:
                        st.write("**注文件数**")
                        st.bar_chart(product_sales.set_index('product_name')['order_count'])

                    # 詳細テーブル
                    st.write("**商品別詳細データ**")
                    st.dataframe(product_sales, use_container_width=True)
                else:
                    st.info("商品データがありません")

            except Exception as e:
                st.error(f"商品別売上取得エラー: {e}")

            engine.dispose()

        except Exception as e:
            st.error(f"売上分析エラー: {e}")

    def _render_customer_analysis(self):
        """顧客分析"""
        st.subheader("👥 顧客分析")

        try:
            engine = sqlalchemy.create_engine(os.getenv('PG_CONN_STR'))

            # customersテーブルの存在確認
            if not self._table_exists(engine, 'customers'):
                st.warning("customersテーブルが存在しないため、顧客分析をスキップします")
                engine.dispose()
                return

            # ordersテーブルの存在確認
            orders_exists = self._table_exists(engine, 'orders')

            if orders_exists:
                # 両方のテーブルが存在する場合
                customer_stats = pd.read_sql("""
                                             SELECT c.city,
                                                    COUNT(c.id)                            as customer_count,
                                                    COUNT(o.id)                            as total_orders,
                                                    COALESCE(SUM(o.price * o.quantity), 0) as total_spent,
                                                    COALESCE(AVG(o.price * o.quantity), 0) as avg_order_value
                                             FROM customers c
                                                      LEFT JOIN orders o ON c.id = o.customer_id
                                             GROUP BY c.city
                                             ORDER BY total_spent DESC
                                             """, engine)
            else:
                # customersテーブルのみ存在する場合
                customer_stats = pd.read_sql("""
                                             SELECT city,
                                                    COUNT(id) as customer_count,
                                                    0         as total_orders,
                                                    0         as total_spent,
                                                    0         as avg_order_value
                                             FROM customers
                                             GROUP BY city
                                             ORDER BY customer_count DESC
                                             """, engine)

            if len(customer_stats) > 0:
                col1, col2 = st.columns(2)

                with col1:
                    st.write("**都市別顧客数**")
                    st.bar_chart(customer_stats.set_index('city')['customer_count'])

                with col2:
                    if orders_exists:
                        st.write("**都市別売上**")
                        st.bar_chart(customer_stats.set_index('city')['total_spent'])
                    else:
                        st.write("**売上データなし**")
                        st.info("ordersテーブルが存在しないため売上データを表示できません")

                # 顧客分析詳細
                st.write("**都市別詳細データ**")
                st.dataframe(customer_stats, use_container_width=True)

                # 上位顧客分析（ordersテーブルが存在する場合のみ）
                if orders_exists:
                    top_customers = pd.read_sql("""
                                                SELECT c.name,
                                                       c.city,
                                                       c.email,
                                                       COUNT(o.id)               as order_count,
                                                       SUM(o.price * o.quantity) as total_spent
                                                FROM customers c
                                                         JOIN orders o ON c.id = o.customer_id
                                                GROUP BY c.id, c.name, c.city, c.email
                                                ORDER BY total_spent DESC
                                                LIMIT 10
                                                """, engine)

                    if len(top_customers) > 0:
                        st.write("**上位顧客 Top 10**")
                        st.dataframe(top_customers, use_container_width=True)
            else:
                st.info("顧客データがありません")

            engine.dispose()

        except Exception as e:
            st.error(f"顧客分析エラー: {e}")

    def _render_redis_statistics(self):
        """Redis統計"""
        st.subheader("🔴 Redis 統計")

        try:
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                active_sessions = len(r.keys('session:*'))
                st.metric("アクティブセッション", active_sessions)

            with col2:
                page_views = r.get('counter:page_views') or 0
                st.metric("ページビュー", f"{page_views:,}")

            with col3:
                search_count = r.llen('search:recent')
                st.metric("検索履歴数", search_count)

            # Redis詳細統計
            st.write("**Redis詳細統計**")

            # メモリ使用量（info commandの結果をパース）
            redis_info = r.info()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                used_memory = redis_info.get('used_memory_human', 'N/A')
                st.metric("使用メモリ", used_memory)

            with col2:
                connected_clients = redis_info.get('connected_clients', 0)
                st.metric("接続クライアント数", connected_clients)

            with col3:
                total_commands = redis_info.get('total_commands_processed', 0)
                st.metric("総コマンド数", f"{total_commands:,}")

            with col4:
                uptime_days = redis_info.get('uptime_in_days', 0)
                st.metric("稼働日数", f"{uptime_days}日")

        except Exception as e:
            st.error(f"Redis統計取得エラー: {e}")

    def _render_advanced_analytics(self):
        """高度な分析"""
        st.subheader("🔬 高度な分析")

        try:
            engine = sqlalchemy.create_engine(os.getenv('PG_CONN_STR'))

            # ordersテーブルが存在しない場合はスキップ
            if not self._table_exists(engine, 'orders'):
                st.warning("ordersテーブルが存在しないため、高度な分析をスキップします")
                engine.dispose()
                return

            # 時系列分析（もしorder_dateがあれば）
            try:
                daily_sales = pd.read_sql("""
                                          SELECT DATE(order_date)      as date,
                                                 COUNT(*)              as order_count,
                                                 SUM(price * quantity) as daily_sales
                                          FROM orders
                                          WHERE order_date IS NOT NULL
                                          GROUP BY DATE(order_date)
                                          ORDER BY date
                                          """, engine)

                if len(daily_sales) > 0:
                    st.write("**日次売上推移**")
                    st.line_chart(daily_sales.set_index('date')['daily_sales'])

                    st.write("**日次注文数推移**")
                    st.line_chart(daily_sales.set_index('date')['order_count'])
                else:
                    st.info("時系列データがありません（order_dateカラムが空またはNULL）")
            except Exception as e:
                st.info(f"時系列分析はスキップされました: {str(e)[:50]}")

            # 商品カテゴリ分析
            try:
                # productsテーブルの存在確認
                if self._table_exists(engine, 'products'):
                    category_analysis = pd.read_sql("""
                                                    SELECT p.category,
                                                           COUNT(DISTINCT p.id)                   as product_count,
                                                           COALESCE(SUM(o.price * o.quantity), 0) as total_sales,
                                                           COALESCE(COUNT(o.id), 0)               as order_count
                                                    FROM products p
                                                             LEFT JOIN orders o ON p.name = o.product_name
                                                    GROUP BY p.category
                                                    ORDER BY total_sales DESC
                                                    """, engine)

                    if len(category_analysis) > 0:
                        st.write("**カテゴリ別分析**")
                        st.dataframe(category_analysis, use_container_width=True)
                    else:
                        st.info("カテゴリ分析データがありません")
                else:
                    st.info("productsテーブルが存在しないため、カテゴリ分析をスキップします")
            except Exception as e:
                st.info(f"カテゴリ分析はスキップされました: {str(e)[:50]}")

            engine.dispose()

        except Exception as e:
            st.error(f"高度な分析エラー: {e}")


# ==================================================
# 設定ページ
# ==================================================
class SettingsPage(PageManager):
    """設定とヘルプページ"""

    def render(self):
        st.header("⚙️ 設定とヘルプ")

        # システム情報
        self._render_system_info()

        # パフォーマンス情報
        self._render_performance_info()

        # Docker コマンド
        self._render_docker_commands()

        # MCP エンドポイント情報
        self._render_mcp_endpoints()

        # トラブルシューティング
        self._render_troubleshooting()

        # アプリ情報
        self._render_app_info()

    def _render_system_info(self):
        """システム情報の表示"""
        st.subheader("🖥️ システム情報")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**環境変数:**")
            env_status = {
                "OPENAI_API_KEY": "設定済み" if os.getenv('OPENAI_API_KEY') else "❌ 未設定",
                "REDIS_URL"     : os.getenv('REDIS_URL', '未設定'),
                "PG_CONN_STR"   : "設定済み" if os.getenv('PG_CONN_STR') else "❌ 未設定",
                "ELASTIC_URL"   : os.getenv('ELASTIC_URL', 'http://localhost:9200'),
                "QDRANT_URL"    : os.getenv('QDRANT_URL', 'http://localhost:6333')
            }

            for key, value in env_status.items():
                if "❌" in str(value):
                    st.error(f"**{key}**: {value}")
                else:
                    st.success(f"**{key}**: {value}")

        with col2:
            st.write("**サーバー接続状況:**")
            status = self.status_manager.check_all_servers()
            for server, state in status.items():
                if "🟢" in state["status"]:
                    st.success(f"**{server}**: 接続OK")
                    if "details" in state:
                        st.caption(f"詳細: {state['details']}")
                else:
                    st.error(f"**{server}**: 接続NG")
                    if "details" in state:
                        st.caption(f"詳細: {state['details']}")

    def _render_performance_info(self):
        """パフォーマンス情報の表示"""
        st.subheader("⚡ パフォーマンス情報")

        # セッション状態のサイズ
        session_size = len(st.session_state)
        st.metric("セッション変数数", session_size)

        # キャッシュ情報
        if hasattr(st, 'cache_data'):
            st.info("Streamlitキャッシュが有効です")

        # メモリ使用量（可能であれば）
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            st.metric("メモリ使用量", f"{memory_mb:.1f} MB")
        except ImportError:
            st.info("詳細なパフォーマンス情報にはpsutilが必要です")
        except Exception:
            st.info("パフォーマンス情報を取得できませんでした")

    def _render_docker_commands(self):
        """Docker管理コマンドの表示"""
        st.subheader("🐳 Docker 管理コマンド")

        command_tabs = st.tabs(["起動", "停止", "ログ確認", "データリセット"])

        with command_tabs[0]:
            st.write("**データベース起動:**")
            st.code("docker-compose -f docker-compose.mcp-demo.yml up -d redis postgres elasticsearch qdrant")

            st.write("**MCPサーバー起動:**")
            st.code("docker-compose -f docker-compose.mcp-demo.yml up -d redis-mcp postgres-mcp es-mcp qdrant-mcp")

            st.write("**全サービス起動:**")
            st.code("docker-compose -f docker-compose.mcp-demo.yml up -d")

        with command_tabs[1]:
            st.write("**全サービス停止:**")
            st.code("docker-compose -f docker-compose.mcp-demo.yml down")

            st.write("**ボリューム削除（データも削除）:**")
            st.code("docker-compose -f docker-compose.mcp-demo.yml down -v")

        with command_tabs[2]:
            st.write("**全サービスのログ:**")
            st.code("docker-compose -f docker-compose.mcp-demo.yml logs -f")

            st.write("**特定サービスのログ:**")
            st.code("docker-compose -f docker-compose.mcp-demo.yml logs -f redis-mcp")

        with command_tabs[3]:
            st.write("**テストデータ再投入:**")
            st.code("uv run python scripts/setup_test_data.py")

            st.write("**完全リセット:**")
            st.code("""
# 停止してボリューム削除  
docker-compose -f docker-compose.mcp-demo.yml down -v

# 再起動
docker-compose -f docker-compose.mcp-demo.yml up -d

# データ再投入
uv run python scripts/setup_test_data.py
            """)

    def _render_mcp_endpoints(self):
        """MCPエンドポイント情報の表示"""
        st.subheader("🌐 MCP エンドポイント")

        mcp_endpoints = {
            "Redis MCP"        : "http://localhost:8000/mcp",
            "PostgreSQL MCP"   : "http://localhost:8001/mcp",
            "Elasticsearch MCP": "http://localhost:8002/mcp",
            "Qdrant MCP"       : "http://localhost:8003/mcp"
        }

        st.json(mcp_endpoints)

        # エンドポイントのヘルスチェック
        st.write("**エンドポイントヘルスチェック:**")
        for name, url in mcp_endpoints.items():
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    st.success(f"{name}: 🟢 応答OK")
                else:
                    st.warning(f"{name}: 🟡 応答あり (Status: {response.status_code})")
            except Exception:
                st.error(f"{name}: 🔴 応答なし")

    def _render_troubleshooting(self):
        """トラブルシューティングの表示"""
        st.subheader("🔧 トラブルシューティング")

        with st.expander("❓ よくある問題と解決方法"):
            st.markdown("""
            **🔴 Redis 接続エラー**
            - Dockerコンテナが起動しているか確認: `docker ps | grep redis`
            - ポート6379が使用中でないか確認: `lsof -i :6379`
            - Redis設定ファイルの確認: `docker logs redis`

            **🟦 PostgreSQL 接続エラー**
            - 認証情報を確認: `testuser/testpass`
            - データベース初期化を確認: `docker-compose logs postgres`
            - 接続文字列の確認: `PG_CONN_STR`環境変数

            **🟡 Elasticsearch 接続エラー**
            - メモリ不足の可能性: `docker stats`
            - Java heap size設定を確認: `ES_JAVA_OPTS=-Xms512m -Xmx512m`
            - インデックスの確認: `curl http://localhost:9200/_cat/indices`

            **🟠 Qdrant 接続エラー**
            - コンテナの起動状況: `docker-compose ps qdrant`
            - ヘルスチェック: `curl http://localhost:6333/`
            - コレクションの確認: `curl http://localhost:6333/collections`

            **🤖 OpenAI API エラー**
            - APIキーの設定確認: `.env`ファイルの`OPENAI_API_KEY`
            - クォータ制限の確認: OpenAIダッシュボード
            - ネットワーク接続の確認

            **🐳 Docker関連エラー**
            - Docker Daemonの起動確認: `docker info`
            - ディスク容量の確認: `docker system df`
            - ポート競合の確認: `netstat -tulpn | grep :6379`

            **💾 データ関連エラー**
            - データ初期化: `scripts/setup_test_data.py`の実行
            - ボリュームの再作成: `docker-compose down -v && docker-compose up -d`
            """)

        # 自動診断機能
        with st.expander("🔍 自動診断"):
            if st.button("システム診断を実行"):
                self._run_system_diagnosis()

    def _run_system_diagnosis(self):
        """システム自動診断"""
        st.write("**システム診断を実行中...**")

        diagnosis_results = []

        # Docker確認
        try:
            import subprocess
            result = subprocess.run(['docker', '--version'],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                diagnosis_results.append("✅ Docker: インストール済み")
            else:
                diagnosis_results.append("❌ Docker: 問題あり")
        except Exception:
            diagnosis_results.append("❌ Docker: アクセスできません")

        # データベース接続確認
        status = self.status_manager.check_all_servers()
        for server, state in status.items():
            if "🟢" in state["status"]:
                diagnosis_results.append(f"✅ {server}: 接続OK")
            else:
                diagnosis_results.append(f"❌ {server}: 接続NG")

        # 環境変数確認
        required_env_vars = ['OPENAI_API_KEY', 'PG_CONN_STR']
        for var in required_env_vars:
            if os.getenv(var):
                diagnosis_results.append(f"✅ {var}: 設定済み")
            else:
                diagnosis_results.append(f"❌ {var}: 未設定")

        # 結果表示
        for result in diagnosis_results:
            if "✅" in result:
                st.success(result)
            else:
                st.error(result)

    def _render_app_info(self):
        """アプリケーション情報の表示"""
        st.subheader("ℹ️ アプリケーション情報")

        app_info = {
            "バージョン"    : "2.0.0-refactored",
            "作成日"        : "2024-01-15",
            "最終更新"      : "2025-01-28",
            "Python"        : "3.11+",
            "Streamlit"     : st.__version__,
            "使用技術"      : ["Docker", "Redis", "PostgreSQL", "Elasticsearch", "Qdrant", "OpenAI API"],
            "アーキテクチャ": "モジュラー設計",
            "主要改善点"    : [
                "1,100行から50行のメインファイルに削減",
                "クラスベースの設計",
                "機能別モジュール分割",
                "保守性・拡張性の向上"
            ]
        }

        st.json(app_info)

        # ライセンス情報
        with st.expander("📄 ライセンス・著作権情報"):
            st.markdown("""
            **MIT License**

            Copyright (c) 2025 MCP Demo Application

            本ソフトウェアおよび関連文書ファイル（以下「ソフトウェア」）のコピーを取得する
            すべての人に対し、ソフトウェアを無制限に扱うことを無償で許可します。

            **使用しているオープンソースライブラリ:**
            - Streamlit (Apache License 2.0)
            - Pandas (BSD License)
            - Redis-py (MIT License)
            - SQLAlchemy (MIT License)
            - その他requirements.txtに記載のライブラリ
            """)


# ==================================================
# エクスポート
# ==================================================
__all__ = [
    'DirectQueryPage',
    'DataAnalysisPage',
    'SettingsPage',
]
