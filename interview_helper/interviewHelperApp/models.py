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


# ===== COMMUNITY QUESTION BANK =====

class Company(models.Model):
    """Companies for tagging community questions"""
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Topics for community questions (DSA, OOP, System Design, etc.)"""
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CommunityQuestion(models.Model):
    """Interview questions submitted by community"""
    QUESTION_TYPES = [
        ('general', 'General Interview'),
        ('technical', 'Technical Question'),
        ('behavioral', 'Behavioral Question'),
    ]
    
    text = models.TextField(help_text="The interview question")
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='general')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_questions')
    
    # Tagging
    companies = models.ManyToManyField(Company, blank=True, related_name='questions')
    tags = models.ManyToManyField(Tag, blank=True, related_name='questions')
    
    # Voting
    vote_count = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-vote_count', '-created_at']
    
    def __str__(self):
        return f"{self.text[:60]}..."
    
    def update_vote_count(self):
        """Update cached vote count"""
        self.vote_count = self.votes.filter(vote_type='up').count() - self.votes.filter(vote_type='down').count()
        self.save(update_fields=['vote_count'])


class QuestionVote(models.Model):
    """User votes on community questions"""
    VOTE_TYPES = [
        ('up', 'Upvote'),
        ('down', 'Downvote'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_votes')
    question = models.ForeignKey(CommunityQuestion, on_delete=models.CASCADE, related_name='votes')
    vote_type = models.CharField(max_length=4, choices=VOTE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'question')
    
    def __str__(self):
        return f"{self.user.username} - {self.vote_type} - {self.question.text[:30]}"