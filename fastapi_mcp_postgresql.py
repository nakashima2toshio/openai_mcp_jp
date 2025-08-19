# fastapi_mcp_postgresql.py - 自然言語でPostgreSQLにアクセスするStreamlitアプリ
# streamlit run fastapi_mcp_postgresql.py --server.port=8504

import streamlit as st
import os
import pandas as pd
import psycopg2
import psycopg2.extras
import re
import time
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# ヘルパーモジュールからインポート
from helper_api import OpenAIClient, MessageManager, config, logger
from helper_mcp import MCPSessionManager
from helper_st import UIHelper


class SafeDatabaseManager:
    """安全なPostgreSQLデータベース接続・操作管理"""
    
    ALLOWED_KEYWORDS = [
        "SELECT", "WITH", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", 
        "FULL", "ON", "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "OFFSET",
        "UNION", "INTERSECT", "EXCEPT", "AS", "DISTINCT", "COUNT", "SUM", 
        "AVG", "MIN", "MAX", "CASE", "WHEN", "THEN", "ELSE", "END"
    ]
    
    FORBIDDEN_KEYWORDS = [
        "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE",
        "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL", "DECLARE", "CURSOR"
    ]
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self) -> bool:
        """データベース接続"""
        try:
            self.connection = psycopg2.connect(
                self.connection_string,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            return True
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            st.error(f"データベース接続エラー: {e}")
            return False
    
    def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """SQL安全性検証"""
        sql_upper = sql.upper().strip()
        
        # 禁止キーワードチェック
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in sql_upper:
                return False, f"禁止されたSQL操作が含まれています: {keyword}"
        
        # SELECT文チェック
        if not sql_upper.startswith(("SELECT", "WITH")):
            return False, "SELECT文またはWITH文のみ実行可能です"
        
        # セミコロンの数チェック（SQL injection防止）
        if sql.count(';') > 1:
            return False, "複数のSQL文は実行できません"
        
        return True, "SQL文は安全です"
    
    def execute_query(self, sql: str) -> Tuple[bool, List[Dict], str]:
        """安全なクエリ実行"""
        is_valid, message = self.validate_sql(sql)
        if not is_valid:
            return False, [], message
        
        if not self.connection:
            if not self.connect():
                return False, [], "データベース接続が確立できません"
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                return True, [dict(row) for row in results], f"{len(results)}件の結果を取得しました"
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return False, [], f"クエリ実行エラー: {e}"
    
    def get_schema_info(self) -> Dict[str, Any]:
        """データベーススキーマ情報を取得"""
        schema_info = {}
        
        tables_query = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
        
        success, tables, _ = self.execute_query(tables_query)
        if not success:
            return schema_info
        
        for table in tables:
            table_name = table['table_name']
            columns_query = f"""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND table_schema = 'public'
            ORDER BY ordinal_position
            """
            
            success, columns, _ = self.execute_query(columns_query)
            if success:
                schema_info[table_name] = columns
        
        return schema_info


class NLQueryProcessor:
    """自然言語クエリをSQLに変換するプロセッサ"""
    
    def __init__(self, openai_client: OpenAIClient, db_manager: SafeDatabaseManager):
        self.openai_client = openai_client
        self.db_manager = db_manager
        self.schema_info = db_manager.get_schema_info()
    
    def build_sql_prompt(self, user_query: str) -> List[Dict[str, str]]:
        """SQL生成用プロンプトを構築"""
        schema_text = self._format_schema_info()
        
        system_prompt = f"""あなたは優秀なSQLクエリ生成アシスタントです。
ユーザーの自然言語による質問を、PostgreSQLクエリに変換してください。

【データベーススキーマ】
{schema_text}

【重要な制約】
- SELECT文またはWITH文のみ生成してください
- INSERT、UPDATE、DELETE、DROP等の変更系操作は禁止です
- SQLクエリのみを返し、説明文は不要です
- 日本語のカラム値は適切にエスケープしてください

【出力形式】
生成するSQLクエリのみを出力してください。説明やコメントは不要です。"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"次の質問に対応するSQLクエリを生成してください:\n\n{user_query}"}
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
    
    def generate_sql(self, user_query: str, model: str = "gpt-5-mini") -> Tuple[bool, str, str]:
        """自然言語からSQLを生成"""
        try:
            messages = self.build_sql_prompt(user_query)
            
            response = self.openai_client.create_response(
                input=messages,
                model=model
            )
            
            # レスポンスからテキストを抽出
            from helper_api import ResponseProcessor
            texts = ResponseProcessor.extract_text(response)
            
            if not texts:
                return False, "", "SQLクエリの生成に失敗しました"
            
            sql_query = texts[0].strip()
            
            # SQLクエリのクリーンアップ
            sql_query = self._clean_sql_query(sql_query)
            
            return True, sql_query, "SQLクエリを生成しました"
            
        except Exception as e:
            logger.error(f"SQL generation error: {e}")
            return False, "", f"SQL生成エラー: {e}"
    
    def _clean_sql_query(self, sql: str) -> str:
        """SQLクエリをクリーンアップ"""
        # マークダウンのコードブロックを除去
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        
        # 前後の空白を除去
        sql = sql.strip()
        
        # セミコロンで終わっていない場合は追加
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
    
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
        
        # データベース接続
        pg_conn_str = os.getenv('PG_CONN_STR', 'postgresql://testuser:testpass@localhost:5432/testdb')
        self.db_manager = SafeDatabaseManager(pg_conn_str)
        
        # OpenAI クライアント初期化
        try:
            self.openai_client = OpenAIClient()
            self.query_processor = NLQueryProcessor(self.openai_client, self.db_manager)
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
        st.title("🗣️ 自然言語でPostgreSQLアクセス")
        st.markdown("**自然な日本語でデータベースに質問してください**")
        
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
            self.execute_natural_language_query(user_query)
        elif execute_button and not user_query:
            st.warning("質問を入力してください。")
        
        # 結果表示
        self.display_results()
    
    def execute_natural_language_query(self, user_query: str):
        """自然言語クエリの実行"""
        st.write(f"🔍 **実行中のクエリ**: {user_query}")  # デバッグ情報
        
        with st.spinner("🤖 SQLクエリを生成中..."):
            # SQL生成
            success, sql_query, message = self.query_processor.generate_sql(
                user_query, 
                st.session_state.selected_model
            )
            
            if not success:
                st.error(f"SQLクエリ生成エラー: {message}")
                return
            
            st.success("SQLクエリを生成しました！")
            
            # 生成されたSQLを表示
            with st.expander("🔧 生成されたSQL", expanded=True):
                st.code(sql_query, language="sql")
        
        with st.spinner("🔍 クエリを実行中..."):
            # クエリ実行
            success, results, message = self.db_manager.execute_query(sql_query)
            
            if not success:
                st.error(f"クエリ実行エラー: {message}")
                return
            
            st.success(message)
            
            # 結果を保存
            st.session_state.current_results = results
            st.session_state.query_history.append((user_query, sql_query))
        
        # 結果の説明生成
        if results:
            with st.spinner("📝 結果を分析中..."):
                explanation = self.query_processor.explain_results(user_query, results)
                st.session_state.current_explanation = explanation
        else:
            st.session_state.current_explanation = "検索結果がありませんでした。"
    
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
            page_title="自然言語PostgreSQLアクセス",
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
        
        # サイドバーとメインインターフェース
        self.create_sidebar()
        self.create_main_interface()


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