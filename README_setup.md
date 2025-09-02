# MCPプロジェクト セットアップガイド

## 📚 目次

### セットアップ手順
1. [環境設定](#1-環境設定) - Python環境とパッケージのインストール
2. [データ投入](#2-データ投入) - 各データベースへのサンプルデータ投入
3. [サーバー起動](#3-サーバー起動) - APIサーバーの起動と動作確認

### 実行ガイド
- [🚀 利用順番（推奨手順）](#-利用順番推奨手順)
  - [ステップ1: 環境準備](#ステップ1-環境準備) - `setup.py`
  - [ステップ2: API KEY設定](#ステップ2-api-key設定) - `.env`ファイル編集
  - [ステップ3: データベース起動](#ステップ3-データベース起動) - `docker-compose`
  - [ステップ4: サンプルデータ投入](#ステップ4-サンプルデータ投入) - `data.py`
  - [ステップ5: APIサーバー起動](#ステップ5-apiサーバー起動) - `server.py`
  - [ステップ6: Streamlitアプリ起動](#ステップ6-streamlitアプリ起動) - `openai_api_mcp_sample.py`

### その他の情報
- [🌐 アクセスURL](#-アクセスurl)
- [📁 従来ファイルとの対応関係](#-従来ファイルとの対応関係)
- [✨ この統合セットアップの利点](#-この統合セットアップの利点)
- [🔧 トラブルシューティング](#-トラブルシューティング)
- [⚡ ワンライナー（全自動セットアップ）](#-ワンライナー全自動セットアップ)
- [📊 正常動作の確認方法](#-正常動作の確認方法)

## 概要

MCPプロジェクトのセットアップを3つの段階に分けて整理・統合しました。

## セットアップ手順

### 1. 環境設定

```bash
# 必要なパッケージのインストールと環境構築
python setup.py

# クイックセットアップ（検証をスキップ）
python setup.py --quick
```

**機能:**
- Python バージョンチェック
- パッケージマネージャー検出（uv/pip）
- 必要パッケージのインストール
- .env テンプレートファイル作成
- インストール確認

### 2. データ投入

```bash
# 全てのデータベースにデータを投入
python data.py

# 特定のデータベースのみ投入
python data.py --postgres        # PostgreSQLのみ
python data.py --redis           # Redisのみ
python data.py --elasticsearch   # Elasticsearchのみ  
python data.py --qdrant         # Qdrantのみ
```

**機能:**
- PostgreSQL: 顧客、商品、注文データ
- Redis: セッション、キャッシュ、リアルタイムデータ
- Elasticsearch: ブログ記事データ
- Qdrant: 商品ベクトルデータ

### 3. サーバー起動

```bash
# APIサーバー起動
python server.py

# ポート指定とテスト実行
python server.py --port 8080 --test
```

**機能:**
- PostgreSQL、Redis接続確認
- APIサーバー起動
- エンドポイントテスト
- 使用方法表示

## 🚀 利用順番（推奨手順）

### ステップ1: 環境準備
```bash
# パッケージインストールと環境構築
python setup.py
```
✅ **完了確認**: "🎉 環境セットアップ完了!" が表示される

### ステップ2: API KEY設定
```bash
# .envファイルを編集してOpenAI API KEYを設定（必須）
vi .env
```
```bash
# .envファイル内で設定
OPENAI_API_KEY=your-actual-api-key-here
```
⚠️ **重要**: この設定がないとアプリが動作しません

### ステップ3: データベース起動
```bash
# Dockerで全データベースサービスを起動
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d
```
✅ **完了確認**: `docker ps` で4つのコンテナが起動していることを確認

### ステップ4: サンプルデータ投入
```bash
# 全データベース（PostgreSQL, Redis, Elasticsearch, Qdrant）にデータを投入
python data.py
```
✅ **完了確認**: "🎉 全てのデータ投入が成功しました!" が表示される

### ステップ5: APIサーバー起動
```bash
# APIサーバーを起動（テスト付き）
python server.py --test
```
✅ **完了確認**: "✅ 全てのエンドポイントが正常です" が表示される

### ステップ6: Streamlitアプリ起動
```bash
# Webアプリケーションを起動
streamlit run openai_api_mcp_sample.py --server.port=8501
```
✅ **完了確認**: ブラウザで http://localhost:8501 にアクセスできる

---

## 🌐 アクセスURL

| サービス | URL | 説明 |
|---------|-----|-----|
| **Streamlitアプリ** | http://localhost:8501 | メインのWebアプリケーション |
| **API ドキュメント** | http://localhost:8000/docs | REST API仕様書（Swagger UI） |
| **API管理画面** | http://localhost:8000/redoc | REST API仕様書（ReDoc） |
| **ヘルスチェック** | http://localhost:8000/health | サーバー状態確認 |

---

## 📁 従来ファイルとの対応関係

| 新ファイル | 従来ファイル | 機能 |
|-----------|-------------|------|
| `setup.py` | `setup_env.sh`<br>`setup_api.py` (一部) | 環境設定・パッケージインストール |
| `server.py` | `start_api.sh`<br>`setup_api.py` (一部) | サーバー起動・ヘルスチェック |
| `data.py` | `setup_test_data.py`<br>`setup_sample_data.py` | 全データベース（PostgreSQL, Redis, Elasticsearch, Qdrant）へのデータ投入 |

## ✨ この統合セットアップの利点

### 🎯 **明確な役割分担**
- 各スクリプトの目的が一目で分かる
- 問題箇所を素早く特定可能

### 🔧 **柔軟な実行**
- 必要な部分だけ個別実行可能
- 段階的なトラブルシューティング

### 🤝 **統一されたインターface**
- 共通のオプション体系
- 一貫したエラーメッセージ

### 🛡️ **堅牢なエラー処理**
- 分かりやすいエラーメッセージ
- 具体的な解決方法を提示

### 📈 **段階的セットアップ**
- ステップごとの成功確認
- 問題箇所の早期発見

## 🔧 トラブルシューティング

### 🚨 問題発生時の段階的確認手順

#### 1. 環境設定で問題が発生した場合
```bash
# 検証をスキップしてクイックセットアップ
python setup.py --quick

# パッケージが不足している場合
pip install -r requirements.txt
```

#### 2. API KEY設定を忘れた場合
```bash
# .envファイルの確認
cat .env | grep OPENAI_API_KEY

# 設定されていない場合は編集
vi .env
```

#### 3. Dockerサービスが起動しない場合
```bash
# サービス状態確認
docker-compose -f docker-compose/docker-compose.mcp-demo.yml ps

# 全サービス再起動
docker-compose -f docker-compose/docker-compose.mcp-demo.yml down
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d

# ログ確認
docker-compose -f docker-compose/docker-compose.mcp-demo.yml logs
```

#### 4. データ投入で問題が発生した場合
```bash
# 個別データベースをテスト
python data.py --postgres   # PostgreSQL のみ
python data.py --redis      # Redis のみ  
python data.py --elasticsearch  # Elasticsearch のみ
python data.py --qdrant     # Qdrant のみ

# データベース接続確認
telnet localhost 5432  # PostgreSQL
telnet localhost 6379  # Redis
telnet localhost 9200  # Elasticsearch
telnet localhost 6333  # Qdrant
```

#### 5. サーバー起動で問題が発生した場合
```bash
# 詳細テスト付きで起動
python server.py --test

# 別ポートで起動を試す
python server.py --port 8080

# ポート使用状況確認
netstat -an | grep 8000
```

#### 6. Streamlitアプリで問題が発生した場合
```bash
# 別ポートで起動を試す
streamlit run openai_api_mcp_sample.py --server.port=8502

# アプリファイルの存在確認
ls -la openai_api_mcp_sample.py

# Streamlit設定クリア
streamlit cache clear
```

---

## ⚡ ワンライナー（全自動セットアップ）

急いでいる場合の全自動実行：

```bash
# 注意: .envファイルのAPI KEY設定は事前に必要
python setup.py && \
docker-compose -f docker-compose/docker-compose.mcp-demo.yml up -d && \
sleep 10 && \
python data.py && \
python server.py --test &
sleep 5 && \
streamlit run openai_api_mcp_sample.py --server.port=8501
```

---

## 📊 正常動作の確認方法

### 各ステップの成功メッセージ

| ステップ | 成功メッセージ | 失敗時の対処 |
|---------|-------------|-------------|
| **環境設定** | "🎉 環境セットアップ完了!" | `python setup.py --quick` |
| **Docker起動** | 4つのコンテナが"Up"状態 | `docker-compose up -d` 再実行 |
| **データ投入** | "🎉 全てのデータ投入が成功しました!" | 個別データベースをテスト |
| **サーバー起動** | "✅ 全てのエンドポイントが正常です" | ポート変更して再試行 |
| **アプリ起動** | "You can now view your Streamlit app" | キャッシュクリアして再起動 |

### 最終確認
```bash
# 全てが正常に動作しているかの確認
curl http://localhost:8000/health        # APIサーバー確認
curl http://localhost:8501               # Streamlitアプリ確認
```