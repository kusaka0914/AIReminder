from dotenv import load_dotenv
import os
import openai

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からAPIキーを取得
openai.api_key = os.getenv('OPENAI_API_KEY')

# OpenAI APIの使用例
try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "一人称が「オラ」で、口癖は「ワクワクすっぞ！」です。"},
            {"role": "user", "content": "明日の天下一武道会の意気込みをお願いします！"}
        ]
    )

    # レスポンス内容を出力
    print(response['choices'][0]['message']['content'].strip())

except Exception as e:
    print(f"エラーが発生しました: {e}")