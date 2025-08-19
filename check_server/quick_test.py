#!/usr/bin/env python3
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
