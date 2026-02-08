from django.contrib import admin
from .models import Question, Rating, Company, Tag, CommunityQuestion, QuestionVote

# Register your models here.
admin.site.register(Question)
admin.site.register(Rating)

# Community Question Bank
admin.site.register(Company)
admin.site.register(Tag)
admin.site.register(CommunityQuestion)
admin.site.register(QuestionVote)