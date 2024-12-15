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
    if is_retry:
        all_questions = Question.objects.filter(user=request.user, theme=keyword)
    else:
        all_questions = request.session.get('all_questions', [])
    
    # 問題番号が有効範囲内かチェック
    if not all_questions or question_number < 1 or question_number > len(all_questions):
        return redirect('generate')
    
    # 現在の問題を取得
    if isinstance(all_questions, list):
        current_question = all_questions[question_number - 1]
        question_text = current_question['question_text']  # セッションから取得した場合
    else:
        current_question = all_questions[question_number - 1]  # クエリセットから取得した場合
        question_text = current_question.question_text
    
    # デバッグ用出力
    print(f"Question Text: {question_text}")

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
    
    # デバッグ用出力
    print(f"Options: {options}")

    context = {
        'question': main_question,
        'options': options,
        'keyword': keyword,
        'question_number': question_number,
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
    return render(request, 'index.html')

@login_required
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
            theme = request.POST.get('theme', '').replace('　', ' ')
            user = request.user

            # ユーザーの過去の質問を取得
            past_questions = Question.objects.filter(user=user, theme=theme)

            prompt = f"{theme}というキーワードに関する4択問題を10個作成してください。正解はまだ表示しないでください。"
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "問題の選択肢は (A)選択肢の内容 (B)選択肢の内容 (C)選択肢の内容 (D)選択肢の内容 という形で出力してください。問題は問1 問2 問3 問4 問5 問6 問7 問8 問9 問10.という形で出力してください。"},
                    {"role": "user", "content": prompt}
                ]
            )
            questions_data_all = response.choices[0].message.content.strip() 
            questions_data = response.choices[0].message.content.strip().split('\n\n')  # 各質問を分割

            if not is_similar(questions_data_all, past_questions):
                # セッションに全ての問題を保存
                request.session['all_questions'] = []
                
                for i, question_data in enumerate(questions_data, 1):
                    # Questionモデルに保存
                    question = Question.objects.create(
                        user=user,
                        theme=theme,
                        question_text=question_data,
                        question_number=i
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
                return render(request, 'index.html', {
                    'error_message': "このキーワードで生成できる全ての問題を生成しました。他のキーワードでお試しください。"
                })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def answer_question(request, keyword, question_number, question_text):
    if request.method == 'POST':
        try:
            user_answer = request.POST.get('answer', '')  # 例: "A"
            is_retry = request.POST.get('retry', '')
            if is_retry == "True":
                all_questions = Question.objects.filter(user=request.user, theme=keyword,question_text=question_text)
            else:
                all_questions = request.session.get('all_questions', [])
            
            if not all_questions or question_number < 1 or question_number > len(all_questions):
                return redirect('generate')
            
            if isinstance(all_questions, list):
                current_question = all_questions[question_number - 1]
                question_data = current_question['question_text']  # セッションから取得した場合
                question_id = current_question['question_id']
            else:
                current_question = all_questions[question_number - 1]  # クエリセットから取得した場合
                question_data = current_question.question_text
                question_id = current_question.id

            # デバッグ用出力
            print(f"is_retry: {is_retry}")
            print(f"all_questions: {all_questions}")
            print(f"Question Data: {question_data}")

            # AIにユーザーの回答を判定させる
            check_prompt = f"""
            問題: {question_data}
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
            
            # デバッグ用出力
            print(f"AI Response: {explanation}")
            
            # 正解の抽出方法を修正
            correct_option = None
            explanation_text = ""
            
            for line in explanation.split('\n'):
                if line.startswith('正解:'):
                    # 括弧や空白を除去して正解を取得
                    correct_option = line.replace('正解:', '').strip().replace('(', '').replace(')', '')
                elif line.startswith('解説:'):
                    explanation_text = line.replace('解説:', '').strip()

            # デバッグ用出力
            print(f"User Answer: {user_answer}")
            print(f"Correct Option: {correct_option}")

            # 正誤を判定（大文字小文字を区別しない）
            is_correct = user_answer.upper() == correct_option.upper()
            print(f"Is Correct: {is_correct}")

            context = {
                'question': question_data,
                'keyword': keyword,
                'question_number': question_number,
                'total_questions': len(all_questions),
                'has_next': question_number < len(all_questions),
                'next_number': question_number + 1,
                'is_correct': is_correct,
                'explanation': explanation_text,
                'correct_option': correct_option,
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

            return render(request, 'answer.html', context)

        except Exception as e:
            print(f"Error: {str(e)}")  # デバッグ用
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

def profile_view(request):
    user = request.user 
    correct_count = user.correct_count
    generate_count = user.generate_count
    accuracy = round(user.accuracy, 1)  # 正答率を小数点第1位までに丸める
    # ユーザーの生成した問題を取得
    user_questions = Question.objects.filter(user=request.user)
    
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
    
    return render(request, 'profile.html', {'correct_count': correct_count, 'generate_count': generate_count, 'accuracy': accuracy, 'favorite_keyword': favorite_keyword})

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
        cleaned_questions.append({'text': cleaned_text, 'question_number': question_number, 'is_correct_first': is_correct_first, 'is_correct': is_correct})
    
    return render(request, 'keyword_questions.html', {'questions': cleaned_questions, 'keyword': keyword, 'user': request.user})

@login_required
def explanation_view(request, keyword, question_number):
    if request.method == 'POST':
        try:
            user_answer = request.POST.get('answer', '')  # 例: "A"
            is_retry = request.POST.get('retry', '')
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
            else:
                current_question = all_questions[question_number - 1]  # クエリセットから取得した場合
                question_data = current_question.question_text
                question_id = current_question.id

            # デバッグ用出力
            print(f"is_retry: {is_retry}")
            print(f"all_questions: {all_questions}")
            print(f"Question Data: {question_data}")

            # AIにユーザーの回答を判定させる
            check_prompt = f"""
            問題: {question_data}
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
            
            # デバッグ用出力
            print(f"AI Response: {explanation}")
            
            # 正解の抽出方法を修正
            correct_option = None
            explanation_text = ""
            
            for line in explanation.split('\n'):
                if line.startswith('正解:'):
                    # 括弧や空白を除去して正解を取得
                    correct_option = line.replace('正解:', '').strip().replace('(', '').replace(')', '')
                elif line.startswith('解説:'):
                    explanation_text = line.replace('解説:', '').strip()

            # デバッグ用出力
            print(f"User Answer: {user_answer}")
            print(f"Correct Option: {correct_option}")

            # 正誤を判定（大文字小文字を区別しない）
            is_correct = user_answer.upper() == correct_option.upper()
            print(f"Is Correct: {is_correct}")

            context = {
                'question': question_data,
                'keyword': keyword,
                'question_number': question_number,
                'total_questions': len(all_questions),
                'has_next': question_number < len(all_questions),
                'next_number': question_number + 1,
                'is_correct': is_correct,
                'explanation': explanation_text,
                'correct_option': correct_option,
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
            print(f"Error: {str(e)}")  # デバッグ用
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def keyword_history(request):
    user = request.user
    # テーマのリストを取得
    keywords = Question.objects.filter(user=user).values_list('theme', flat=True).distinct()
    return JsonResponse({'keywords': list(keywords)})