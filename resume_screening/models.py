from django.db import models
import json

class Resume(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    education = models.TextField(null=True, blank=True)
    experience = models.IntegerField(null=True, blank=True)
    skills = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='resumes/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ranking_score = models.FloatField(null=True, blank=True)
    recommended_roles = models.CharField(max_length=200, null=True, blank=True)
    sentiment = models.CharField(max_length=20, default="Neutral")

    # ✅ Change missing_skills to JSONField for better storage
    missing_skills = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name
