from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.index, name='generate'),
    path('generate_question/', views.generate_question, name='generate_question'),
    path('answer_question/', views.answer_question, name='answer_question'),
    path('question_history/', views.question_history, name='question_history'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('question/<int:question_number>/', views.question_view, name='question'),
    path('answer/<int:question_number>/', views.answer_question, name='answer_question'),
    path('profile/', views.profile_view, name='profile'),
]
