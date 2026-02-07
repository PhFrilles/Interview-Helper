from django.contrib import admin
from .models import QuestionBank, Question, Rating

# Register your models here.
admin.site.register(QuestionBank)
admin.site.register(Question)
admin.site.register(Rating)