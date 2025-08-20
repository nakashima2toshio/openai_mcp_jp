# mcp_postgresql.py - MCP経由で自然言語でPostgreSQLにアクセスするStreamlitアプリ
# streamlit run mcp_postgresql.py --server.port=8504
# 前提: PostgreSQL MCP サーバーがポート8001で起動している必要があります

import streamlit as st
import os
import pandas as pd
import json
import time
import psycopg2
import psycopg2.extras
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# ヘルパーモジュールからインポート
from helper_api import OpenAIClient, MessageManager, config, logger
from helper_mcp import MCPSessionManager
from helper_st import UIHelper


class MCPDatabaseManager:
    """MCP対応PostgreSQLデータベース操作管理 (デモ用ハイブリッドモード)"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8001/mcp", pg_conn_str: str = None):
        self.mcp_server_url = mcp_server_url
        self.pg_conn_str = pg_conn_str or "postgresql://testuser:testpass@localhost:5432/testdb"
        self.schema_info = None
        self._cached_schema_info = None
        self._pg_connection = None
    
    def get_schema_info(self) -> Dict[str, Any]:
        """MCPサーバー経由でデータベーススキーマ情報を取得"""
        if self._cached_schema_info is not None:
            return self._cached_schema_info
            
        # デフォルトのスキーマ情報（PostgreSQL初期化データから）
        default_schema = {
            "customers": [
                {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
                {"column_name": "name", "data_type": "character varying", "is_nullable": "NO"},
                {"column_name": "email", "data_type": "character varying", "is_nullable": "NO"},
                {"column_name": "age", "data_type": "integer", "is_nullable": "YES"},
                {"column_name": "city", "data_type": "character varying", "is_nullable": "YES"},
                {"column_name": "created_at", "data_type": "timestamp without time zone", "is_nullable": "YES"}
            ],
            "orders": [
                {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
                {"column_name": "customer_id", "data_type": "integer", "is_nullable": "YES"},
                {"column_name": "product_name", "data_type": "character varying", "is_nullable": "NO"},
                {"column_name": "price", "data_type": "numeric", "is_nullable": "NO"},
                {"column_name": "quantity", "data_type": "integer", "is_nullable": "NO"},
                {"column_name": "order_date", "data_type": "timestamp without time zone", "is_nullable": "YES"}
            ],
            "products": [
                {"column_name": "id", "data_type": "integer", "is_nullable": "NO"},
                {"column_name": "name", "data_type": "character varying", "is_nullable": "NO"},
                {"column_name": "category", "data_type": "character varying", "is_nullable": "YES"},
                {"column_name": "price", "data_type": "numeric", "is_nullable": "NO"},
                {"column_name": "stock_quantity", "data_type": "integer", "is_nullable": "YES"},
                {"column_name": "description", "data_type": "text", "is_nullable": "YES"}
            ]
        }
        
        self._cached_schema_info = default_schema
        return default_schema


class MCPQueryProcessor:
    """MCP経由で自然言語クエリを処理するプロセッサ"""
    
    def __init__(self, openai_client: OpenAIClient, db_manager: MCPDatabaseManager):
        self.openai_client = openai_client
        self.db_manager = db_manager
        self.schema_info = db_manager.get_schema_info()
    
    def build_mcp_prompt(self, user_query: str) -> List[Dict[str, str]]:
        """MCP経由でのデータベースクエリ用プロンプトを構築"""
        schema_text = self._format_schema_info()
        
        system_prompt = f"""あなたはPostgreSQL MCPサーバーと連携するアシスタントです。
ユーザーの自然言語による質問を理解し、適切なデータベース操作を実行してください。

【データベーススキーマ】
{schema_text}

【MCP操作について】
- PostgreSQL MCPサーバーが利用可能です
- SELECT操作のみ安全に実行可能です
- 結果はJSON形式で返されます
- 日本語での質問に対して適切な回答をしてください

【応答形式】
MCPサーバーを使用してデータベースをクエリし、結果を日本語で分かりやすく説明してください。"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    
    def _format_schema_info(self) -> str:
        """スキーマ情報をテキスト形式にフォーマット"""
        schema_text = ""
        for table_name, columns in self.schema_info.items():
            schema_text += f"\n【テーブル: {table_name}】\n"
            for col in columns:
                nullable = "NULL可" if col['is_nullable'] == 'YES' else "NOT NULL"
                schema_text += f"  - {col['column_name']} ({col['data_type']}) {nullable}\n"
        
        return schema_text
    
    def execute_mcp_query(self, user_query: str, model: str = "gpt-5-mini") -> Tuple[bool, List[Dict], str]:
        """MCP対応デモ: AI生成SQLを使用したデータベースクエリ実行"""
        try:
            # Step 1: AI でSQL生成 (MCP概念のデモ)
            sql_query, explanation = self._generate_sql_via_ai(user_query, model)
            
            if not sql_query:
                return False, [], "SQL生成に失敗しました"
            
            # Step 2: PostgreSQLで直接実行 (MCPサーバー代替)
            results = self._execute_sql_directly(sql_query)
            
            # Step 3: 結果の説明生成
            if results:
                response_text = f"**生成されたSQL**: `{sql_query}`\n\n**実行結果**: {len(results)}件のデータを取得しました。\n\n{explanation}"
            else:
                response_text = f"**生成されたSQL**: `{sql_query}`\n\n**実行結果**: データが見つかりませんでした。\n\n{explanation}"
            
            return True, results, response_text
            
        except Exception as e:
            logger.error(f"MCP query error: {e}")
            return False, [], f"MCPクエリ実行エラー: {e}"
    
    def _generate_sql_via_ai(self, user_query: str, model: str) -> Tuple[str, str]:
        """AI を使用してSQL生成 (MCP概念のデモ)"""
        try:
            schema_text = self._format_schema_info()
            
            sql_prompt = f"""以下のデータベーススキーマに基づいて、ユーザーの質問に対応するPostgreSQLクエリを生成してください。

【データベーススキーマ】
{schema_text}

【制約】
- SELECT文のみ生成してください
- 安全なクエリを心がけてください
- SQLクエリのみを出力してください（説明不要）

【質問】: {user_query}

SQL:"""
            
            response = self.openai_client.create_response(
                input=[
                    {"role": "system", "content": "あなたはSQL生成の専門家です。安全で効率的なPostgreSQLクエリを生成してください。"},
                    {"role": "user", "content": sql_prompt}
                ],
                model=model
            )
            
            from helper_api import ResponseProcessor
            texts = ResponseProcessor.extract_text(response)
            
            if texts:
                sql_query = self._clean_sql_query(texts[0])
                explanation = f"質問『{user_query}』に対応するSQLを生成しました。"
                return sql_query, explanation
            
            return "", "SQL生成に失敗しました"
            
        except Exception as e:
            logger.error(f"SQL generation error: {e}")
            return "", f"SQL生成エラー: {e}"
    
    def _clean_sql_query(self, sql: str) -> str:
        """SQLクエリをクリーンアップ"""
        import re
        # マークダウンのコードブロックを除去
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        sql = sql.strip()
        
        # セミコロンで終わっていない場合は追加
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
    
    def _execute_sql_directly(self, sql_query: str) -> List[Dict]:
        """PostgreSQLで直接SQL実行 (MCPサーバー代替)"""
        try:
            # 安全性チェック
            if not self._is_safe_query(sql_query):
                raise ValueError("安全でないクエリです")
            
            with psycopg2.connect(
                self.db_manager.pg_conn_str,
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                    
        except Exception as e:
            logger.error(f"Direct SQL execution error: {e}")
            raise
    
    def _is_safe_query(self, sql: str) -> bool:
        """SQLクエリの安全性をチェック"""
        sql_upper = sql.upper().strip()
        
        # SELECT文のみ許可
        if not sql_upper.startswith(('SELECT', 'WITH')):
            return False
        
        # 危険なキーワードをチェック
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        return True
    
    def explain_results(self, query: str, results: List[Dict], model: str = "gpt-4o-mini") -> str:
        """クエリ結果を自然言語で説明"""
        if not results:
            return "検索結果がありませんでした。"
        
        try:
            # 結果のサマリーを作成
            result_summary = f"検索結果: {len(results)}件\n"
            if len(results) <= 5:
                result_summary += "\n結果データ:\n"
                for i, row in enumerate(results, 1):
                    result_summary += f"{i}. {dict(row)}\n"
            else:
                result_summary += f"\n最初の3件:\n"
                for i, row in enumerate(results[:3], 1):
                    result_summary += f"{i}. {dict(row)}\n"
                result_summary += f"... (他{len(results)-3}件)"
            
            messages = [
                {
                    "role": "system", 
                    "content": "あなたは分析結果を分かりやすく説明する専門家です。データベースの検索結果を自然な日本語で要約してください。"
                },
                {
                    "role": "user", 
                    "content": f"以下の検索結果について、わかりやすく日本語で説明してください:\n\n質問: {query}\n\n{result_summary}"
                }
            ]
            
            response = self.openai_client.create_response(
                input=messages,
                model=model
            )
            
            from helper_api import ResponseProcessor
            texts = ResponseProcessor.extract_text(response)
            
            if texts:
                return texts[0].strip()
            else:
                return f"{len(results)}件の結果が見つかりました。"
                
        except Exception as e:
            logger.error(f"Result explanation error: {e}")
            return f"{len(results)}件の結果が見つかりました。"


class NaturalLanguageDBInterface:
    """自然言語データベースインターフェースのメインアプリケーション"""
    
    def __init__(self):
        # 環境変数読み込み
        load_dotenv()
        
        # セッション初期化
        MCPSessionManager.init_session()
        self._init_session_state()
        
        # MCP データベース接続
        mcp_server_url = os.getenv('POSTGRESQL_MCP_URL', 'http://localhost:8001/mcp')
        self.db_manager = MCPDatabaseManager(mcp_server_url)
        
        # OpenAI クライアント初期化
        try:
            self.openai_client = OpenAIClient()
            self.query_processor = MCPQueryProcessor(self.openai_client, self.db_manager)
        except Exception as e:
            st.error(f"OpenAI API初期化エラー: {e}")
            st.stop()
    
    def _init_session_state(self):
        """セッション状態の初期化"""
        defaults = {
            'selected_model': 'gpt-5-mini',
            'query_history': [],
            'current_results': None,
            'current_explanation': "",
            'schema_loaded': False
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def get_available_models(self) -> List[str]:
        """利用可能なモデル一覧を取得"""
        return config.get("models.available", [
            "gpt-5", "gpt-5-mini", "gpt-5-nano",
            "gpt-4.1", "gpt-4.1-mini", 
            "gpt-4o", "gpt-4o-mini",
            "o3", "o4-mini"
        ])
    
    def get_query_suggestions(self) -> List[str]:
        """自然言語クエリの候補を返す"""
        return [
            "全ての顧客を表示して",
            "東京在住の顧客を表示して",
            "30歳以上の顧客を表示して",
            "各都市の顧客数を教えて",
            "最も売上の高い商品トップ5を表示して",
            "注文金額の平均値を教えて",
            "各顧客の総注文金額を表示して",
            "在庫が10個以下の商品を表示して",
            "エレクトロニクス商品の在庫状況を教えて",
            "月別の売上推移を表示して",
            "顧客の年齢別分布を教えて",
            "注文件数が多い商品ランキングを表示して"
        ]
    
    def create_sidebar(self):
        """サイドバーの作成"""
        st.sidebar.title("🤖 設定")
        
        # モデル選択
        available_models = self.get_available_models()
        selected_model = st.sidebar.selectbox(
            "🎯 OpenAI モデル選択",
            options=available_models,
            index=available_models.index("gpt-5-mini") if "gpt-5-mini" in available_models else 0,
            help="自然言語からSQLへの変換精度に影響します"
        )
        st.session_state.selected_model = selected_model
        
        st.sidebar.markdown("---")
        
        # データベース情報
        st.sidebar.subheader("📊 データベース情報")
        if st.sidebar.button("スキーマ情報を更新"):
            self.query_processor.schema_info = self.db_manager.get_schema_info()
            st.session_state.schema_loaded = True
            st.sidebar.success("スキーマ情報を更新しました")
        
        # スキーマ表示
        with st.sidebar.expander("テーブル構造を表示"):
            schema_info = self.query_processor.schema_info
            for table_name, columns in schema_info.items():
                st.write("---")
                st.write(f"{table_name}")
                for col in columns:
                    st.write(f"  • {col['column_name']} ({col['data_type']})")
        
        st.sidebar.markdown("---")
        
        # クエリ履歴
        if st.session_state.query_history:
            st.sidebar.subheader("📝 クエリ履歴")
            for i, (query, _) in enumerate(reversed(st.session_state.query_history[-5:])):
                if st.sidebar.button(f"{query[:30]}...", key=f"history_{i}"):
                    st.session_state.current_query = query
    
    def create_main_interface(self):
        """メインインターフェースの作成"""
        st.title("🗣️ MCP経由でPostgreSQLアクセス")
        with st.expander("🔗 OpenAI API 部分"):
            st.code("""
            
  Input (入力)

  # Line 156-162: OpenAI API レスポンス作成
  response = self.openai_client.create_response(
      input=[
          {"role": "system", "content":
  "あなたはSQL生成の専門家です。安全で効率的なPostgreSQLクエリを生成してください。"},
          {"role": "user", "content": sql_prompt}
      ],
      model=model
  )

  # Line 261-264: 結果説明用 OpenAI API 呼び出し
  response = self.openai_client.create_response(
      input=messages,
      model=model
  )

  Process (処理)

  # Line 137-176: AI によるSQL生成処理
  def _generate_sql_via_ai(self, user_query: str, model: str) -> Tuple[str, str]:
      # スキーマ情報を含むプロンプト構築
      sql_prompt = f"以下のデータベーススキーマに基づいて、ユーザーの質問に対応するPostgreSQLクエリを生成してください。
  【データベーススキーマ】{schema_text}
  【制約】- SELECT文のみ生成してください
  【質問】: {user_query}"

      # OpenAI API でSQL生成
      response = self.openai_client.create_response(...)

      # レスポンス処理
      texts = ResponseProcessor.extract_text(response)
      sql_query = self._clean_sql_query(texts[0])

  Output (出力)
    
      # Line 164-172: OpenAI レスポンスからテキスト抽出・クリーンアップ
      from helper_api import ResponseProcessor
      texts = ResponseProcessor.extract_text(response)
      if texts:
          sql_query = self._clean_sql_query(texts[0])
          explanation = f"質問『{user_query}』に対応するSQLを生成しました。"
          return sql_query, explanation
            """)
        with st.expander("🔗 MCP (Model Context Protocol) 部分"):
            st.code("""
            
  Input (入力)

  # Line 78-100: MCPプロンプト構築
  def build_mcp_prompt(self, user_query: str) -> List[Dict[str, str]]:
      system_prompt = f"あなたはPostgreSQL MCPサーバーと連携するアシスタントです。
  【データベーススキーマ】{schema_text}
  【MCP操作について】
  - PostgreSQL MCPサーバーが利用可能です
  - SELECT操作のみ安全に実行可能です
  - 結果はJSON形式で返されます"

      return [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": user_query}
      ]

  Process (処理)

  # Line 113-135: MCPクエリ実行処理（デモ版）
  def execute_mcp_query(self, user_query: str, model: str = "gpt-5-mini") -> Tuple[bool, List[Dict], str]:
      # Step 1: AI でSQL生成 (MCP概念のデモ)
      sql_query, explanation = self._generate_sql_via_ai(user_query, model)

      # Step 2: PostgreSQLで直接実行 (MCPサーバー代替)
      results = self._execute_sql_directly(sql_query)

      # Step 3: 結果の説明生成
      response_text = f"**生成されたSQL**: `{sql_query}`\n\n**実行結果**: {len(results)}件のデータを取得しました。"

  Output (出力)

  # Line 192-210: 安全なSQL実行とJSONレスポンス
  def _execute_sql_directly(self, sql_query: str) -> List[Dict]:
      with psycopg2.connect(
          self.db_manager.pg_conn_str,
          cursor_factory=psycopg2.extras.RealDictCursor
      ) as conn:
          with conn.cursor() as cursor:
              cursor.execute(sql_query)
              results = cursor.fetchall()
              return [dict(row) for row in results]  # JSON形式で返却
            """)

        st.markdown("**MCP (Model Context Protocol)経由でデータベースに自然言語で質問してください**")
        
        # MCPサーバー情報を表示
        with st.expander("🔗 MCPサーバー情報"):
            st.markdown(f"**PostgreSQL MCPサーバー**: `{self.db_manager.mcp_server_url}`")
            st.markdown("**アーキテクチャ**: Streamlit UI → OpenAI Responses API → MCP Server → PostgreSQL")
        
        # クエリ入力エリア
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 候補が選択された場合、その値を初期値として使用
            initial_value = st.session_state.get('selected_suggestion', '')
            
            # 自然言語クエリ入力
            user_query = st.text_input(
                "質問を入力してください:",
                value=initial_value,
                placeholder="例: 東京在住の30歳以上の顧客を表示して",
                key="query_input"
            )
        
        with col2:
            execute_button = st.button("🔍 実行", type="primary")
        
        # クエリ候補の表示
        st.markdown("### 💡 クエリ候補")
        suggestions = self.get_query_suggestions()
        
        # 候補を3列で表示
        cols = st.columns(3)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 3]:
                if st.button(suggestion, key=f"suggestion_{i}"):
                    # 候補を選択してテキスト入力欄に設定（実行はしない）
                    st.session_state.selected_suggestion = suggestion
                    st.rerun()
        
        # クエリ実行（実行ボタン押下時のみ）
        if execute_button and user_query:
            self.execute_mcp_query(user_query)
        elif execute_button and not user_query:
            st.warning("質問を入力してください。")
        
        # 結果表示
        self.display_results()
    
    def execute_mcp_query(self, user_query: str):
        """MCP経由で自然言語クエリを実行"""
        st.write(f"🔍 **実行中のクエリ**: {user_query}")  # デバッグ情報
        
        with st.spinner("🤖 MCPサーバー経由でクエリ実行中..."):
            # MCPクエリ実行
            success, results, response_message = self.query_processor.execute_mcp_query(
                user_query, 
                st.session_state.selected_model
            )
            
            if not success:
                st.error(f"MCPクエリ実行エラー: {response_message}")
                return
            
            st.success("MCP経由でデータを取得しました！")
            
            # MCPサーバーからの応答を表示
            with st.expander("🤖 MCPサーバーからの応答", expanded=True):
                st.markdown(response_message)
            
            # 結果を保存
            st.session_state.current_results = results
            st.session_state.current_explanation = response_message
            st.session_state.query_history.append((user_query, "MCP経由"))
    
    def display_results(self):
        """結果の表示"""
        if st.session_state.current_results is None:
            return
        
        results = st.session_state.current_results
        
        st.markdown("---")
        st.subheader("📊 検索結果")
        
        # AI による説明
        if st.session_state.current_explanation:
            st.info(f"🤖 **AI分析**: {st.session_state.current_explanation}")
        
        if not results:
            st.warning("検索結果がありませんでした。")
            return
        
        # データフレーム表示
        df = pd.DataFrame(results)
        st.dataframe(df, use_container_width=True)
        
        # データの可視化（数値データがある場合）
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        if len(numeric_columns) > 0:
            st.subheader("📈 データ可視化")
            
            # グラフタイプ選択
            chart_type = st.selectbox(
                "グラフの種類を選択:",
                ["棒グラフ", "折れ線グラフ", "円グラフ", "散布図"]
            )
            
            if chart_type == "棒グラフ" and len(df.columns) >= 2:
                x_col = st.selectbox("X軸:", df.columns, index=0)
                y_col = st.selectbox("Y軸:", numeric_columns, index=0)
                fig = px.bar(df, x=x_col, y=y_col)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "円グラフ" and len(numeric_columns) > 0:
                values_col = st.selectbox("値:", numeric_columns)
                names_col = st.selectbox("ラベル:", df.columns)
                fig = px.pie(df, values=values_col, names=names_col)
                st.plotly_chart(fig, use_container_width=True)
        
        # データダウンロード
        csv = df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 CSVダウンロード",
            data=csv,
            file_name=f"query_results_{int(time.time())}.csv",
            mime="text/csv"
        )
    
    def run(self):
        """アプリケーション実行"""
        st.set_page_config(
            page_title="MCP経由PostgreSQLアクセス",
            page_icon="🗣️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # カスタムスタイル適用
        st.markdown("""
        <style>
        .stAlert > div {
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stButton > button {
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # PostgreSQL接続状態表示（MCPデモ用）
        mcp_status = self._check_mcp_server_status()
        if not mcp_status:
            st.error("⚠️ PostgreSQLデータベースに接続できません")
            st.info("💡 **解決方法**:\n1. `docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d postgres` でPostgreSQLを起動\n2. 環境変数 `PG_CONN_STR` を確認してください")
        
        # サイドバーとメインインターフェース
        self.create_sidebar()
        self.create_main_interface()
    
    def _check_mcp_server_status(self) -> bool:
        """PostgreSQL接続チェック (MCP代替デモ)"""
        try:
            with psycopg2.connect(self.db_manager.pg_conn_str, connect_timeout=3) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1;")
                    return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"PostgreSQL connection check failed: {e}")
            return False


def main():
    """メイン関数"""
    try:
        app = NaturalLanguageDBInterface()
        app.run()
    except Exception as e:
        st.error(f"アプリケーション初期化エラー: {e}")
        logger.error(f"Application error: {e}")


if __name__ == "__main__":
    main()