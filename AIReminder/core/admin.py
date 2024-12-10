from django.contrib import admin

# Register your models here.
from .models import Question, UserProgress, CustomUser

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('theme', 'question_text', 'correct_option', 'created_at')
    search_fields = ('theme', 'question_text')

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'is_correct', 'review_date')

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_premium')
    search_fields = ('email',)
