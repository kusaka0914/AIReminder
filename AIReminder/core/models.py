from django.db import models
from django.conf import settings
# Create your models here.
from django.contrib.auth.models import AbstractUser

class Question(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")
    theme = models.CharField(max_length=255)
    question_text = models.TextField()
    correct_option = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(null=True,blank=True)
    explanation = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.question_text

class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField()
    review_date = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.question.question_text}"
    
class CustomUser(AbstractUser):
    is_premium = models.BooleanField(default=False)
    def __str__(self):
        return self.username
