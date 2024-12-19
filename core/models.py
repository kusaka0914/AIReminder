from django.db import models
from django.conf import settings
# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User

class Question(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")
    theme = models.CharField(max_length=255)
    question_text = models.TextField()
    correct_option = models.CharField(max_length=255,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(null=True,blank=True)
    is_correct_first = models.BooleanField(default=None,null=True,blank=True)
    explanation = models.TextField(null=True,blank=True)
    question_number = models.IntegerField(default=1,null=True,blank=True)
    difficulty = models.CharField(max_length=255,null=True,blank=True)

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
    correct_count = models.IntegerField(default=0,null=True,blank=True)
    generate_count = models.IntegerField(default=0,null=True,blank=True)
    accuracy = models.FloatField(default=0,null=True,blank=True)
    not_answered_count = models.IntegerField(default=0,null=True,blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    last_generated_date = models.DateField(null=True, blank=True)
    daily_generated_count = models.IntegerField(default=0)
    def __str__(self):
        return self.username
    
class QuestionSet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="question_sets")
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    questions = models.ManyToManyField(Question, related_name="question_sets")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

    
class Subscription(models.Model):
    PLAN_CHOICES = [
        ('basic', 'ベーシックプラン'),
        ('premium', 'プレミアムプラン'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    plan = models.CharField(max_length=50, choices=PLAN_CHOICES)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"