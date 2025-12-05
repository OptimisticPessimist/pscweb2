#!/bin/bash

# エラーが発生した場合、即座に終了する
set -e

echo "Starting startup script..."

# 1. データベースマイグレーションの実行
echo "Applying database migrations..."
python manage.py migrate

# 2. 静的ファイルの収集
# Azure App Service はコードを /home/site/wwwroot に配置しますが、Dockerでは WORKDIR を使用します。
# settings.py で定義された STATIC_ROOT に静的ファイルが収集されるようにします。
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 3. Gunicornの起動
# 必要に応じてワーカー数を調整してください。
# pscweb2.wsgi は pscweb2/wsgi.py 内の WSGI アプリケーション呼び出し可能オブジェクトを参照します
echo "Starting Gunicorn..."
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 4 pscweb2.wsgi
