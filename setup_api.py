# setup_api.py
# MCP API サーバーとクライアントのセットアップスクリプト

import subprocess
import sys
import os
import time
import requests
from pathlib import Path
import json


def check_python_version():
    """Python バージョンチェック"""
    print("🐍 Python バージョンチェック...")
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8以上が必要です。現在のバージョン: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True


def install_requirements():
    """必要なパッケージをインストール"""
    print("📦 必要なパッケージをインストール中...")

    # FastAPI関連のパッケージを追加
    additional_packages = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.0.0"
    ]

    # requirements.txtを更新
    requirements_file = Path("requirements.txt")
    if requirements_file.exists():
        current_requirements = requirements_file.read_text(encoding='utf-8')
    else:
        current_requirements = ""

    # 新しい要件を追加
    new_requirements = current_requirements
    for package in additional_packages:
        package_name = package.split(">=")[0]
        if package_name not in current_requirements:
            new_requirements += f"\n{package}"

    # requirements.txtを更新
    requirements_file.write_text(new_requirements, encoding='utf-8')

    # パッケージをインストール
    try:
        print("📥 パッケージをインストール中...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
        ], check=True, capture_output=True, text=True)
        print("✅ パッケージのインストール完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ パッケージのインストール失敗: {e}")
        print(f"stderr: {e.stderr}")
        print("\n💡 手動でインストールしてください:")
        for package in additional_packages:
            print(f"  pip install {package}")
        return False


def check_postgresql():
    """PostgreSQLサーバーの状態確認"""
    print("🐘 PostgreSQLサーバーの状態確認...")

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2-binary パッケージが不足しています")
        print("💡 インストール: pip install psycopg2-binary")
        return False

    conn_str = os.getenv('PG_CONN_STR', 'postgresql://testuser:testpass@localhost:5432/testdb')

    try:
        conn = psycopg2.connect(conn_str)
        cursor = conn.cursor()

        # テーブルの存在確認
        cursor.execute("""
                       SELECT table_name
                       FROM information_schema.tables
                       WHERE table_schema = 'public'
                         AND table_name IN ('customers', 'orders', 'products')
                       """)
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]

        if len(table_names) == 3:
            cursor.execute("SELECT COUNT(*) FROM customers")
            customer_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]

            print(f"✅ PostgreSQL接続成功")
            print(f"   - 顧客数: {customer_count}")
            print(f"   - 注文数: {order_count}")
            print(f"   - 商品数: {product_count}")
            conn.close()
            return True
        else:
            print(f"⚠️ 必要なテーブルが不足しています: {table_names}")
            conn.close()
            return False

    except Exception as e:
        print(f"❌ PostgreSQL接続失敗: {e}")
        print(f"接続文字列: {conn_str}")
        print("\n💡 解決方法:")
        print("1. Dockerサービスを起動:")
        print("   docker-compose -f docker-compose.mcp-demo.yml up -d postgres")
        print("2. テストデータを投入:")
        print("   python setup_test_data.py")
        print("3. 手動でのポート確認:")
        print("   netstat -an | grep 5432")
        return False


def check_api_dependencies():
    """API関連の依存関係チェック"""
    print("🔍 API依存関係チェック...")

    required_modules = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
        ("requests", "Requests")
    ]

    missing_modules = []

    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name} - インストール済み")
        except ImportError:
            print(f"  ❌ {display_name} - 未インストール")
            missing_modules.append(module_name)

    if missing_modules:
        print(f"\n❌ 不足パッケージ: {', '.join(missing_modules)}")
        print("💡 インストール:")
        print(f"   pip install {' '.join(missing_modules)}")
        return False

    print("✅ 全ての依存関係が満たされています")
    return True


def start_api_server():
    """APIサーバーを起動"""
    print("🚀 APIサーバーを起動中...")

    # サーバーファイルの存在確認
    if not Path("mcp_api_server.py").exists():
        print("❌ mcp_api_server.py が見つかりません")
        return None

    # バックグラウンドでAPIサーバーを起動
    try:
        print("⏳ サーバープロセスを開始...")
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "mcp_api_server:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # サーバーの起動を待機
        print("⏳ サーバーの起動を待機中...")
        for i in range(30):  # 30秒間試行
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    health_data = response.json()
                    print("✅ APIサーバーが起動しました!")
                    print(f"📍 URL: http://localhost:8000")
                    print(f"📖 ドキュメント: http://localhost:8000/docs")
                    print(f"🔗 管理画面: http://localhost:8000/redoc")
                    print(f"🏥 ヘルス: {health_data.get('status', 'unknown')}")
                    return process
            except Exception as e:
                pass

            print(f"   ... 待機中 ({i + 1}/30)")
            time.sleep(1)

        print("❌ APIサーバーの起動に失敗しました")
        print("📋 プロセス情報:")
        stdout, stderr = process.communicate(timeout=5)
        if stdout:
            print(f"stdout: {stdout.decode()}")
        if stderr:
            print(f"stderr: {stderr.decode()}")

        process.terminate()
        return None

    except Exception as e:
        print(f"❌ APIサーバー起動エラー: {e}")
        return None


def test_api_endpoints():
    """API エンドポイントのテスト"""
    print("🧪 APIエンドポイントのテスト...")

    base_url = "http://localhost:8000"
    test_endpoints = [
        ("GET", "/", "ルート"),
        ("GET", "/health", "ヘルスチェック"),
        ("GET", "/api/customers?limit=1", "顧客一覧"),
        ("GET", "/api/products?limit=1", "商品一覧"),
        ("GET", "/api/orders?limit=1", "注文一覧"),
        ("GET", "/api/stats/sales", "売上統計")
    ]

    successful_tests = 0

    for method, endpoint, description in test_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.request(method, url, timeout=5)

            if response.status_code == 200:
                print(f"  ✅ {description}: OK ({response.status_code})")
                successful_tests += 1
            else:
                print(f"  ⚠️ {description}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {description}: エラー - {e}")

    print(f"\n📊 テスト結果: {successful_tests}/{len(test_endpoints)} 成功")
    return successful_tests == len(test_endpoints)


def run_client_demo():
    """クライアントデモを実行"""
    print("\n🎮 クライアントデモを実行...")

    if not Path("mcp_api_client.py").exists():
        print("❌ mcp_api_client.py が見つかりません")
        return False

    try:
        print("▶️ デモを開始します...")
        result = subprocess.run([sys.executable, "mcp_api_client.py"],
                                check=True, timeout=60)
        print("✅ クライアントデモ実行完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ クライアントデモ実行エラー: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("⏰ デモの実行がタイムアウトしました")
        return False
    except FileNotFoundError:
        print("❌ Pythonインタープリターが見つかりません")
        return False


def create_demo_files():
    """デモファイルを作成"""
    print("📝 デモファイルを作成中...")

    # 簡単なテスト用スクリプト
    test_script = '''#!/usr/bin/env python3
# quick_test.py - APIサーバーの簡単なテスト

import requests
import json
import sys

def test_api():
    base_url = "http://localhost:8000"

    print("🧪 API サーバーテスト開始")
    print(f"🌐 ベースURL: {base_url}")
    print("-" * 40)

    tests_passed = 0
    total_tests = 0

    # 1. ヘルスチェック
    total_tests += 1
    try:
        print("1️⃣ ヘルスチェック...")
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ OK - {health_data.get('status', 'unknown')}")
            tests_passed += 1
        else:
            print(f"   ❌ NG - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # 2. 顧客一覧取得
    total_tests += 1
    try:
        print("2️⃣ 顧客一覧取得...")
        response = requests.get(f"{base_url}/api/customers?limit=3", timeout=5)
        if response.status_code == 200:
            customers = response.json()
            print(f"   ✅ OK - {len(customers)}件取得")
            for i, customer in enumerate(customers, 1):
                print(f"      {i}. {customer['name']} ({customer['city']})")
            tests_passed += 1
        else:
            print(f"   ❌ NG - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # 3. 商品一覧取得
    total_tests += 1
    try:
        print("3️⃣ 商品一覧取得...")
        response = requests.get(f"{base_url}/api/products?limit=3", timeout=5)
        if response.status_code == 200:
            products = response.json()
            print(f"   ✅ OK - {len(products)}件取得")
            for i, product in enumerate(products, 1):
                print(f"      {i}. {product['name']} - ¥{product['price']:,}")
            tests_passed += 1
        else:
            print(f"   ❌ NG - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # 4. 売上統計取得
    total_tests += 1
    try:
        print("4️⃣ 売上統計取得...")
        response = requests.get(f"{base_url}/api/stats/sales", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ OK - 統計データ取得")
            print(f"      📊 総売上: ¥{stats['total_sales']:,.0f}")
            print(f"      📦 注文数: {stats['total_orders']:,}件")
            print(f"      💰 平均注文額: ¥{stats['avg_order_value']:,.0f}")
            tests_passed += 1
        else:
            print(f"   ❌ NG - Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # 5. 新規顧客作成テスト
    total_tests += 1
    try:
        print("5️⃣ 新規顧客作成テスト...")
        import time
        test_customer = {
            "name": "テスト太郎",
            "email": f"test.{int(time.time())}@example.com",
            "city": "テスト市"
        }
        response = requests.post(f"{base_url}/api/customers", json=test_customer, timeout=5)
        if response.status_code == 200:
            new_customer = response.json()
            print(f"   ✅ OK - 顧客作成成功")
            print(f"      👤 ID: {new_customer['id']}, 名前: {new_customer['name']}")
            tests_passed += 1
        else:
            print(f"   ❌ NG - Status: {response.status_code}")
            if response.text:
                print(f"      詳細: {response.text}")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # 結果表示
    print("-" * 40)
    print(f"🎯 テスト結果: {tests_passed}/{total_tests} 成功")

    if tests_passed == total_tests:
        print("🎉 全てのテストが成功しました!")
        return True
    else:
        print("⚠️ 一部のテストが失敗しました")
        return False

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
'''

    with open("quick_test.py", "w", encoding="utf-8") as f:
        f.write(test_script)

    # Docker Compose設定（API用）
    docker_compose_api = '''version: '3.8'

services:
  mcp-api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - PG_CONN_STR=postgresql://testuser:testpass@postgres:5432/testdb
    depends_on:
      - postgres
    volumes:
      - .:/app
    working_dir: /app
    command: uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser -d testdb"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
'''

    with open("docker-compose.api.yml", "w", encoding="utf-8") as f:
        f.write(docker_compose_api)

    # Dockerfile for API
    dockerfile_api = '''FROM python:3.11-slim

WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY . .

EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "mcp_api_server:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    with open("Dockerfile.api", "w", encoding="utf-8") as f:
        f.write(dockerfile_api)

    # 起動スクリプト
    startup_script = '''#!/bin/bash
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
'''

    with open("start_api.sh", "w", encoding="utf-8") as f:
        f.write(startup_script)

    # 実行権限を付与（Unix系の場合）
    if os.name != 'nt':  # Windows以外
        os.chmod("start_api.sh", 0o755)

    print("✅ デモファイルを作成しました:")
    print("   - quick_test.py: 簡単なAPIテスト")
    print("   - docker-compose.api.yml: Docker設定")
    print("   - Dockerfile.api: API用Dockerファイル")
    print("   - start_api.sh: 起動スクリプト")


def display_usage_info():
    """使用方法の表示"""
    print("\n" + "=" * 50)
    print("📚 使用方法")
    print("=" * 50)

    print("\n💡 基本的な使用方法:")
    print("1. APIドキュメント確認:")
    print("   🌐 http://localhost:8000/docs (Swagger UI)")
    print("   📖 http://localhost:8000/redoc (ReDoc)")

    print("\n2. 簡単なテスト:")
    print("   python quick_test.py")

    print("\n3. 完全なクライアントデモ:")
    print("   python mcp_api_client.py")

    print("\n4. curlでのテスト:")
    print("   curl http://localhost:8000/health")
    print("   curl http://localhost:8000/api/customers")

    print("\n🔧 サーバー管理:")
    print("- サーバー停止: Ctrl+C")
    print("- ポート確認: netstat -an | grep 8000")
    print("- ログ確認: サーバープロセスのターミナルを確認")

    print("\n📊 利用可能なエンドポイント:")
    endpoints = [
        ("GET", "/api/customers", "顧客一覧取得"),
        ("GET", "/api/customers/{id}", "特定顧客取得"),
        ("POST", "/api/customers", "顧客作成"),
        ("GET", "/api/products", "商品一覧取得"),
        ("GET", "/api/orders", "注文一覧取得"),
        ("POST", "/api/orders", "注文作成"),
        ("GET", "/api/stats/sales", "売上統計"),
        ("GET", "/api/stats/customers/{id}/orders", "顧客別統計")
    ]

    for method, endpoint, description in endpoints:
        print(f"   {method:4} {endpoint:30} - {description}")


def main():
    """メインセットアップ処理"""
    print("🔧 MCP API セットアップを開始します")
    print("=" * 50)

    # 1. Python バージョンチェック
    if not check_python_version():
        return

    # 2. パッケージインストール
    if not install_requirements():
        print("❌ セットアップ失敗: パッケージのインストールに失敗しました")
        return

    # 3. 依存関係チェック
    if not check_api_dependencies():
        print("❌ セットアップ失敗: 依存関係が満たされていません")
        return

    # 4. PostgreSQL確認
    if not check_postgresql():
        print("❌ セットアップ失敗: PostgreSQLに接続できません")
        print("\n💡 PostgreSQLセットアップ手順:")
        print("1. docker-compose -f docker-compose.mcp-demo.yml up -d postgres")
        print("2. python setup_test_data.py")
        return

    # 5. デモファイル作成
    create_demo_files()

    # 6. APIサーバー起動
    print("\n" + "=" * 30)
    print("🚀 APIサーバー起動")
    print("=" * 30)

    server_process = start_api_server()
    if not server_process:
        print("❌ セットアップ失敗: APIサーバーの起動に失敗しました")
        print("\n💡 手動での起動方法:")
        print("   python mcp_api_server.py")
        print("   # または")
        print("   uvicorn mcp_api_server:app --host 0.0.0.0 --port 8000 --reload")
        return

    # 7. エンドポイントテスト
    print("\n" + "=" * 30)
    print("🧪 エンドポイントテスト")
    print("=" * 30)

    if test_api_endpoints():
        print("✅ 全てのエンドポイントが正常に動作しています")
    else:
        print("⚠️ 一部のエンドポイントに問題があります")

    # 8. 使用方法表示
    display_usage_info()

    print("\n" + "=" * 50)
    print("🎉 セットアップ完了!")
    print("=" * 50)

    # ユーザーの選択
    print("\n🎮 次に何をしますか?")
    print("1. 簡単なテストを実行 (quick_test.py)")
    print("2. 完全なクライアントデモを実行 (mcp_api_client.py)")
    print("3. そのままサーバーを起動したまま終了")
    print("4. サーバーを停止して終了")

    try:
        choice = input("\n選択してください (1-4): ").strip()

        if choice == "1":
            print("\n🧪 簡単なテストを実行中...")
            subprocess.run([sys.executable, "quick_test.py"])
        elif choice == "2":
            print("\n🎮 完全なクライアントデモを実行中...")
            run_client_demo()
        elif choice == "3":
            print("\n✅ サーバーを起動したまま終了します")
            print("⏸️ サーバーを停止するには Ctrl+C を押してください...")
            server_process.wait()
        elif choice == "4":
            print("\n🛑 サーバーを停止して終了します...")
            server_process.terminate()
            server_process.wait()
            print("✅ サーバーが停止しました")
        else:
            print("\n✅ サーバーを起動したまま終了します")
            print("⏸️ サーバーを停止するには Ctrl+C を押してください...")
            server_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止中...")
        server_process.terminate()
        server_process.wait()
        print("✅ サーバーが停止しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        server_process.terminate()


if __name__ == "__main__":
    main()
