 pscweb2

演劇の制作を支援するためのWebアプリケーションです。稽古スケジュールの管理、台本の共有、香盤表の作成など、制作プロセスを効率化する機能を提供します。

-   **プロジェクトの状態:** 開発中
-   **詳細情報:** [GitHub Pages](https://satamame.github.io/pscweb2/) (旧情報)

## 主な機能

-   **公演管理:** 複数の公演（プロダクション）を管理できます。
-   **台本管理:** [Fountain](https://fountain.io/)形式で記述された台本を登録・管理できます。
-   **PDFエクスポート:** 登録した台本を、縦書きレイアウトのPDFとしてダウンロードできます。
-   **スケジュール管理:** 稽古のコマや場所を登録し、スケジュールを管理できます。
-   **出欠管理と分析:** 役者ごとの出欠を登録し、香盤表や出欠表、稽古の出席率グラフなどを自動生成します。
-   **メンバー管理:** 招待制で公演にメンバーを追加・管理できます。

## 技術スタック

-   **バックエンド:** Django, Python
-   **データベース:** PostgreSQL (ローカル開発推奨), Azure SQL Database (本番環境)
-   **PDF生成:** WeasyPrint
-   **デプロイ:** Azure App Service (Linux), Gunicorn

---

## ローカル開発環境の構築 (WSL 2)

本番環境であるAzure App Service (Linux)との互換性を高めるため、Windows Subsystem for Linux 2 (WSL 2) 上での開発を推奨します。

### 1. 前提条件

-   Windows 11 または Windows 10 (バージョン 2004 以降)
-   [WSL 2](https://learn.microsoft.com/ja-jp/windows/wsl/install) と Ubuntu
-   Python 3.13
-   [uv](https://github.com/astral-sh/uv) (高速なPythonパッケージ管理ツール)

### 2. 環境構築手順

#### a. WSLのインストール

まだWSLをインストールしていない場合、**管理者としてPowerShellを開き**、以下のコマンドを実行してPCを再起動します。

再起動後、Ubuntuのターミナルが開くので、指示に従ってユーザー名とパスワードを設定してください。b. プロジェクトの準備Ubuntuのターミナルで、プロジェクトをクローンし、ディレクトリに移動します。再起動後、Ubuntuのターミナルが開くので、指示に従ってユーザー名とパスワードを設定してください。

#### b. プロジェクトの準備

Ubuntuのターミナルで、プロジェクトをクローンし、ディレクトリに移動します。

#### c. システム依存関係のインストール

`WeasyPrint` (PDF生成) と `pyodbc` (SQL Database接続) が必要とするシステムライブラリをインストールします。

#### d. Python環境のセットアップ
高速なパッケージ管理ツール uv を使って、仮想環境の作成とパッケージのインストールを行います。

#### e. 環境変数の設定
プロジェクトのルートディレクトリに `.env` ファイルを作成し、Djangoの`SECRET_KEY`を設定します。ローカルでのテストを簡単にするため、データベースはSQLiteを使用します。

以下の内容を元にして `.env` ファイルを記述してください。
```.env
# .env

# --- Django Core Settings ---
# Set to 'True' for local development to enable detailed errors and local DB settings.
DEBUG='True'

# Generate a new key for your local environment.
# Run: uv run python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY="開発環境のシークレットキー"


# --- PostgreSQL Database Settings (for local development) ---
# These must match your local PostgreSQL server setup.
DB_NAME="pscweb2"
DB_USER="pscweb2_user"
DB_PASSWORD="ローカルのPostgreSQLパスワード"
DB_HOST="127.0.0.1"
DB_PORT="5432"


# --- Social Auth (Twitter) ---
# You can leave these blank if you are not testing Twitter login locally.
SOCIAL_AUTH_TWITTER_KEY=""
SOCIAL_AUTH_TWITTER_SECRET=""
```

#### f. データベースの初期化とサーバーの起動
ブラウザで http://127.0.0.1:8000/ にアクセスすると、アプリケーションが表示されます。

## デプロイ (Azure)

このアプリケーションは、Azure App Service (Linux) へのデプロイを想定しています。

-   **スタートアップスクリプト:** `startup.sh` が、デプロイ時にシステム依存関係のインストール、マイグレーションの実行、Gunicornサーバーの起動を自動的に行います。
-   **環境変数:** Azure Portalのアプリケーション設定で、以下の環境変数を設定する必要があります。
    -   `DATABASE_URL`: Azure SQL DatabaseのODBC接続文字列
    -   `SECRET_KEY`: 本番用のシークレットキー
    -   `AZURE_HOSTNAME`: App Serviceのホスト名 (例: `yourapp.azurewebsites.net`)
    -   `DEBUG`: `False`

## ライセンス

このプロジェクトは MIT License の下で公開されています。