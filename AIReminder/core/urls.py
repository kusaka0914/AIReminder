from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.index, name='index'),
    path('generate_question/', views.generate_question, name='generate_question'),
    path('answer_question/', views.answer_question, name='answer_question'),
    path('question_history/', views.question_history, name='question_history'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
]
