from django.contrib import admin
from .models import Resume

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'ranking_score', 'sentiment', 'uploaded_at')
    search_fields = ('name', 'email', 'skills')
    list_filter = ('sentiment', 'education')

admin.site.site_header = "Resume Screening Admin"
admin.site.site_title = "Resume Screening Admin Portal"
admin.site.index_title = "Welcome to the Resume Screening System"
