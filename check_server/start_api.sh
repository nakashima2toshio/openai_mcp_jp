#!/bin/bash
# start_api.sh - APIサーバー起動スクリプト

set -e

echo "🚀 MCP API サーバーを起動中..."

# 環境変数の確認
if [ -z "$PG_CONN_STR" ]; then
    echo "⚠️ PG_CONN_STR環境変数が設定されていません"
    echo "デフォルト値を使用: postgresql://testuser:testpass@localhost:5432/testdb"
    export PG_CONN_STR="postgresql://testuser:testpass@localhost:5432/testdb"
fi

# PostgreSQLの接続確認
echo "🐘 PostgreSQL接続確認..."
python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ['PG_CONN_STR'])
    print('✅ PostgreSQL接続成功')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL接続失敗: {e}')
    exit(1)
"

# APIサーバー起動
echo "🌐 APIサーバーを起動..."
exec uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload
