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
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('generate')  # 'generate'はURLの名前
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login

def login_view(request):
    # ユーザーがすでにログインしている場合は/generateにリダイレクト
    if request.user.is_authenticated:
        return redirect('generate')  # 'generate'はURLの名前

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('generate')  # ログイン成功時も/generateにリダイレクト
        else:
            return render(request, 'login.html', {'error_message': 'メールアドレスまたはパスワードが正しくありません。'})
    
    return render(request, 'login.html')

# @login_required
# def question_view(request, keyword, question_number):
#     # セッションから全ての問題を取得
#     is_retry = request.POST.get('retry', 'false') == 'true'
#     if is_retry == "True":
#         all_questions = Question.objects.filter(user=request.user, theme=keyword)
#     else:
#         all_questions = request.session.get('all_questions', [])
    
#     # 問題番号が有効範囲内かチェック
#     if not all_questions or question_number < 1 or question_number > len(all_questions):
#         return redirect('index')
    
#     # 現在の問題を取得
#     current_question = all_questions[question_number - 1]
#     question_text = current_question['question_text']
    
#     # 問題文と選択肢を分離
#     lines = question_text.split('\n')
#     main_question = lines[0]  # 最初の行を問題文として扱う
    
#     # 選択肢を抽出 ((A)~(D))
#     options = []
#     for line in lines[1:]:  # 2行目以降から選択肢を探す
#         if line.strip().startswith('(') and ')' in line:
#             option_letter = line[1:line.index(')')].strip()
#             option_text = line[line.index(')')+1:].strip()
#             options.append({
#                 'letter': option_letter,
#                 'text': option_text
#             })
    
#     context = {
#         'question': main_question,
#         'options': options,
#         'keyword': keyword,
#         'question_number': question_number,
#         'total_questions': len(all_questions),
#         'has_next': question_number < len(all_questions),
#         'has_previous': question_number > 1,
#         'next_number': question_number + 1,
#         'previous_number': question_number - 1,
#         'is_retry': is_retry,
#     }
    
#     return render(request, 'question.html', context)

@login_required
def question_view(request, keyword, question_number):
    # セッションから全ての問題を取得
    is_retry = request.POST.get('retry', 'false') == 'true'
    question_text = request.POST.get('question_text', '')
    question_id = request.POST.get('question_id', '')
    if is_retry:
        all_questions = Question.objects.filter(user=request.user, theme=keyword, question_text=question_text)
    else:
        all_questions = request.session.get('all_questions', [])
    
    # # 問題番号が有効範囲内かチェック
    # if not all_questions or question_number < 1 or question_number > len(all_questions):
    #     return redirect('index')  # 'index'にリダイレクト

    # 現在の問題を取得
    if isinstance(all_questions, list):
        current_question = all_questions[question_number - 1]
        question_text = current_question['question_text']  # セッションから取得した場合
    # else:
    #     current_question = all_questions[question_number - 1]  # クエリセットから取得した場合
    #     question_text = current_question.question_text

    # 問題文と選択肢を分離
    lines = question_text.split('\n')
    main_question = lines[0] if lines else ""  # 最初の行を問題文として扱う
    
    # 選択肢を抽出 ((A)~(D))
    options = []
    for line in lines[1:]:  # 2行目以降から選択肢を探す
        if line.strip().startswith('(') and ')' in line:
            option_letter = line[1:line.index(')')].strip()
            option_text = line[line.index(')')+1:].strip()
            options.append({
                'letter': option_letter,
                'text': option_text
            })

    # # 選択肢が4つあるか確認
    # if len(options) != 4:
    #     print("選択肢の数が不正です。")
    #     return redirect('generate')  # 選択肢が不正な場合はリダイレクト


    context = {
        'question': main_question,
        'options': options,
        'question_text': question_text,
        'keyword': keyword,
        'question_number': question_number,
        'question_id': question_id,
        'total_questions': len(all_questions),
        'has_next': question_number < len(all_questions),
        'has_previous': question_number > 1,
        'next_number': question_number + 1,
        'previous_number': question_number - 1,
        'is_retry': is_retry,
    }
    
    return render(request, 'question.html', context)

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からAPIキーを取得
openai.api_key = os.getenv('OPENAI_API_KEY')

@login_required
def index(request):
    user = request.user
    daily_generated_count = user.daily_generated_count
    is_premium = user.is_premium
    context = {
        'daily_generated_count': daily_generated_count,
        'is_premium': is_premium
    }
    return render(request, 'index.html', context)

@login_required
def question_history(request):
    user = request.user
    questions = Question.objects.filter(user=user).values('theme', 'question_text', 'is_correct')
    return render(request, 'history.html', {'questions': questions})

from difflib import SequenceMatcher

def is_similar(new_question, past_questions, threshold=0.4):
    for past_question in past_questions:
        similarity = SequenceMatcher(None, new_question, past_question.question_text).ratio()
        if similarity > threshold:
            return True
    return False

import pytesseract
from PIL import Image
from .forms import FileUploadForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import UnidentifiedImageError
import PyPDF2
@csrf_exempt
def generate_question(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            if request.FILES.get('file'):
                print("fileが添付されています。")
                user = request.user
                uploaded_file = form.cleaned_data['file']
                file_type = uploaded_file.content_type

                if file_type.startswith('image/'):
                    # 画像ファイルの処理
                    image = Image.open(uploaded_file)
                    width, height = image.size
                    extracted_text = f"画像のサイズは{width}x{height}です。"

                elif file_type == 'application/pdf':
                    # PDFファイルの処理
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    extracted_text = ""
                    for page in pdf_reader.pages:
                        extracted_text += page.extract_text()

                max_attempts = 5
                attempt = 0
                valid_questions = []
                theme = extracted_text[:10]

                while attempt < max_attempts and len(valid_questions) < 10:
                    attempt += 1
                # ChatGPT APIで問題を生成
                    prompt = f"次のテキストを読み、実用的な4択問題を10個作成してください。:{extracted_text}正解はまだ表示しないでください。"
                    print(prompt)
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "問題の選択肢は (A)選択肢の内容 (B)選択肢の内容 (C)選択肢の内容 (D)選択肢の内容 という形で出力してください。"},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    questions_data_all = response.choices[0].message.content.strip() 
                    questions_data = questions_data_all.split('\n\n')  # 各質問を分割

                    for question_data in questions_data:
                        print(question_data)
                        lines = question_data.split('\n')
                        non_empty_lines = [line for line in lines if line.strip() != '']
                        if len(non_empty_lines) < 5:
                            continue  # 空でない行が6以下の場合はスキップ

                        # 問題文の検証
                        main_question = lines[0].strip()
                        if not main_question or len(main_question) < 10:
                            continue  # 問題文が空または5文字未満の場合はスキップ

                        valid_questions.append(question_data)

                    # 十分な数の有効な問題が生成された場合、ループを終了
                    if len(valid_questions) >= 10:
                        break

                if len(valid_questions) < 10:
                    return render(request, 'index.html', {
                        'error_message': "有効な問題を生成できませんでした。別のキーワードでお試しください。"
                    })

                request.session['all_questions'] = []
                for i, question_data in enumerate(valid_questions[:10], 1):
                    # Questionモデルに保存
                    question = Question.objects.create(
                        user=user,
                        theme=theme,
                        question_text=question_data,
                        question_number=i,
                    )
                    
                    # セッションに問題データを追加
                    request.session['all_questions'].append({
                        'question_id': question.id,
                        'question_text': question_data,
                        'theme': theme,
                        'question_number': i
                    })
                
                request.session.modified = True

                user.generate_count += 10
                user.save()
                # 最初の問題にリダイレクト
                return redirect('question', keyword=theme, question_number=1)
        else:
            try:
                theme = request.POST.get('theme', '').replace('　', ' ')
                difficulty = request.POST.get('difficulty', 'medium')  # デフォルトは普通
                user = request.user
                today = timezone.now().date()

                # 難易度に応じたレベル設定
                level_map = {
                    'basic': '初級レベル',
                    'advanced': '上級レベル',
                    'master': '最上級レベル'
                }
                level = level_map.get(difficulty, '上級')

                # プレミアムユーザーでない場合、1日の生成数を制限
                if not user.is_premium:
                    if user.last_generated_date == today:
                        if user.daily_generated_count >= 10:
                            return render(request, 'index.html', {
                                'error_message': "1日に生成できる問題数の上限に達しました。"
                            })
                    else:
                        # 新しい日付の場合、カウントをリセット
                        user.last_generated_date = today
                        user.daily_generated_count = 0

                # ユーザーの過去の質問を取得
                past_questions = Question.objects.filter(user=user, theme=theme)[:20]

                # 問題生成の試行回数を制限
                max_attempts = 5
                attempt = 0
                valid_questions = []

                while attempt < max_attempts and len(valid_questions) < 10:
                    attempt += 1
                    prompt = f"{theme}に関する、実用的な4択問題を10個作成してください。作成する問題の難易度は{level}です。しっかりとこのレベルの問題を作成してください。正解はまだ表示しないでください。"
                    print(prompt)
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "問題の選択肢は (A)選択肢の内容 (B)選択肢の内容 (C)選択肢の内容 (D)選択肢の内容 という形で出力してください。問題はきちんと1~10の順番で出力してください。"},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    questions_data_all = response.choices[0].message.content.strip() 
                    questions_data = questions_data_all.split('\n\n')  # 各質問を分割

                    # 検証ロジックを追加
                    for question_data in questions_data:
                        print(question_data)
                        lines = question_data.split('\n')
                        non_empty_lines = [line for line in lines if line.strip() != '']
                        if len(non_empty_lines) < 5:
                            continue  # 空でない行が6以下の場合はスキップ

                        # 問題文の検証
                        main_question = lines[0].strip()
                        if not main_question or len(main_question) < 10:
                            continue  # 問題文が空または5文字未満の場合はスキップ

                        # 類似度のチェック
                        if is_similar(main_question, past_questions):
                            continue  # 過去の質問と似ている場合はスキップ

                        valid_questions.append(question_data)
                        if not user.is_premium:
                            user.daily_generated_count += 1
                            user.save()

                    # 十分な数の有効な問題が生成された場合、ループを終了
                    if len(valid_questions) >= 10:
                        break

                if len(valid_questions) < 10:
                    return render(request, 'index.html', {
                        'error_message': "有効な問題を生成できませんでした。別のキーワードでお試しください。"
                    })

                # セッションに全ての問題を保存
                request.session['all_questions'] = []
                
                for i, question_data in enumerate(valid_questions[:10], 1):
                    # Questionモデルに保存
                    question = Question.objects.create(
                        user=user,
                        theme=theme,
                        question_text=question_data,
                        question_number=i,
                        difficulty=difficulty
                    )
                    
                    # セッションに問題データを追加
                    request.session['all_questions'].append({
                        'question_id': question.id,
                        'question_text': question_data,
                        'theme': theme,
                        'question_number': i
                    })
                
                request.session.modified = True

                user.generate_count += len(valid_questions)
                user.save()
                # 最初の問題にリダイレクト
                return redirect('question', keyword=theme, question_number=1)

            except Exception as e:
                return JsonResponse({"error": str(e)}, status=500)
        return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def answer_question(request, keyword, question_number):
    if request.method == 'POST':
        try:
            user_answer = request.POST.get('answer', '')  # 例: "A"
            is_retry = request.POST.get('retry', '')
            question_text = request.POST.get('question_text', '')
            question_id = request.POST.get('question_id', '')
            print("idの前")
            print("question_id", question_id)
            print("idの後")
            if is_retry == "True":
                all_questions = Question.objects.filter(user=request.user, theme=keyword, question_text=question_text)
                print(all_questions)
            else:
                all_questions = request.session.get('all_questions', [])
            
            # if not all_questions or question_number < 1 or question_number > len(all_questions):
            #     return redirect('generate')
            
            if isinstance(all_questions, list):
                current_question = all_questions[question_number - 1]
                question_data = current_question['question_text']  # セッションから取得した場合
                question_id = current_question['question_id']
            # else:
            #     current_question = all_questions[question_number - 1]  # クエリセットから取得した場合
            #     question_data = current_question.question_text
            #     question_id = current_question.id

            # AIにユーザーの回答を判定させる
            check_prompt = f"""
            問題: {question_text}
            ユーザーの回答: {user_answer}
            
            この回答が正しいかどうかを判定し、解説を提供してください。
            以下の形式で出力してください：
            正解:(A/B/C/D)
            解説:解説内容
            解説は誰でも理解できるようにしてください。
            解説は180文字以上220文字以下で出力してください。必ずです。
            """
            
            check_response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "正解は必ず(A)〜(D)の中から1つ選んでください。"},
                    {"role": "user", "content": check_prompt}
                ]
            )
            
            explanation = check_response.choices[0].message.content.strip()
            
            # 正解の抽出方法を修正
            correct_option = None
            explanation_text = ""
            
            for line in explanation.split('\n'):
                if line.startswith('正解:'):
                    correct_option = line.replace('正解:', '').strip().replace('(', '').replace(')', '')
                elif line.startswith('解説:'):
                    explanation_text = line.replace('解説:', '').strip()

            # 正誤を判定（大文字小文字を区別しない）
            is_correct = user_answer.upper() == correct_option.upper()

            context = {
                'question': question_text,
                'question_text': question_text,
                'keyword': keyword,
                'question_number': question_number,
                'total_questions': len(all_questions),
                'has_next': question_number < len(all_questions),
                'next_number': question_number + 1,
                'is_correct': is_correct,
                'question_id': question_id,
                'explanation': explanation_text,
                'correct_option': correct_option,  # AIが選んだ正解を追加
                'is_retry': is_retry,
                'user_answer': user_answer,
                'debug_info': {  # デバッグ情報を追加
                    'user_answer': user_answer,
                    'correct_option': correct_option,
                    'is_correct': is_correct,
                    'raw_explanation': explanation
                }
            }

            # Questionモデルを更新
            question = Question.objects.get(id=question_id)
            if question.is_correct_first is None:
                question.is_correct_first = is_correct
                first= True
            else:
                question.is_correct = is_correct
                first= False
            
            question.correct_option = correct_option
            question.explanation = explanation_text
            question.save()

            user = request.user

            if first and is_correct:
                user.correct_count += 1
                user.save()

            if user.generate_count > 0:
                user.accuracy = user.correct_count / user.generate_count * 100
                user.save()

            return render(request, 'answer.html', context)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def update_not_answered_count(user):
    # is_correctがNoneの質問をフィルタリング
    not_answered_questions = Question.objects.filter(user=user, is_correct=None)
    
    # カウントを計算
    not_answered_count = not_answered_questions.count()
    
    # ユーザーオブジェクトを更新
    user.not_answered_count = not_answered_count
    user.save()

@login_required
def profile_view(request):
    user = request.user  # request.userを使用して現在のユーザーを取得
    
    # not_answered_countを更新
    # update_not_answered_count(user)
    
    correct_count = user.correct_count
    generate_count = user.generate_count
    accuracy = round(user.accuracy, 1)  # 正答率を小数点第1位までに丸める
    not_answered_count = user.not_answered_count
    
    # ユーザーの生成した問題を取得
    user_questions = Question.objects.filter(user=user)  # request.userを使用
    
    # キーワードの集計
    keyword_counts = {}
    for question in user_questions:
        keyword = question.theme  # 例: Questionモデルにkeywordフィールドがあると仮定
        if keyword in keyword_counts:
            keyword_counts[keyword] += 1
        else:
            keyword_counts[keyword] = 1
    
    # 最も多いキーワードを取得
    favorite_keyword = max(keyword_counts, key=keyword_counts.get) if keyword_counts else "なし"
    
    return render(request, 'profile.html', {
        'correct_count': correct_count,
        'generate_count': generate_count,
        'accuracy': accuracy,
        'favorite_keyword': favorite_keyword,
        'not_answered_count': not_answered_count  # 追加
    })

@login_required
def allkeyword_view(request):
    search_query = request.GET.get('search', '')
    sort_option = request.GET.get('sort', 'alphabetical')

    # テーマごとの問題数をカウント
    user_themes = Question.objects.filter(user=request.user).values('theme').annotate(count=Count('theme'))

    if search_query:
        user_themes = user_themes.filter(theme__icontains=search_query)

    # 並び替えオプションに基づいて並び替え
    if sort_option == 'count':
        user_themes = user_themes.order_by('-count')
    else:
        user_themes = user_themes.order_by('theme')

    # テーマ名とその問題数のリストに変換
    user_themes_list = [{'theme': theme['theme'], 'count': theme['count']} for theme in user_themes]

    return render(request, 'allkeyword.html', {'user_themes': user_themes_list})

def allquestion_view(request):
    return render(request, 'allquestion.html')

@login_required
def keyword_questions_view(request, keyword):
    # フィルター条件を取得
    filter_option = request.GET.get('filter', 'all')

    # キーワードに基づいて問題を取得
    questions = Question.objects.filter(user=request.user, theme=keyword)

    # フィルター条件に基づいて質問をフィルタリング
    if filter_option == 'incorrect_first':
        questions = questions.filter(is_correct_first=False)
    elif filter_option == 'correct_first':
        questions = questions.filter(is_correct_first=True)
    elif filter_option == 'incorrect_second':
        questions = questions.filter(is_correct=False)
    elif filter_option == 'correct_second':
        questions = questions.filter(is_correct=True)
    elif filter_option == 'retry_none':
        questions = questions.filter(is_correct=None)
    # 他のフィルター条件を追加する場合はここに追加

    # 番号を削除したテキストを作成
    cleaned_questions = []
    for question in questions:
        text = question.question_text
        question_id = question.id
        question_number = question.question_number
        is_correct_first = question.is_correct_first
        is_correct = question.is_correct
        # 最初の数字とピリオドを削除
        cleaned_text = text.replace('問', '').strip()
        cleaned_text = cleaned_text.replace('題', '').strip()
        cleaned_text = cleaned_text.replace('0', '').strip()
        cleaned_text = cleaned_text.replace('1', '').strip()
        cleaned_text = cleaned_text.replace('2', '').strip()
        cleaned_text = cleaned_text.replace('3', '').strip()
        cleaned_text = cleaned_text.replace('4', '').strip()
        cleaned_text = cleaned_text.replace('5', '').strip()
        cleaned_text = cleaned_text.replace('6', '').strip()
        cleaned_text = cleaned_text.replace('7', '').strip()
        cleaned_text = cleaned_text.replace('8', '').strip()
        cleaned_text = cleaned_text.replace('9', '').strip()
        cleaned_text = cleaned_text.replace('10', '').strip()
        cleaned_text = cleaned_text.replace(':', '').strip()
        cleaned_text = cleaned_text.replace('.', '').strip()
        if '？' in cleaned_text:
            cleaned_text = cleaned_text.split('？')[0].strip() + '？'
        if '。' in cleaned_text:
            cleaned_text = cleaned_text.split('。')[0].strip() + '？'
        cleaned_questions.append({"original_text": text, 'text': cleaned_text, 'question_number': question_number, 'is_correct_first': is_correct_first, 'is_correct': is_correct, 'question_id': question_id})
    
    return render(request, 'keyword_questions.html', {'questions': cleaned_questions, 'keyword': keyword, 'user': request.user})

@login_required
def explanation_view(request, keyword, question_number):
    if request.method == 'POST':
        try:
            user_answer = request.POST.get('answer', '')  # 例: "A"
            is_retry = request.POST.get('retry', '')
            question_text = request.POST.get('question_text', '')
            question_id = request.POST.get('question_id', '')
            if is_retry == "true":
                all_questions = Question.objects.filter(user=request.user, theme=keyword)
            else:
                all_questions = request.session.get('all_questions', [])
            
            if not all_questions or question_number < 1 or question_number > len(all_questions):
                return redirect('index')
            
            if isinstance(all_questions, list):
                current_question = all_questions[question_number - 1]
                question_data = current_question['question_text']  # セッションから取得した場合
                question_id = current_question['question_id']
            # else:
                # current_question = all_questions[question_number - 1]  # クエリセットから取得した場合
                # question_data = current_question.question_text
                # question_id = current_question.id

            # AIにユーザーの回答を判定させる
            check_prompt = f"""
            問題: {question_text}
            ユーザーの回答: {user_answer}
            
            この回答が正しいかどうかを判定し、解説を提供してください。
            以下の形式で出力してください：
            正解:(A/B/C/D)
            解説:解説内容
            解説は誰でも理解できるようにしてください。
            解説は180文字以上220文字以下で出力してください。必ずです。
            """
            
            check_response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "正解は必ず(A)〜(D)の中から1つ選んでください。"},
                    {"role": "user", "content": check_prompt}
                ]
            )
            
            explanation = check_response.choices[0].message.content.strip()
            
            # 正解の抽出方法を修正
            correct_option = None
            explanation_text = ""
            
            for line in explanation.split('\n'):
                if line.startswith('正解:'):
                    correct_option = line.replace('正解:', '').strip().replace('(', '').replace(')', '')
                elif line.startswith('解説:'):
                    explanation_text = line.replace('解説:', '').strip()

            # 正誤を判定（大文字小文字を区別しない）
            is_correct = user_answer.upper() == correct_option.upper()

            context = {
                'question': question_text,
                'keyword': keyword,
                'question_number': question_number,
                'question_text': question_text,
                'total_questions': len(all_questions),
                'has_next': question_number < len(all_questions),
                'next_number': question_number + 1,
                'is_correct': is_correct,
                'explanation': explanation_text,
                'correct_option': correct_option,  # AIが選んだ正解を追加
                'is_retry': is_retry,
                'user_answer': user_answer,
                'debug_info': {  # デバッグ情報を追加
                    'user_answer': user_answer,
                    'correct_option': correct_option,
                    'is_correct': is_correct,
                    'raw_explanation': explanation
                }
            }

            # Questionモデルを更新
            question = Question.objects.get(id=question_id)
            if is_retry:
                question.is_correct = is_correct
            if question.is_correct_first is None:
                question.is_correct_first = is_correct
            question.correct_option = correct_option
            question.explanation = explanation_text
            question.save()

            user = request.user

            if is_correct:
                user.correct_count += 1
                user.save()

            if user.generate_count > 0:
                user.accuracy = user.correct_count / user.generate_count * 100
                user.save()

            return render(request, 'explanation.html', context)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def keyword_history(request):
    user = request.user
    # テーマのリストを取得
    keywords = Question.objects.filter(user=user).values_list('theme', flat=True).distinct()
    return JsonResponse({'keywords': list(keywords)})



# your_app/views.py
import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Subscription
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import get_user_model
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

User = get_user_model()

@login_required
def create_checkout_session(request, plan):
    PLAN_PRICE_MAP = {
        'basic': 'price_1QWgzYRsfW3rHLql8AgXGsxq',      # 事前にStripeで作成した価格IDを入力
        'premium': 'price_1QWh03RsfW3rHLqlJwmfjxTP',   # 実際のプレミアムプランの価格IDに置き換えてください
    }

    price_id = PLAN_PRICE_MAP.get(plan)
    if not price_id:
        logger.error(f"Invalid plan requested: {plan}")
        return HttpResponse("Invalid plan", status=400)

    domain = "http://localhost:8001"  # ローカル開発環境の場合。デプロイ先では適宜変更してください

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=request.user.email,  # ユーザーのメールアドレスを使用
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=domain + reverse('success'),
            cancel_url=domain + reverse('cancel'),
        )
        logger.info(f"Checkout session created: {checkout_session.id}")
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Stripe InvalidRequestError: {e.user_message}")
        return HttpResponse(f"Stripe error: {e.user_message}", status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return HttpResponse("An unexpected error occurred.", status=500)

    return redirect(checkout_session.url, code=303)

def success(request):
    return render(request, 'success.html')

def cancel(request):
    return render(request, 'cancel.html')

# your_app/views.py
import stripe
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Subscription
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import get_user_model
import logging

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

User = get_user_model()

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        logger.info(f"Received event: {event['type']}")
    except ValueError:
        # 無効なペイロード
        logger.error("Invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # 無効な署名
        logger.error("Invalid signature")
        return HttpResponse(status=400)

    # イベントタイプに応じて処理を分岐
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_invoice_payment_succeeded(invoice)

    # 他のイベントタイプも必要に応じて処理

    return HttpResponse(status=200)

@login_required
def create_checkout_session(request, plan):
    PLAN_PRICE_MAP = {
        'basic': 'price_1QWgzYRsfW3rHLql8AgXGsxq',      # 事前にStripeで作成した価格IDを入力
        'premium': 'price_1QWh03RsfW3rHLqlJwmfjxTP',   # 実際のプレミアムプランの価格IDに置き換えてください
    }

    price_id = PLAN_PRICE_MAP.get(plan)
    if not price_id:
        logger.error(f"Invalid plan requested: {plan}")
        return HttpResponse("Invalid plan", status=400)

    domain = "http://localhost:8001"  # ローカル開発環境の場合。デプロイ先では適宜変更してください

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=request.user.email,  # ユーザーのメールアドレスを使用
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=domain + reverse('success'),
            cancel_url=domain + reverse('cancel'),
        )
        logger.info(f"Checkout session created: {checkout_session.id}")
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Stripe InvalidRequestError: {e.user_message}")
        return HttpResponse(f"Stripe error: {e.user_message}", status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return HttpResponse("An unexpected error occurred.", status=500)

    return redirect(checkout_session.url, code=303)

def success(request):
    return render(request, 'success.html')

def cancel(request):
    return render(request, 'plans.html')

def handle_checkout_session(session):
    customer_email = session.get('customer_email')
    logger.info(f"Handling checkout session for email: {customer_email}")

    if not customer_email:
        logger.error("No customer_email found in session.")
        return

    try:
        user = User.objects.get(email=customer_email)
        logger.info(f"Found user: {user.username}")
    except User.DoesNotExist:
        logger.error(f"User with email {customer_email} does not exist.")
        return

    subscription_id = session.get('subscription')
    logger.info(f"Subscription ID: {subscription_id}")

    if not subscription_id:
        logger.error("No subscription ID found in session.")
        return

    subscription, created = Subscription.objects.get_or_create(user=user)
    subscription.stripe_customer_id = session.get('customer')
    subscription.stripe_customer_id = session.get('customer')
# ここでUserモデルにもstripe_customer_idを紐付けるフィールドがあるなら更新
    user.stripe_customer_id = session.get('customer')
    user.save()
    subscription.stripe_subscription_id = subscription_id
    subscription.active = True
    subscription.plan = determine_plan_from_subscription(subscription_id)
    subscription.save()
    logger.info(f"Subscription saved: {subscription}")

    # ユーザーのis_premiumをTrueに設定
    user.is_premium = True
    user.save()
    logger.info(f"User {user.username} is_premium set to True.")

def handle_subscription_deleted(subscription):
    # サブスクリプションが削除された場合、is_premiumをFalseに設定
    customer_id = subscription.get('customer')
    try:
        user = User.objects.get(subscription__stripe_customer_id=customer_id)
        logger.info(f"Found user: {user.username} for subscription deletion.")
    except User.DoesNotExist:
        logger.error(f"User with customer ID {customer_id} does not exist.")
        return
        

    user.is_premium = False
    user.save()
    logger.info(f"User {user.username} is_premium set to False.")

def handle_invoice_payment_succeeded(invoice):
    # 支払い成功時の処理
    logger.info("Payment succeeded for invoice: " + invoice.get('id'))

    customer_id = invoice.get('customer')
    if not customer_id:
        logger.error("No customer ID found in invoice.")
        return

    try:
        user = User.objects.get(subscription__stripe_customer_id=customer_id)
        logger.info(f"Found user: {user.username} for invoice payment.")
    except User.DoesNotExist:
        logger.error(f"User with customer ID {customer_id} does not exist.")
        return
    
    user.stripe_customer_id = invoice.get('customer')
    user.save()

    # 必要に応じて追加の処理を行う
    user.is_premium = True
    user.save()
    logger.info(f"User {user.username} is_premium set to True after payment.")
    print("変更")
    print(user.is_premium)
    print("変更")

def determine_plan_from_subscription(subscription_id):
    subscription = stripe.Subscription.retrieve(subscription_id)
    price_id = subscription['items']['data'][0]['price']['id']
    # 価格IDからプランを判定
    PRICE_PLAN_MAP = {
        'price_1QWgzYRsfW3rHLql8AgXGsxq': 'basic',      # ベーシックプランの価格ID
        'price_1QWh03RsfW3rHLqlJwmfjxTP': 'premium',   # プレミアムプランの価格ID
    }
    return PRICE_PLAN_MAP.get(price_id, 'basic')

@login_required
def plans(request):
    return render(request, 'plans.html')
