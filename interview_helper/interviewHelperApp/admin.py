from django.contrib import admin
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from .models import Question, Rating, Company, Tag, CommunityQuestion, QuestionVote
=======
from .models import QuestionBank, Question, Rating, Company, Tag, CommunityQuestion, QuestionVote
>>>>>>> Stashed changes
=======
from .models import QuestionBank, Question, Rating, Company, Tag, CommunityQuestion, QuestionVote
>>>>>>> Stashed changes
=======
from .models import QuestionBank, Question, Rating, Company, Tag, CommunityQuestion, QuestionVote
>>>>>>> Stashed changes
=======
from .models import QuestionBank, Question, Rating, Company, Tag, CommunityQuestion, QuestionVote
>>>>>>> Stashed changes

# Register your models here.
admin.site.register(Question)
admin.site.register(Rating)

# Community Question Bank
admin.site.register(Company)
admin.site.register(Tag)
admin.site.register(CommunityQuestion)
admin.site.register(QuestionVote)