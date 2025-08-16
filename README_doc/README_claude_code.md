# Claude Code + PyCharm Professional 開発ガイド

## 🚀 Claude Code の使い方

### 1. Claude Code のインストール

```bash
# Homebrewでインストール（推奨）
brew install anthropic/claude/claude

# またはcurlでインストール
curl -fsSL https://claude.ai/install.sh | sh

# インストール確認
claude --version
```

### 2. 認証設定

```bash
# APIキーを設定
claude auth login

# または環境変数で設定
export ANTHROPIC_API_KEY="your-api-key-here"
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. 基本的な使い方

#### ファイル作成・編集
```bash
# MCPプロジェクトディレクトリで
cd /path/to/mcp-project

# 新しいファイルを作成
claude create --file helper_new.py --description "新しいヘルパーモジュール"

# 既存ファイルを編集
claude edit mcp_api_server.py --instruction "FastAPIサーバーにキャッシュ機能を追加"

# 複数ファイルを同時に編集
claude edit helper_api.py helper_st.py --instruction "エラーハンドリングを改善"
```

#### コード生成・リファクタリング
```bash
# Streamlitアプリの新機能追加
claude generate --type streamlit-component --description "売上グラフ表示コンポーネント"

# 既存コードのリファクタリング
claude refactor openai_api_mcp_sample.py --goal "モジュラー化とパフォーマンス改善"

# テストコード生成
claude test mcp_api_client.py --framework pytest
```

#### プロジェクト全体の分析
```bash
# プロジェクト構造の分析
claude analyze --project . --focus architecture

# コード品質チェック
claude review --files "*.py" --focus "security,performance,maintainability"

# ドキュメント生成
claude docs --input . --output docs/ --format markdown
```

### 4. MCPプロジェクト特有の使い方

#### Streamlitアプリの改善
```bash
# UI/UXの改善提案
claude improve openai_api_mcp_sample.py --focus ui --target streamlit

# レスポンシブデザイン対応
claude enhance --file openai_api_mcp_sample.py --instruction "モバイル対応とレスポンシブデザインを追加"
```

#### API統合の改善
```bash
# OpenAI API連携の最適化
claude optimize helper_api.py --focus "api-calls,error-handling,performance"

# データベース操作の改善
claude improve setup_test_data.py --instruction "SQLインジェクション対策とパフォーマンス向上"
```

#### 新機能開発
```bash
# 新しいMCPサーバー機能
claude create --file mcp_server_advanced.py --description "高度なMCPサーバー機能（キャッシュ、認証、ログ）"

# Streamlit用新しいページ
claude generate --type streamlit-page --description "リアルタイム分析ダッシュボード"
```

---

## 🎯 PyCharm Professional の使い方

### 1. プロジェクトセットアップ

#### 新しいプロジェクト作成
1. **File** → **New Project**
2. **Pure Python** を選択
3. **Location**: `/Users/your-name/mcp-streamlit-project`
4. **Python Interpreter**: 適切なPythonバージョン（3.8+）を選択
5. **Create**

#### 既存プロジェクトを開く
1. **File** → **Open**
2. MCPプロジェクトのフォルダを選択
3. **Open as Project** を選択

### 2. Python環境設定

#### インタープリター設定
```bash
# PyCharm内で: File → Settings → Project → Python Interpreter

# 仮想環境作成（ターミナル内で）
python -m venv venv
source venv/bin/activate  # Mac/Linux

# 必要パッケージのインストール
pip install -r requirements.txt
```

#### 環境変数設定
1. **Run** → **Edit Configurations**
2. **Environment Variables** に以下を追加：
```
OPENAI_API_KEY=your-api-key
PG_CONN_STR=postgresql://testuser:testpass@localhost:5432/testdb
PYTHONPATH=/path/to/your/project
```

### 3. Streamlit開発の最適化

#### Run Configuration設定
1. **Run** → **Edit Configurations**
2. **+** → **Python**
3. 設定：
   - **Name**: `Streamlit MCP App`
   - **Script path**: `/path/to/streamlit` (which streamlitで確認)
   - **Parameters**: `run openai_api_mcp_sample.py --server.port=8501`
   - **Working directory**: プロジェクトルート

#### デバッグ設定
```python
# openai_api_mcp_sample.py の先頭に追加
import streamlit as st

if __name__ == "__main__":
    # PyCharmデバッグ用の設定
    import sys
    if '--debug' in sys.argv:
        import debugpy
        debugpy.listen(5678)
        debugpy.wait_for_client()

    # 通常のStreamlit実行
    main()
```

### 4. 開発効率化機能

#### コード補完・ナビゲーション
- **Ctrl + Space**: コード補完
- **Cmd + B**: 定義へジャンプ
- **Cmd + F12**: ファイル構造表示
- **Cmd + Shift + F**: プロジェクト全体検索

#### リファクタリング
- **Shift + F6**: 名前変更
- **Cmd + Alt + M**: メソッド抽出
- **Cmd + Alt + V**: 変数抽出
- **Cmd + Alt + C**: 定数抽出

#### Git統合
1. **VCS** → **Enable Version Control Integration**
2. **Git** を選択
3. コミット: **Cmd + K**
4. プッシュ: **Cmd + Shift + K**

### 5. MCPプロジェクト特有の設定

#### ファイルテンプレート作成
1. **File** → **Settings** → **Editor** → **File and Code Templates**
2. **+** で新規テンプレート作成

**Streamlitページテンプレート**:
```python
# streamlit_page_template.py
import streamlit as st
from helper_st import UIHelper
from helper_mcp import ServerStatusManager

def render_${PAGE_NAME}_page():
    """${PAGE_NAME}ページの描画"""
    st.header("${PAGE_TITLE}")

    # ここにページ固有の処理を追加
    st.write("${PAGE_NAME}ページの内容")

def main():
    """メイン処理"""
    UIHelper.init_page("${PAGE_TITLE}")
    render_${PAGE_NAME}_page()

if __name__ == "__main__":
    main()
```

#### 外部ツール設定
1. **File** → **Settings** → **Tools** → **External Tools**
2. **+** で新規ツール追加

**Streamlit起動ツール**:
- **Name**: `Start Streamlit`
- **Program**: `streamlit`
- **Arguments**: `run $FileName$ --server.port=8501`
- **Working directory**: `$ProjectFileDir$`

**Docker Compose起動**:
- **Name**: `Start MCP Services`
- **Program**: `docker-compose`
- **Arguments**: `-f docker-compose.mcp-demo.yml up -d`
- **Working directory**: `$ProjectFileDir$`

### 6. デバッグとテスト

#### Streamlitアプリのデバッグ
```python
# デバッグ用のヘルパー関数
def debug_session_state():
    """セッション状態をデバッグ表示"""
    if st.checkbox("🐛 Debug Session State"):
        st.write("**Session State:**")
        for key, value in st.session_state.items():
            st.write(f"- `{key}`: {type(value).__name__}")
            if not key.startswith('_'):
                st.json(str(value)[:200])

# 使用例
debug_session_state()
```

#### pytest統合
```python
# tests/test_mcp_client.py
import pytest
from mcp_api_client import MCPAPIClient

class TestMCPAPIClient:
    def setup_method(self):
        self.client = MCPAPIClient("http://localhost:8000")

    def test_health_check(self):
        result = self.client.check_health()
        assert result is True
```

**Run Configuration**:
- **Name**: `pytest MCP`
- **Target**: `Custom`
- **Additional Arguments**: `-v tests/`

### 7. プロダクティビティプラグイン

#### 推奨プラグイン
1. **Python**: Python開発支援
2. **Database Tools and SQL**: PostgreSQL接続
3. **Docker**: Docker統合
4. **Rainbow Brackets**: 括弧の色分け
5. **GitToolBox**: Git機能拡張
6. **String Manipulation**: 文字列操作
7. **Key Promoter X**: ショートカット学習

#### プラグインインストール
1. **File** → **Settings** → **Plugins**
2. **Marketplace** タブで検索してインストール

### 8. データベース接続（PyCharm Professional限定）

#### PostgreSQL接続設定
1. **Database** タブを開く
2. **+** → **Data Source** → **PostgreSQL**
3. 接続情報入力：
   - **Host**: `localhost`
   - **Port**: `5432`
   - **Database**: `testdb`
   - **User**: `testuser`
   - **Password**: `testpass`

#### クエリ実行
```sql
-- PyCharm内でSQLファイルを作成して実行
SELECT c.name, COUNT(o.id) as order_count, SUM(o.price * o.quantity) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
ORDER BY total_spent DESC;
```

### 9. パフォーマンス監視

#### プロファイリング設定
```python
# performance_monitor.py
import cProfile
import pstats
from functools import wraps

def profile_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()

        # PyCharmコンソールに出力
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)

        return result
    return wrapper

# 使用例
@profile_function
def heavy_computation():
    # 重い処理
    pass
```

### 10. プロジェクト構造の最適化

#### 推奨フォルダ構造
```
mcp-streamlit-project/
├── .idea/                  # PyCharm設定（自動生成）
├── venv/                   # 仮想環境
├── src/                    # ソースコード
│   ├── __init__.py
│   ├── main/              # メインアプリケーション
│   │   ├── openai_api_mcp_sample.py
│   │   └── __init__.py
│   ├── helpers/           # ヘルパーモジュール
│   │   ├── helper_api.py
│   │   ├── helper_mcp.py
│   │   ├── helper_st.py
│   │   └── __init__.py
│   ├── api/               # API関連
│   │   ├── mcp_api_server.py
│   │   ├── mcp_api_client.py
│   │   └── __init__.py
│   └── utils/             # ユーティリティ
│       ├── setup_test_data.py
│       └── __init__.py
├── tests/                 # テストコード
├── docs/                  # ドキュメント
├── docker/                # Docker設定
├── requirements.txt
├── .env.example
└── README.md
```

## 🎯 実践的なワークフロー

### 1. 日常的な開発フロー
```bash
# 1. プロジェクト開始
cd mcp-streamlit-project
source venv/bin/activate

# 2. Claude Codeで新機能開発
claude create --file new_feature.py --description "新しい機能"

# 3. PyCharmで詳細実装
# - コード補完を使いながら実装
# - デバッガーで動作確認

# 4. Streamlitでテスト
streamlit run openai_api_mcp_sample.py --server.port=8501

# 5. Claude Codeでコードレビュー
claude review new_feature.py --focus "best-practices,security"

# 6. PyCharmでGitコミット
# Cmd + K でコミット
```

### 2. トラブルシューティング

#### よくある問題と解決方法

| 問題 | 原因 | 解決方法 |
|-----|------|----------|
| **モジュールが見つからない** | PYTHONPATH設定不備 | PyCharmのProject Structure設定確認 |
| **Streamlitが起動しない** | ポート競合 | `lsof -i :8501` でプロセス確認 |
| **データベース接続エラー** | Docker未起動 | `docker-compose up -d` 実行 |
| **Claude Code認証エラー** | APIキー設定不備 | `claude auth login` 再実行 |
| **デバッガーが動かない** | 設定ミス | Run Configuration再設定 |

## 🚀 まとめ

### Claude Code の強み
- **AI支援開発**: 自然言語でコード生成・編集
- **プロジェクト理解**: 全体構造を把握した提案
- **効率的なリファクタリング**: 大規模な改善も素早く

### PyCharm Professional の強み
- **強力なデバッグ機能**: ステップ実行、変数監視
- **データベース統合**: SQL実行、スキーマ管理
- **Git統合**: 視覚的な差分表示、マージ機能
- **プロファイリング**: パフォーマンス分析

### 最適な使い分け
- **アイデア段階**: Claude Code で素早くプロトタイプ
- **詳細実装**: PyCharm で精密な開発・デバッグ
- **コードレビュー**: Claude Code で品質チェック
- **本格運用**: PyCharm でプロダクション管理

この組み合わせにより、MCPプロジェクトの開発効率が大幅に向上します！
