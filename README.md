# pscweb2
演劇の制作を支援するためのWebアプリケーションです。稽古スケジュールの管理、台本の共有、香盤表の作成など、制作プロセスを効率化する機能を提供します。
- **プロジェクトの状態**: 開発中
- **詳細情報**: [GitHub Pages](https://satamame.github.io/pscweb2/) (旧情報)


## 主な機能
- **公演管理**: 複数の公演（プロダクション）を管理できます。
- **台本管理**: Fountain形式で記述された台本を登録・管理できます。
- **PDFエクスポート**: 登録した台本を、縦書きレイアウトのPDFとしてダウンロードできます。
- **スケジュール管理**: 稽古のコマや場所を登録し、スケジュールを管理できます。
- **出欠管理と分析**: 役者ごとの出欠を登録し、香盤表や出欠表、稽古の出席率グラフなどを自動生成します。
- **メンバー管理**: 招待制で公演にメンバーを追加・管理できます。

## 技術スタック
- **バックエンド**: Django, Python
- **データベース**: PostgreSQL (ローカル開発推奨), Azure SQL Database (本番環境)
- **PDF生成**: WeasyPrint
- **デプロイ**: Azure App Service (Linux), Gunicorn

--- 

## 方法1：Docker Compose を使用する（推奨）
アプリケーションとデータベースをまとめてコンテナとして起動する方法です。PCに個別のライブラリをインストールする必要がありません。

### 1. 前提条件
- Docker Desktop がインストールされ、起動していること

### 2. 環境構築手順
#### a. プロジェクトの準備
ターミナルで、プロジェクトをクローンし、ディレクトリに移動します。
```shell
git clone https://github.com/OptimisticPessimist/pscweb2
cd pscweb2
```

#### b. 環境変数の設定
プロジェクトのルートに`.env`ファイルを作成します。`DB_PASSWORD`には任意のパスワードを設定してください。`DB_HOST`は`"db"`まま変更しないでください。
```shell
touch .env
```
以下の内容を`.env`ファイルに記述します。
```
# .env

# --- Django Core Settings ---
DEBUG=True
SECRET_KEY="your-super-secret-key-here" # あとで生成したキーに置き換える

# --- PostgreSQL Database Settings for Docker ---
DB_NAME="pscweb2"
DB_USER="pscweb2_user"
DB_PASSWORD="your-local-postgres-password" # 任意のパスワードを設定
DB_HOST="db" # Dockerサービス名のため、このままにする
DB_PORT="5432"
```

#### c. コンテナの起動
以下のコマンドで、Dockerイメージのビルドとコンテナの起動を行います。初回は少し時間がかかります。
```shell
docker-compose up --build
```

#### d. データベースの初期化
別のターミナルを開き、以下のコマンドを実行してデータベースのテーブルを作成します。
```shell
docker-compose exec web python manage.py migrate
```

#### e. スーパーユーザーの作成（任意）
管理サイトにログインするために、スーパーユーザーを作成します。
```shell
docker-compose exec web python manage.py createsuperuser
```

これで、ブラウザで http://localhost:8000 にアクセスすると、アプリケーションが表示されます。

---

## 方法2：WSL 2上で直接実行する（上級者向け）
本番環境であるAzure App Service (Linux)との互換性を高めるため、Windows Subsystem for Linux 2 (WSL 2) 上での開発を推奨します。

### 1. 前提条件
- Windows 11 または Windows 10 (バージョン 2004 以降)
- WSL 2 と Ubuntu
- Python 3.13
- uv (高速なPythonパッケージ管理ツール)

### 2. 環境構築手順

#### a. PostgreSQLのインストールと設定
WSLのUbuntuターミナルで、PostgreSQLをインストールし、データベースとユーザーを作成します。

```shell
# PostgreSQLをインストール
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# PostgreSQLサービスを開始
sudo service postgresql start

# pscweb2用のデータベースとユーザーを作成 (パスワード入力を求められます)
sudo -u postgres createuser --pwprompt pscweb2_user
sudo -u postgres createdb -O pscweb2_user pscweb2
```

#### b. プロジェクトの準備
Ubuntuのターミナルで、プロジェクトをクローンし、ディレクトリに移動します。

```shell
git clone https://github.com/OptimisticPessimist/pscweb2.git
cd pscweb2
```

#### c. システム依存関係のインストール
WeasyPrint (PDF生成) と pyodbc (SQL Database接続) が必要とするシステムライブラリをインストールします。

```shell
sudo apt update
sudo apt install -y curl gnupg
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list > /dev/null
sudo apt update
sudo apt install -y unixodbc-dev msodbcsql18 libgtk-3-0 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2 libffi-dev
```

#### d. Python環境のセットアップ
```shell
# uvをインストール (未インストールの場合)
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.cargo/env"

# 仮想環境を作成し、有効化
uv venv
source .venv/bin/activate

# 開発用の依存関係も含めてPythonパッケージをインストール
uv pip install .[local]
```

#### e. 環境変数の設定
プロジェクトのルートディレクトリに .env ファイルを作成し、DjangoのSECRET_KEYやデータベース接続情報を設定します。

```shell
# .env ファイルを作成
touch .env
```

以下の内容を元にして .env ファイルを記述してください。
```toml
# .env

# --- Django Core Settings ---
DEBUG=True
SECRET_KEY="your-super-secret-key-here" # あとで生成したキーに置き換える

# --- PostgreSQL Database Settings for Native WSL ---
DB_NAME="pscweb2"
DB_USER="pscweb2_user"
DB_PASSWORD="your-local-postgres-password" # 手順aで設定したパスワード
DB_HOST="localhost" # WSL上で直接実行するため、localhostを指定
DB_PORT="5432"
```

#### f. データベースの初期化とサーバーの起動
```shell
# シークレットキーを生成
uv run python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```shell
# データベースのマイグレーションを実行
uv run manage.py migrate

# 開発サーバーを起動
uv run manage.py runserver
```
ブラウザで http://127.0.0.1:8000/ にアクセスすると、アプリケーションが表示されます。

## デプロイ (Azure)
このアプリケーションは、Azure App Service (Linux) へのデプロイを想定しています。
- スタートアップスクリプト: startup.sh が、デプロイ時にシステム依存関係のインストール、マイグレーションの実行、Gunicornサーバーの起動を自動的に行います。
- 環境変数: Azure Portalのアプリケーション設定で、以下の環境変数を設定する必要があります。
  - DATABASE_URL: Azure SQL DatabaseのODBC接続文字列
  - SECRET_KEY: 本番用のシークレットキー
  - AZURE_HOSTNAME: App Serviceのホスト名 (例: yourapp.azurewebsites.net)
  - DEBUG: False

## ライセンス
このプロジェクトは MIT License の下で公開されています。