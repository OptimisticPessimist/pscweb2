# F:/src/PythonProject/pscweb2/Dockerfile

# ベースイメージをPython 3.13に更新
FROM python:3.13-slim

# 環境変数設定
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
# MicrosoftのODBCドライバとWeasyPrintの依存関係を一度にインストール
RUN apt-get update && \
    apt-get install -y curl gnupg && \
    # Microsoftの公式リポジトリキーを追加
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    # Microsoftのソフトウェアリポジトリを追加 (Debian 12 "Bookworm" for Python 3.13)
    curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    # パッケージリストを更新し、必要なライブラリをインストール
    apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc-dev \
    msodbcsql18 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libcairo2 \
    libffi-dev \
    # 不要になったパッケージキャッシュを削除
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 高速なパッケージ管理ツール uv をインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# pyproject.tomlをコピーして、先にパッケージをインストール
COPY pyproject.toml ./

# localの依存関係も一緒にインストールする
RUN uv pip sync pyproject.toml --all-extras

# プロジェクトのコードをコピー
COPY . .

# 開発サーバーが使用するポートを公開
EXPOSE 8000