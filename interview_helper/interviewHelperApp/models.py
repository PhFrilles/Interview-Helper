from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

# Create your models here.
class QuestionBank(models.Model):
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="question_banks"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company} - {self.role}"
    
class Question(models.Model):
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    text = models.TextField()

    def __str__(self):
        return self.text[:50] + "..."
    
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question_bank = models.ForeignKey(
        QuestionBank,
        on_delete=models.CASCADE,
        related_name="ratings"
    )
    score = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "question_bank")

    def __str__(self):
        return f"{self.user} - {self.score}"