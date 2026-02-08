from django.db import models
from datetime import datetime
from django.contrib.auth.models import User

# Create your models here.
class Question(models.Model):
    company = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    text = models.TextField()
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company} - {self.role}" 
    
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="ratings"
    )
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "question")

    def __str__(self):
        return f"{self.user} - {self.score}"