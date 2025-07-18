!/bin/bash

# Microsoftの公式リポジトリキーを追加
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
# Microsoftのソフトウェアリポジトリを追加
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# パッケージリストを更新し、ODBCドライバとWeasyPrintの依存関係をインストール
apt-get update && apt-get install -y \
    unixodbc-dev \
    msodbcsql17 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev

# Djangoのマイグレーションを実行
python manage.py migrate

# Gunicornでアプリケーションを起動
gunicorn --bind=0.0.0.0 --workers=2 pscweb2.wsgi