from django.urls import path
from . import views
from django.shortcuts import render

urlpatterns = [
    path("", views.upload_resume, name="upload_resume"),
    path("result/<int:resume_id>/", views.resume_result, name="resume_result"),
    path("login/", views.user_login, name="user_login"),
    path("signup/", views.user_signup, name="user_signup"),
    path("logout/", views.user_logout, name="user_logout"),
    path("ranking_chart/", views.ranking_chart, name="ranking_chart"),
    path("ranking/", views.ranking_chart, name="ranking_page"),

    # ✅ Analytics API Route
    path("analytics_dashboard/", views.analytics_dashboard, name="analytics_dashboard"),

    # ✅ Analytics Page Route
    path("dashboard/", lambda request: render(request, "analytics.html"), name="dashboard"),
]
