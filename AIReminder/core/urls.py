from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.index, name='generate'),
    path('generate_question/', views.generate_question, name='generate_question'),
    path('answer_question/', views.answer_question, name='answer_question'),
    path('question_history/', views.question_history, name='question_history'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('question/<str:keyword>/<int:question_number>/', views.question_view, name='question'),
    path('answer/<str:keyword>/<int:question_number>/', views.answer_question, name='answer_question'),
    path('profile/', views.profile_view, name='profile'),
    path('allkeyword/', views.allkeyword_view, name='allkeyword'),
    path('allquestion/', views.allquestion_view, name='allquestion'),
    path('keywords/<str:keyword>/', views.keyword_questions_view, name='keyword_questions'),
    path('explanation/<str:keyword>/<int:question_number>/', views.explanation_view, name='explanation'),
]
