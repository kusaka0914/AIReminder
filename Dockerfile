FROM python:3.10-slim

# アプリケーションの作業ディレクトリ
WORKDIR /app

# 必要なファイルをコピー
COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

CMD gunicorn AIReminder.wsgi:application --bind 0.0.0.0:$PORT
