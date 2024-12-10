from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os
import openai
from django.contrib.auth.models import User
from .models import Question
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'signup.html', {'error_message': 'パスワードが一致しません。'})

        User = get_user_model()
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error_message': 'このメールアドレスは既に登録されています。'})

        user = User.objects.create(
            email=email,
            username=email,
            password=make_password(password),
            is_premium=False
        )
        return redirect('login')  # 登録後のリダイレクト先

    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')  # ログイン後のリダイレクト先
        else:
            return render(request, 'login.html', {'error_message': 'メールアドレスまたはパスワードが正しくありません。'})
    return render(request, 'login.html')

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からAPIキーを取得
openai.api_key = os.getenv('OPENAI_API_KEY')

def index(request):
    return render(request, 'index.html')

def question_history(request):
    user = request.user
    questions = Question.objects.filter(user=user).values('theme', 'question_text', 'is_correct')
    return render(request, 'history.html', {'questions': questions})

from difflib import SequenceMatcher

def is_similar(new_question, past_questions, threshold=0.2):
    for past_question in past_questions:
        similarity = SequenceMatcher(None, new_question, past_question.question_text).ratio()
        if similarity > threshold:
            return True
    return False

@csrf_exempt
def generate_question(request):
    if request.method == 'POST':
        try:
            theme = request.POST.get('theme', '')
            user = request.user

            # ユーザーの過去の質問を取得
            past_questions = Question.objects.filter(user=user, theme=theme)

            # 新しい質問を生成するためのループ
            prompt = f"{theme}というキーワードに関する4択問題を10個作成してください。正解はまだ表示しないでください。"
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "問題の選択肢は (A)選択肢の内容 (B)選択肢の内容 (C)選択肢の内容 (D)選択肢の内容 という形で出力してください。"},
                    {"role": "user", "content": prompt}
                ]
            )
            questions_data_all = response.choices[0].message.content.strip() 
            questions_data = response.choices[0].message.content.strip().split('\n\n')  # 各質問を分割

            if not is_similar(questions_data_all, past_questions):
            
                for question_data in questions_data:
                    correct_option = ""  # 例として固定の正解

                    # Questionモデルに保存
                    question = Question.objects.create(
                        user=user,
                        theme=theme,
                        question_text=question_data,
                    )

                    request.session['question_id'] = question.id

                    

                return JsonResponse({
                        "question": questions_data_all,
                        "correct_option": correct_option
                    }, status=200)
            else:
                correct_option = ""
                return JsonResponse({
                        "question": "このキーワードで生成できる全ての問題を生成しました。他のキーワードでお試しください。",
                        "correct_option": correct_option
                    }, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def answer_question(request):
    if request.method == 'POST':
        try:
            user_answer = request.POST.get('answer', '')
            correct_option = request.session.get('correct_option', '')
            question_data = request.session.get('question_data', '')

            # AIにユーザーの回答を判定させる
            check_prompt = f"問題: {question_data}\nユーザーの回答は「{user_answer}」です。この回答が正しいかどうかを判定し、解説を提供してください。形式は「正解は「」です。解説:解説内容」という形で出力してください。"
            check_response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "淡々とした口調で"},
                    {"role": "user", "content": check_prompt}
                ]
            )
            explanation = check_response.choices[0].message.content.strip()
            correct_option = explanation.split("正解は「")[1].split("」")[0]
            explanation_text = explanation.split("解説:")[1]

            question = Question.objects.get(id=request.session.get('question_id', ''))
            question.is_correct = user_answer == correct_option
            question.correct_option = correct_option
            question.explanation = explanation_text
            question.save()

            return JsonResponse({"explanation": explanation}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)