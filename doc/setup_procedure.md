# MCP API Server 環境構築・起動手順書

## 概要

この手順書では、MCP (Model Context Protocol) API Serverの環境構築からアプリケーション起動まで、ステップバイステップで説明します。

## 前提条件

### 必要なソフトウェア
- **Python**: 3.12.2以上
- **Docker**: 最新版（Docker Composeを含む）
- **Git**: リポジトリクローン用
- **uv**: 高速パッケージ管理ツール（推奨）

### システム要件
- **OS**: Windows, macOS, Linux
- **メモリ**: 4GB以上推奨
- **ディスク**: 2GB以上の空き容量

## ステップ1: 環境準備とリポジトリセットアップ

### 1.1 リポジトリクローン（必要に応じて）
```bash
# リポジトリがない場合のみ
git clone <repository-url>
cd openai_mcp_jp
```

### 1.2 Pythonバージョン確認
```bash
python --version
# Python 3.12.2以上であることを確認

# pipの最新化
python -m pip install --upgrade pip
```

### 1.3 uv インストール（推奨）
```bash
# uv の高速インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# またはpipでインストール
pip install uv

# インストール確認
uv --version
```

## ステップ2: Docker環境とデータベースの起動

### 2.1 Docker Compose設定確認
```bash
# Docker Compose設定ファイルの存在確認
ls docker-compose/docker-compose.mcp-demo.yml
```

### 2.2 データベースコンテナ起動
```bash
# プロジェクトルートから実行
cd docker-compose

# データベース系のみ起動（PostgreSQL, Redis, Elasticsearch, Qdrant）
docker-compose -f docker-compose.mcp-demo.yml up -d

# 起動状態確認
docker-compose -f docker-compose.mcp-demo.yml ps

# ヘルスチェック確認（全てhealthyになるまで待機）
docker-compose -f docker-compose.mcp-demo.yml logs postgres
```

### 2.3 データベース接続確認
```bash
# PostgreSQL接続テスト
docker-compose -f docker-compose.mcp-demo.yml exec postgres psql -U testuser -d testdb -c "SELECT version();"

# Redis接続テスト
docker-compose -f docker-compose.mcp-demo.yml exec redis redis-cli ping

# Elasticsearch確認
curl http://localhost:9200/_cluster/health

# Qdrant確認
curl http://localhost:6333/health
```

## ステップ3: Python環境セットアップ

### 3.1 環境変数設定
```bash
# .envファイル作成（プロジェクトルートに戻る）
cd ..

# .envファイルの作成または編集
cat > .env << 'EOF'
# PostgreSQL接続設定
PG_CONN_STR=postgresql://testuser:testpass@localhost:5432/testdb

# その他のデータベースURL
REDIS_URL=redis://localhost:6379/0
ELASTIC_URL=http://localhost:9200
QDRANT_URL=http://localhost:6333

# OpenAI API Key（後で設定）
OPENAI_API_KEY=your-openai-api-key-here
EOF
```

### 3.2 環境セットアップスクリプト実行
```bash
# setup_env.sh の実行権限付与
chmod +x setup_env.sh

# 環境セットアップ実行
./setup_env.sh
```

**setup_env.shで実行されること：**
- Python・pip・uvバージョン確認
- requirements.txt作成
- 必要パッケージのインストール（uv/pip自動選択）
- .envファイルテンプレート作成（存在しない場合）
- パッケージインストール確認
- アプリケーションファイル構文チェック

## ステップ4: データベース初期化とテストデータ投入

### 4.1 テストデータセットアップ
```bash
# テストデータ投入
python setup_test_data.py

# サンプルデータ投入（オプション）
python setup_sample_data.py
```

### 4.2 データベース状態確認
```bash
# PostgreSQLのテーブル確認
docker-compose -f docker-compose/docker-compose.mcp-demo.yml exec postgres \
  psql -U testuser -d testdb -c "
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public';
  "

# データ件数確認
docker-compose -f docker-compose/docker-compose.mcp-demo.yml exec postgres \
  psql -U testuser -d testdb -c "
    SELECT 
      'customers' as table_name, COUNT(*) as count FROM customers
    UNION ALL
    SELECT 'orders' as table_name, COUNT(*) as count FROM orders
    UNION ALL
    SELECT 'products' as table_name, COUNT(*) as count FROM products;
  "
```

## ステップ5: setup_api.py による統合セットアップ

### 5.1 setup_api.py 実行
```bash
# 統合セットアップスクリプト実行
python setup_api.py
```

**setup_api.pyで実行されること：**
1. **Python バージョンチェック**: Python 3.8以上の確認
2. **パッケージインストール**: FastAPI、uvicorn、pydanticなど追加パッケージ
3. **依存関係チェック**: 必要モジュールの存在確認
4. **PostgreSQL接続確認**: データベース接続とテーブル存在確認
5. **デモファイル作成**: 
   - `quick_test.py`: 簡単なAPIテスト
   - `docker-compose.api.yml`: API用Docker設定
   - `Dockerfile.api`: API用Dockerfile
   - `start_api.sh`: 起動スクリプト
6. **APIサーバー起動**: バックグラウンドでAPIサーバー起動
7. **エンドポイントテスト**: 全APIエンドポイントの動作確認
8. **インタラクティブメニュー**: テスト実行選択肢提示

### 5.2 setup_api.py の実行結果確認
実行後、以下が表示されることを確認：
```
✅ APIサーバーが起動しました!
📍 URL: http://localhost:8000
📖 ドキュメント: http://localhost:8000/docs
🔗 管理画面: http://localhost:8000/redoc
🏥 ヘルス: healthy

🧪 エンドポイントテスト
✅ ルート: OK (200)
✅ ヘルスチェック: OK (200)
✅ 顧客一覧: OK (200)
✅ 商品一覧: OK (200)
✅ 注文一覧: OK (200)
✅ 売上統計: OK (200)

📊 テスト結果: 6/6 成功
```

## ステップ6: 個別アプリケーション起動方法

### 6.1 start_api.sh による起動（推奨）
```bash
# 起動スクリプト使用
./start_api.sh
```

**start_api.shで実行されること：**
- 環境変数PG_CONN_STRの確認とデフォルト設定
- PostgreSQL接続テスト
- uvicornによるAPIサーバー起動

### 6.2 mcp_api_server.py 直接起動
```bash
# Python直接実行
python mcp_api_server.py

# uvicorn直接実行
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload

# uv環境での実行
uv run python mcp_api_server.py
```

### 6.3 Docker を使った起動
```bash
# API用Docker Compose（setup_api.pyで作成される）
docker-compose -f docker-compose.api.yml up -d

# ログ確認
docker-compose -f docker-compose.api.yml logs -f mcp-api
```

## ステップ7: 動作確認とテスト

### 7.1 ヘルスチェック
```bash
# APIサーバー生存確認
curl http://localhost:8000/health

# 期待される応答:
# {
#   "status": "healthy",
#   "database": "connected",  
#   "timestamp": "2024-01-01T12:00:00.000000"
# }
```

### 7.2 基本機能テスト
```bash
# 簡単なテストスクリプト実行
python quick_test.py

# 詳細なクライアントテスト
python mcp_api_client.py
```

### 7.3 API文書確認
ブラウザで以下にアクセス：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 7.4 基本的なAPI呼び出しテスト
```bash
# 顧客一覧取得
curl -X GET "http://localhost:8000/api/customers?limit=5" -H "accept: application/json"

# 商品一覧取得
curl -X GET "http://localhost:8000/api/products?limit=5" -H "accept: application/json"

# 売上統計取得
curl -X GET "http://localhost:8000/api/stats/sales" -H "accept: application/json"
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. PostgreSQL接続エラー
```bash
# 症状: psycopg2.OperationalError: connection failed
# 解決:
docker-compose -f docker-compose/docker-compose.mcp-demo.yml restart postgres
docker-compose -f docker-compose/docker-compose.mcp-demo.yml logs postgres
```

#### 2. ポート衝突エラー
```bash
# 症状: port 8000 already in use
# 解決:
lsof -i :8000
# または
netstat -an | grep 8000
# プロセスを特定して終了
kill -9 <PID>
```

#### 3. Python パッケージエラー
```bash
# 症状: ImportError: No module named 'fastapi'
# 解決:
pip install -r requirements.txt --upgrade
# または
uv sync
```

#### 4. Docker コンテナ起動失敗
```bash
# 症状: container failed to start
# 解決:
docker-compose -f docker-compose/docker-compose.mcp-demo.yml down -v
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d
```

### ログとデバッグ

#### ログの確認方法
```bash
# APIサーバーログ（直接起動の場合）
# ターミナル出力を確認

# Docker起動の場合
docker-compose -f docker-compose.api.yml logs -f mcp-api

# データベースログ
docker-compose -f docker-compose/docker-compose.mcp-demo.yml logs postgres
```

#### デバッグモード起動
```bash
# デバッグ情報付きで起動
uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

## アプリケーション停止方法

### APIサーバー停止
```bash
# 直接起動の場合
Ctrl+C

# Docker起動の場合
docker-compose -f docker-compose.api.yml down
```

### 全データベース停止
```bash
# データベースコンテナ停止
docker-compose -f docker-compose/docker-compose.mcp-demo.yml down

# ボリューム削除（データも削除）
docker-compose -f docker-compose/docker-compose.mcp-demo.yml down -v
```

## 完全セットアップ確認チェックリスト

- [ ] Python 3.12.2以上インストール済み
- [ ] Docker Desktop起動済み  
- [ ] uv または pip 利用可能
- [ ] `.env` ファイル作成済み
- [ ] `./setup_env.sh` 実行完了
- [ ] Docker Compose でデータベース起動済み
- [ ] `python setup_test_data.py` 実行完了
- [ ] `python setup_api.py` 実行完了  
- [ ] API サーバーが http://localhost:8000 で応答
- [ ] `curl http://localhost:8000/health` が成功
- [ ] `python quick_test.py` の全テスト通過

## 次のステップ

セットアップ完了後の推奨作業：

1. **API文書確認**: http://localhost:8000/docs でAPI仕様確認
2. **クライアントテスト**: `python mcp_api_client.py` で全機能テスト
3. **開発開始**: 必要に応じてAPIエンドポイントの拡張
4. **本番デプロイ**: 本番環境への配置準備

## 不足情報・改善点

現在の手順で以下の情報が不足している可能性があります：

1. **OpenAI API Key設定**: .envファイルのOPENAI_API_KEY設定方法
2. **本番環境設定**: セキュリティ設定、HTTPS化、環境分離
3. **データバックアップ**: PostgreSQLデータのバックアップ方法
4. **ログローテーション**: 本番運用時のログ管理
5. **モニタリング**: ヘルスチェックとアラート設定
6. **スケーリング**: 負荷分散とパフォーマンス最適化

これらの詳細については、個別ドキュメントまたは本番運用ガイドとして別途作成することを推奨します。