# mcp_qdrant.py - MCP経由で自然言語でQdrantにアクセスするStreamlitアプリ
# streamlit run mcp_qdrant.py --server.port=8505
# 前提: Qdrant MCPサーバーがポート8003で起動している必要があります

import streamlit as st
import os
import pandas as pd
import json
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv
import plotly.express as px
import plotly.graph_objects as go

# QdrantクライアントとEmbedding関連
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, Range, MatchValue
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    st.error("Qdrantクライアントが必要です: pip install qdrant-client")

# ヘルパーモジュールからインポート
from helper_api import OpenAIClient, MessageManager, config, logger
from helper_mcp import MCPSessionManager
from helper_st import UIHelper


class MCPQdrantManager:
    """MCP対応Qdrantベクターデータベース操作管理 (デモ用ハイブリッドモード)"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8003/mcp", qdrant_url: str = None):
        self.mcp_server_url = mcp_server_url
        self.qdrant_url = qdrant_url or os.getenv('QDRANT_URL', 'http://localhost:6333')
        self.collections_info = None
        self._cached_collections_info = None
        self._qdrant_client = None
        
        if QDRANT_AVAILABLE:
            try:
                self._qdrant_client = QdrantClient(url=self.qdrant_url)
            except Exception as e:
                logger.error(f"Qdrant client initialization error: {e}")
    
    def get_collections_info(self) -> Dict[str, Any]:
        """MCPサーバー経由でQdrantコレクション情報を取得"""
        if self._cached_collections_info is not None:
            return self._cached_collections_info
            
        # デフォルトのコレクション情報（Qdrant初期化データから）
        default_collections = {
            "documents": {
                "description": "文書の埋め込みベクトルコレクション",
                "vector_size": 384,
                "distance": "cosine",
                "fields": ["title", "content", "category", "timestamp", "author"],
                "sample_count": 100
            },
            "products": {
                "description": "商品の埋め込みベクトルコレクション (product_embeddings)",
                "vector_size": 384,
                "distance": "cosine", 
                "fields": ["ID", "name", "category", "description", "price"],
                "sample_count": 5
            },
            "product_embeddings": {
                "description": "商品の埋め込みベクトルコレクション",
                "vector_size": 384,
                "distance": "cosine", 
                "fields": ["ID", "name", "category", "description", "price"],
                "sample_count": 5
            },
            "knowledge_base": {
                "description": "知識ベースの埋め込みベクトルコレクション",
                "vector_size": 384,
                "distance": "cosine",
                "fields": ["topic", "content", "tags", "difficulty_level", "source"],
                "sample_count": 200
            }
        }
        
        # 実際のQdrantサーバーに接続してコレクション情報を取得（可能な場合）
        if self._qdrant_client:
            try:
                actual_collections = {}
                collections_response = self._qdrant_client.get_collections()
                
                for collection in collections_response.collections:
                    collection_name = collection.name
                    collection_info = self._qdrant_client.get_collection(collection_name)
                    
                    actual_collections[collection_name] = {
                        "description": f"{collection_name}コレクション",
                        "vector_size": collection_info.config.params.vectors.size,
                        "distance": collection_info.config.params.vectors.distance.name.lower(),
                        "fields": ["id", "payload", "vector"],  # Qdrantの基本フィールド
                        "sample_count": collection_info.points_count or 0
                    }
                
                if actual_collections:
                    self._cached_collections_info = actual_collections
                    return actual_collections
                    
            except Exception as e:
                logger.warning(f"Could not fetch actual Qdrant collections: {e}")
        
        self._cached_collections_info = default_collections
        return default_collections


class MCPVectorQueryProcessor:
    """MCP経由で自然言語ベクトルクエリを処理するプロセッサ"""
    
    def __init__(self, openai_client: OpenAIClient, qdrant_manager: MCPQdrantManager):
        self.openai_client = openai_client
        self.qdrant_manager = qdrant_manager
        self.collections_info = qdrant_manager.get_collections_info()
    
    def build_mcp_prompt(self, user_query: str) -> List[Dict[str, str]]:
        """MCP経由でのベクトルデータベースクエリ用プロンプトを構築"""
        collections_text = self._format_collections_info()
        
        system_prompt = f"""あなたはQdrant MCPサーバーと連携するアシスタントです。
ユーザーの自然言語による質問を理解し、適切なベクトルデータベース操作を実行してください。

【Qdrantコレクション】
{collections_text}

【MCP操作について】
- Qdrant MCPサーバーが利用可能です
- ベクトル検索、フィルタリング、類似度検索が可能です
- 結果はJSON形式で返されます
- 日本語での質問に対して適切な回答をしてください

【応答形式】
MCPサーバーを使用してベクトルデータベースをクエリし、結果を日本語で分かりやすく説明してください。"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    
    def _format_collections_info(self) -> str:
        """コレクション情報をテキスト形式にフォーマット"""
        collections_text = ""
        for collection_name, info in self.collections_info.items():
            collections_text += f"\n【コレクション: {collection_name}】\n"
            collections_text += f"  - 説明: {info['description']}\n"
            collections_text += f"  - ベクトルサイズ: {info['vector_size']}\n"
            collections_text += f"  - 距離関数: {info['distance']}\n"
            collections_text += f"  - フィールド: {', '.join(info['fields'])}\n"
            collections_text += f"  - サンプル数: {info['sample_count']}\n"
        
        return collections_text
    
    def execute_mcp_query(self, user_query: str, model: str = "gpt-5-mini") -> Tuple[bool, List[Dict], str]:
        """MCP対応デモ: AI生成ベクトル検索を使用したQdrantクエリ実行"""
        try:
            # Step 1: ユーザークエリから検索戦略を生成 (MCP概念のデモ)
            search_strategy, explanation = self._generate_search_strategy_via_ai(user_query, model)
            
            if not search_strategy:
                return False, [], "検索戦略生成に失敗しました"
            
            # Step 2: Qdrantで検索実行 (MCPサーバー代替)
            results = self._execute_vector_search_directly(search_strategy, user_query)
            
            # Step 3: 結果の説明生成
            if results:
                response_text = f"**検索戦略**: {search_strategy['description']}\n\n**実行結果**: {len(results)}件のベクトルデータを取得しました。\n\n{explanation}"
            else:
                response_text = f"**検索戦略**: {search_strategy['description']}\n\n**実行結果**: マッチするデータが見つかりませんでした。\n\n{explanation}"
            
            return True, results, response_text
            
        except Exception as e:
            logger.error(f"MCP vector query error: {e}")
            return False, [], f"MCPベクトルクエリ実行エラー: {e}"
    
    def _generate_search_strategy_via_ai(self, user_query: str, model: str) -> Tuple[Dict, str]:
        """AI を使用してベクトル検索戦略生成 (MCP概念のデモ)"""
        try:
            collections_text = self._format_collections_info()
            
            strategy_prompt = f"""以下のQdrantコレクション情報に基づいて、ユーザーの質問に対応するベクトル検索戦略を生成してください。

【Qdrantコレクション情報】
{collections_text}

【制約】
- 適切なコレクションを選択してください
- ベクトル検索のクエリタイプを決定してください
- 安全な検索戦略を心がけてください
- JSON形式で戦略を出力してください

【質問】: {user_query}

以下のJSON形式で回答してください：
{{
    "collection": "適切なコレクション名",
    "query_type": "semantic_search|filter_search|hybrid_search",
    "search_text": "検索に使用するテキスト",
    "filters": {{}},
    "limit": 10,
    "description": "検索戦略の説明"
}}"""
            
            response = self.openai_client.create_response(
                input=[
                    {"role": "system", "content": "あなたはベクトル検索の専門家です。効率的で安全なQdrant検索戦略を生成してください。"},
                    {"role": "user", "content": strategy_prompt}
                ],
                model=model
            )
            
            from helper_api import ResponseProcessor
            texts = ResponseProcessor.extract_text(response)
            
            if texts:
                strategy_text = self._clean_json_response(texts[0])
                try:
                    strategy = json.loads(strategy_text)
                    explanation = f"質問『{user_query}』に対応するベクトル検索戦略を生成しました。"
                    return strategy, explanation
                except json.JSONDecodeError:
                    # JSONパースに失敗した場合のフォールバック
                    fallback_strategy = {
                        "collection": "documents",
                        "query_type": "semantic_search",
                        "search_text": user_query,
                        "filters": {},
                        "limit": 10,
                        "description": "デフォルト検索戦略"
                    }
                    return fallback_strategy, "フォールバック戦略を使用します。"
            
            return {}, "検索戦略生成に失敗しました"
            
        except Exception as e:
            logger.error(f"Search strategy generation error: {e}")
            return {}, f"検索戦略生成エラー: {e}"
    
    def _clean_json_response(self, text: str) -> str:
        """AI応答からJSONを抽出・クリーンアップ"""
        import re
        # マークダウンのコードブロックを除去
        text = re.sub(r'```json\n?', '', text)
        text = re.sub(r'```\n?', '', text)
        text = text.strip()
        
        # JSONブロックを探す
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx != -1 and end_idx != -1:
            return text[start_idx:end_idx+1]
        
        return text
    
    def _execute_vector_search_directly(self, strategy: Dict, user_query: str) -> List[Dict]:
        """Qdrantで直接ベクトル検索実行 (MCPサーバー代替)"""
        try:
            if not self.qdrant_manager._qdrant_client:
                # Qdrantクライアントが利用できない場合はモックデータを返す
                return self._generate_mock_search_results(strategy, user_query)
            
            collection_name = strategy.get('collection', 'documents')
            search_text = strategy.get('search_text', user_query)
            limit = strategy.get('limit', 10)
            
            # 検索テキストをベクトルに変換（OpenAI embeddings使用）
            search_vector = self._get_embedding(search_text)
            
            if not search_vector:
                return self._generate_mock_search_results(strategy, user_query)
            
            # Qdrantで検索実行（新しいAPIを使用）
            search_result = self.qdrant_manager._qdrant_client.query_points(
                collection_name=collection_name,
                query=search_vector,
                limit=limit,
                with_payload=True
            )
            
            # 結果をDict形式に変換
            results = []
            for point in search_result:
                result_dict = {
                    'id': point.id,
                    'score': float(point.score),
                    'payload': point.payload or {}
                }
                results.append(result_dict)
            
            return results
                    
        except Exception as e:
            logger.error(f"Direct vector search execution error: {e}")
            # エラー時はモックデータを返す
            return self._generate_mock_search_results(strategy, user_query)
    
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """OpenAI APIを使用してテキストの埋め込みベクトルを取得"""
        try:
            response = self.openai_client.client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            
            # Qdrantのベクトル次元に合わせて調整（384次元に切り詰め）
            if len(embedding) > 384:
                embedding = embedding[:384]
            elif len(embedding) < 384:
                # 必要に応じてゼロパディング
                embedding.extend([0.0] * (384 - len(embedding)))
            
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None
    
    def _generate_mock_search_results(self, strategy: Dict, user_query: str) -> List[Dict]:
        """モック検索結果を生成（Qdrant接続できない場合）"""
        collection_name = strategy.get('collection', 'documents')
        mock_results = []
        
        if collection_name == 'documents':
            mock_results = [
                {
                    'id': 'doc_001',
                    'score': 0.95,
                    'payload': {
                        'title': 'AI技術概要',
                        'content': 'AI技術に関する基本的な説明文書',
                        'category': 'technology',
                        'timestamp': '2024-01-15T10:00:00Z',
                        'author': 'AI研究チーム'
                    }
                },
                {
                    'id': 'doc_002', 
                    'score': 0.88,
                    'payload': {
                        'title': 'データベース設計',
                        'content': 'データベース設計の基本原則とベストプラクティス',
                        'category': 'database',
                        'timestamp': '2024-01-20T14:30:00Z',
                        'author': 'データベース専門家'
                    }
                }
            ]
        elif collection_name in ['products', 'product_embeddings']:
            mock_results = [
                {
                    'id': 1,
                    'score': 0.92,
                    'payload': {
                        'ID': 1,
                        'name': '高性能ノートPC',
                        'description': 'プログラミングやデザイン作業に最適な高性能ノートパソコン',
                        'category': 'エレクトロニクス',
                        'price': 89800
                    }
                },
                {
                    'id': 4,
                    'score': 0.75,
                    'payload': {
                        'ID': 4,
                        'name': 'レザービジネスバッグ',
                        'description': '本革製の高級ビジネスバッグ、ノートPCも収納可能',
                        'category': 'ファッション',
                        'price': 8900
                    }
                },
                {
                    'id': 2,
                    'score': 0.65,
                    'payload': {
                        'ID': 2,
                        'name': 'ワイヤレスイヤホン',
                        'description': 'ノイズキャンセリング機能付きの高音質ワイヤレスイヤホン',
                        'category': 'エレクトロニクス',
                        'price': 12800
                    }
                }
            ]
        elif collection_name == 'knowledge_base':
            mock_results = [
                {
                    'id': 'kb_001',
                    'score': 0.90,
                    'payload': {
                        'topic': 'プログラミング基礎',
                        'content': 'プログラミングの基本概念と実践',
                        'tags': ['programming', 'basics', 'education'],
                        'difficulty_level': 'beginner',
                        'source': '教育プラットフォーム'
                    }
                }
            ]
        
        return mock_results[:strategy.get('limit', 5)]
    
    def explain_results(self, query: str, results: List[Dict], model: str = "gpt-4o-mini") -> str:
        """ベクトル検索結果を自然言語で説明"""
        if not results:
            return "検索結果がありませんでした。"
        
        try:
            # 結果のサマリーを作成
            result_summary = f"ベクトル検索結果: {len(results)}件\n"
            result_summary += "\n検索結果データ:\n"
            
            for i, result in enumerate(results[:3], 1):
                score = result.get('score', 0)
                payload = result.get('payload', {})
                result_summary += f"{i}. [類似度: {score:.2f}] {payload}\n"
            
            if len(results) > 3:
                result_summary += f"... (他{len(results)-3}件)"
            
            messages = [
                {
                    "role": "system", 
                    "content": "あなたはベクトル検索結果を分かりやすく説明する専門家です。検索結果の内容と類似度スコアを自然な日本語で要約してください。"
                },
                {
                    "role": "user", 
                    "content": f"以下のベクトル検索結果について、わかりやすく日本語で説明してください:\n\n質問: {query}\n\n{result_summary}"
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
                return f"{len(results)}件の類似結果が見つかりました。"
                
        except Exception as e:
            logger.error(f"Result explanation error: {e}")
            return f"{len(results)}件の類似結果が見つかりました。"


class NaturalLanguageVectorInterface:
    """自然言語ベクトルデータベースインターフェースのメインアプリケーション"""
    
    def __init__(self):
        # 環境変数読み込み
        load_dotenv()
        
        # セッション初期化
        MCPSessionManager.init_session()
        self._init_session_state()
        
        # MCP Qdrant接続
        mcp_server_url = os.getenv('QDRANT_MCP_URL', 'http://localhost:8003/mcp')
        self.qdrant_manager = MCPQdrantManager(mcp_server_url)
        
        # OpenAI クライアント初期化
        try:
            self.openai_client = OpenAIClient()
            self.query_processor = MCPVectorQueryProcessor(self.openai_client, self.qdrant_manager)
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
            'collections_loaded': False
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
        """自然言語ベクトル検索クエリの候補を返す"""
        return [
            "プログラミング作業に適したノートPCを探して",
            "高音質なワイヤレスイヤホンを検索して",
            "全自動のコーヒーメーカーを見つけて",
            "ビジネス用の本革バッグを探して",
            "ランニング用の軽量シューズを検索して",
            "エレクトロニクス製品を一覧表示して",
            "キッチン家電の商品を探して",
            "ファッション関連の商品を検索して",
            "スポーツ用品を見つけて",
            "10000円以下の商品を探して",
            "高価格帯の商品を検索して",
            "類似した商品を探して"
        ]
    
    def create_sidebar(self):
        """サイドバーの作成"""
        st.sidebar.title("🔍 設定")
        
        # モデル選択
        available_models = self.get_available_models()
        selected_model = st.sidebar.selectbox(
            "🎯 OpenAI モデル選択",
            options=available_models,
            index=available_models.index("gpt-5-mini") if "gpt-5-mini" in available_models else 0,
            help="自然言語からベクトル検索への変換精度に影響します"
        )
        st.session_state.selected_model = selected_model
        
        st.sidebar.markdown("---")
        
        # Qdrant情報
        st.sidebar.subheader("🗄️ Qdrant情報")
        if st.sidebar.button("コレクション情報を更新"):
            self.query_processor.collections_info = self.qdrant_manager.get_collections_info()
            st.session_state.collections_loaded = True
            st.sidebar.success("コレクション情報を更新しました")
        
        # コレクション表示
        with st.sidebar.expander("コレクション構造を表示"):
            collections_info = self.query_processor.collections_info
            for collection_name, info in collections_info.items():
                st.write("---")
                st.write(f"**{collection_name}**")
                st.write(f"📝 {info['description']}")
                st.write(f"📏 ベクトルサイズ: {info['vector_size']}")
                st.write(f"📊 データ数: {info['sample_count']}")
        
        st.sidebar.markdown("---")
        
        # クエリ履歴
        if st.session_state.query_history:
            st.sidebar.subheader("📝 クエリ履歴")
            for i, (query, _) in enumerate(reversed(st.session_state.query_history[-5:])):
                if st.sidebar.button(f"{query[:30]}...", key=f"history_{i}"):
                    st.session_state.current_query = query
    
    def create_main_interface(self):
        """メインインターフェースの作成"""
        st.title("🔍 MCP経由でQdrantアクセス")
        
        with st.expander("🔗 OpenAI API 部分"):
            st.code("""
            
  Input (入力)

  # Line: OpenAI API レスポンス作成 (検索戦略生成)
  response = self.openai_client.create_response(
      input=[
          {"role": "system", "content": 
  "あなたはベクトル検索の専門家です。効率的で安全なQdrant検索戦略を生成してください。"},
          {"role": "user", "content": strategy_prompt}
      ],
      model=model
  )

  # Line: 埋め込みベクトル生成
  response = self.openai_client.client.embeddings.create(
      input=text,
      model="text-embedding-3-small"
  )

  Process (処理)

  # ベクトル検索戦略の生成
  def _generate_search_strategy_via_ai(self, user_query: str, model: str):
      # コレクション情報を含むプロンプト構築
      strategy_prompt = f"以下のQdrantコレクション情報に基づいて、ユーザーの質問に対応するベクトル検索戦略を生成してください。
  【Qdrantコレクション情報】{collections_text}
  【制約】- 適切なコレクションを選択してください
  【質問】: {user_query}"

      # OpenAI API で検索戦略生成
      response = self.openai_client.create_response(...)

      # レスポンス処理
      texts = ResponseProcessor.extract_text(response)
      strategy = json.loads(strategy_text)

  Output (出力)
    
      # ベクトル検索結果の処理
      search_result = qdrant_client.search(
          collection_name=collection_name,
          query_vector=search_vector,
          limit=limit,
          with_payload=True
      )
      
      results = []
      for point in search_result:
          result_dict = {
              'id': point.id,
              'score': float(point.score),
              'payload': point.payload or {}
          }
          results.append(result_dict)
            """)
            
        with st.expander("🔗 MCP (Model Context Protocol) 部分"):
            st.code("""
            
  Input (入力)

  # MCPプロンプト構築 (ベクトル検索用)
  def build_mcp_prompt(self, user_query: str) -> List[Dict[str, str]]:
      system_prompt = f"あなたはQdrant MCPサーバーと連携するアシスタントです。
  【Qdrantコレクション】{collections_text}
  【MCP操作について】
  - Qdrant MCPサーバーが利用可能です
  - ベクトル検索、フィルタリング、類似度検索が可能です
  - 結果はJSON形式で返されます"

      return [
          {"role": "system", "content": system_prompt},
          {"role": "user", "content": user_query}
      ]

  Process (処理)

  # MCPベクトルクエリ実行処理（デモ版）
  def execute_mcp_query(self, user_query: str, model: str = "gpt-5-mini"):
      # Step 1: AI でベクトル検索戦略生成 (MCP概念のデモ)
      search_strategy, explanation = self._generate_search_strategy_via_ai(user_query, model)

      # Step 2: Qdrantで直接実行 (MCPサーバー代替)
      results = self._execute_vector_search_directly(search_strategy, user_query)

      # Step 3: 結果の説明生成
      response_text = f"**検索戦略**: {search_strategy['description']}"

  Output (出力)

  # ベクトル検索とJSONレスポンス
  def _execute_vector_search_directly(self, strategy: Dict, user_query: str):
      search_result = self.qdrant_manager._qdrant_client.search(
          collection_name=collection_name,
          query_vector=search_vector,
          limit=limit,
          with_payload=True
      )
      
      return [{'id': point.id, 'score': point.score, 'payload': point.payload} 
              for point in search_result]  # JSON形式で返却
            """)

        st.markdown("**MCP (Model Context Protocol)経由でベクトルデータベースに自然言語で質問してください**")
        
        # MCPサーバー情報を表示
        with st.expander("🔗 MCPサーバー情報"):
            st.markdown(f"**Qdrant MCPサーバー**: `{self.qdrant_manager.mcp_server_url}`")
            st.markdown("**アーキテクチャ**: Streamlit UI → OpenAI Responses API → MCP Server → Qdrant")
        
        # クエリ入力エリア
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 候補が選択された場合、その値を初期値として使用
            initial_value = st.session_state.get('selected_suggestion', '')
            
            # 自然言語クエリ入力
            user_query = st.text_input(
                "質問を入力してください:",
                value=initial_value,
                placeholder="例: プログラミング作業に適したノートPCを探して",
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
        """MCP経由で自然言語ベクトルクエリを実行"""
        st.write(f"🔍 **実行中のクエリ**: {user_query}")
        
        with st.spinner("🤖 MCPサーバー経由でベクトル検索実行中..."):
            # MCPベクトルクエリ実行
            success, results, response_message = self.query_processor.execute_mcp_query(
                user_query, 
                st.session_state.selected_model
            )
            
            if not success:
                st.error(f"MCPベクトルクエリ実行エラー: {response_message}")
                return
            
            st.success("MCP経由でベクトルデータを取得しました！")
            
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
        st.subheader("🔍 ベクトル検索結果")
        
        # AI による説明
        if st.session_state.current_explanation:
            st.info(f"🤖 **AI分析**: {st.session_state.current_explanation}")
        
        if not results:
            st.warning("検索結果がありませんでした。")
            return
        
        # 結果をカード形式で表示
        for i, result in enumerate(results):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**結果 {i+1}**")
                    payload = result.get('payload', {})
                    
                    # payloadの内容を表示
                    for key, value in payload.items():
                        if key in ['title', 'name', 'topic']:
                            st.write(f"**{key}**: {value}")
                        elif key in ['content', 'description']:
                            # 長いテキストは省略表示
                            if len(str(value)) > 100:
                                st.write(f"**{key}**: {str(value)[:100]}...")
                            else:
                                st.write(f"**{key}**: {value}")
                        else:
                            st.write(f"**{key}**: {value}")
                
                with col2:
                    score = result.get('score', 0)
                    st.metric("類似度", f"{score:.3f}")
                
                st.markdown("---")
        
        # データダウンロード（JSON形式）
        if results:
            results_json = json.dumps(results, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 JSONダウンロード",
                data=results_json,
                file_name=f"vector_search_results_{int(time.time())}.json",
                mime="application/json"
            )
    
    def run(self):
        """アプリケーション実行"""
        st.set_page_config(
            page_title="MCP経由Qdrantアクセス",
            page_icon="🔍",
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
        
        # Qdrant接続状態表示（MCPデモ用）
        mcp_status = self._check_mcp_server_status()
        if not mcp_status:
            st.error("⚠️ Qdrantベクトルデータベースに接続できません")
            st.info("💡 **解決方法**:\n1. `docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d qdrant` でQdrantを起動\n2. 環境変数 `QDRANT_URL` を確認してください")
        
        # サイドバーとメインインターフェース
        self.create_sidebar()
        self.create_main_interface()
    
    def _check_mcp_server_status(self) -> bool:
        """Qdrant接続チェック (MCP代替デモ)"""
        try:
            if not self.qdrant_manager._qdrant_client:
                return False
            
            # 簡単な接続テスト
            collections = self.qdrant_manager._qdrant_client.get_collections()
            return True
            
        except Exception as e:
            logger.error(f"Qdrant connection check failed: {e}")
            return False


def main():
    """メイン関数"""
    try:
        app = NaturalLanguageVectorInterface()
        app.run()
    except Exception as e:
        st.error(f"アプリケーション初期化エラー: {e}")
        logger.error(f"Application error: {e}")


if __name__ == "__main__":
    main()