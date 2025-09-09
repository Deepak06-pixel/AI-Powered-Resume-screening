import os
import pickle
import io
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Resume
from .parser import extract_text_from_pdf, extract_features, analyze_sentiment,analyze_skills_gap
from collections import Counter

# ✅ Load trained ML model
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "resume_ranking_model.pkl")

try:
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    print("✅ Model Loaded Successfully!")
except FileNotFoundError:
    print("❌ Model file not found. Train the model first by running m1_model.py.")
    model = None

def analytics_dashboard(request):
    resumes = Resume.objects.all().order_by("-ranking_score")[:10]  # Get top 10 ranked resumes

    # Extract data for charts
    all_skills = []
    ranking_scores = []
    candidate_names = []
    education_levels = []
    sentiments = {"Positive": 0, "Neutral": 0, "Negative": 0}

    for resume in resumes:
        ranking_scores.append(resume.ranking_score)
        candidate_names.append(resume.name)
        education_levels.append(resume.education)
        all_skills.extend(resume.skills.split(", "))
        sentiments[resume.sentiment] += 1

    # Count most common skills
    skill_counts = Counter(all_skills).most_common(10)
    skills, skill_freqs = zip(*skill_counts) if skill_counts else ([], [])

    # Count education levels
    education_counts = Counter(education_levels)

    return JsonResponse({
        "skills": list(skills),
        "skill_freqs": list(skill_freqs),
        "ranking_scores": ranking_scores,
        "candidate_names": candidate_names,
        "education_levels": list(education_counts.keys()),
        "education_counts": list(education_counts.values()),
        "sentiments": sentiments,
    })


def upload_resume(request):
    if request.method == "POST" and request.FILES.get("resume"):
        resume_file = request.FILES["resume"]
        pdf_bytes = resume_file.read()
        resume_text = extract_text_from_pdf(io.BytesIO(pdf_bytes))

        features = extract_features(resume_text)

        # Extracted Features
        candidate_name = features.get("name", "Unknown").split("-")[-1].strip()
        candidate_email = features.get("email", "Not Provided")
        candidate_phone = features.get("phone", "Not Provided")
        candidate_experience = float(features.get("experience", 0))

        edu_mapping = {"Diploma": 0, "Bachelors": 1, "Masters": 2, "PhD": 3}
        education_level = edu_mapping.get(features.get("education", "Bachelors"), 1)

        skills_list = features["skills"].split(",") if features["skills"] else []
        skills_count = len(skills_list)

        # Recommend Job Roles and Missing Skills
        recommended_roles, missing_skills = recommend_job_roles(skills_list, candidate_experience)

        # Prepare Input for Model
        input_data = pd.DataFrame([[education_level, candidate_experience, skills_count]],
                                  columns=["education", "experience", "skills"])

        ranking_score = model.predict(input_data)[0] if model else 0

        sentiment = analyze_sentiment(resume_text)

        # ✅ Check if the resume already exists
        existing_resume = Resume.objects.filter(email=candidate_email, phone=candidate_phone).first()

        if existing_resume:
            # ✅ If resume exists, update it instead of creating a duplicate
            existing_resume.ranking_score = ranking_score
            existing_resume.sentiment = sentiment
            existing_resume.recommended_roles = ", ".join(recommended_roles)
            existing_resume.missing_skills = json.dumps(missing_skills)
            existing_resume.save()
            return redirect("resume_result", resume_id=existing_resume.id)
        else:
            # ✅ If a new resume, check the limit of stored resumes
            max_resumes = 10
            if Resume.objects.count() >= max_resumes:
                oldest_resume = Resume.objects.order_by("uploaded_at").first()
                if oldest_resume:
                    oldest_resume.delete()

            # ✅ Save the new resume
            resume = Resume(
                name=candidate_name,
                email=candidate_email,
                phone=candidate_phone,
                education=features["education"],
                experience=candidate_experience,
                skills=", ".join(skills_list),
                ranking_score=ranking_score,
                sentiment=sentiment,
                recommended_roles=", ".join(recommended_roles),
                missing_skills=json.dumps(missing_skills)  # Store missing skills as JSON
            )
            resume.save()

        return redirect("resume_result", resume_id=resume.id)

    return render(request, "resume_screening/upload.html")



def resume_result(request, resume_id):
    try:
        resume = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        messages.error(request, "Resume not found!")
        return redirect("upload_resume")

    recommended_roles = resume.recommended_roles.split(", ") if resume.recommended_roles else []
    sentiment = resume.sentiment

    # ✅ Load missing skills from the database
    stored_missing_skills = json.loads(resume.missing_skills) if resume.missing_skills else {}

    # ✅ Debug: Print missing skills from DB
    print("Missing Skills from DB:", stored_missing_skills)

    # ✅ Analyze skills gap
    job_description = "Job description here"
    new_missing_skills = analyze_skills_gap(resume.skills, job_description)

    # ✅ Debug: Print missing skills after analysis
    print("Missing Skills after analyze_skills_gap:", new_missing_skills)

    # ✅ Merge missing skills
    merged_missing_skills = stored_missing_skills.copy()
    for role, skills in new_missing_skills.items():
        if role in merged_missing_skills:
            merged_missing_skills[role] = list(set(merged_missing_skills[role] + skills))  # Remove duplicates
        else:
            merged_missing_skills[role] = skills

    # ✅ Remove skills that the candidate already has
    candidate_skills = set(map(str.strip, resume.skills.split(",")))  # Convert to set for easy checking
    for role in merged_missing_skills:
        merged_missing_skills[role] = [skill for skill in merged_missing_skills[role] if skill.strip().lower() not in candidate_skills]

    # ✅ Only keep missing skills for recommended roles
    filtered_missing_skills = {
        role: skills for role, skills in merged_missing_skills.items() if role in recommended_roles
    }

    # ✅ Debug: Print final missing skills
    print("Final Missing Skills Sent to Template:", filtered_missing_skills)

    return render(request, "resume_screening/result.html", {
        "resume": resume,
        "recommended_roles": recommended_roles,
        "sentiment": sentiment,
        "missing_skills": filtered_missing_skills  # ✅ Pass only relevant missing skills
    })

def ranking_chart(request):
    # ✅ Get the top 9 resumes by ranking_score, excluding unwanted names
    top_resumes = list(
        Resume.objects.exclude(name__in=["Unknown", "Candidate", "Not Provided", ""])
        .order_by("-ranking_score")[:10]
    )

    # ✅ Get the latest uploaded resume
    latest_resume = Resume.objects.latest("uploaded_at")

    # ✅ Ensure latest resume is included
    if latest_resume not in top_resumes:
        top_resumes.append(latest_resume)

    # ✅ Keep only the top 10 resumes
    top_resumes = sorted(top_resumes, key=lambda r: r.ranking_score, reverse=True)[:10]

    # ✅ Ensure all candidates have proper names
    candidates = [
        resume.name.strip() if resume.name and resume.name.strip() else f"Candidate {i + 1}"
        for i, resume in enumerate(top_resumes)
    ]

    scores = [resume.ranking_score for resume in top_resumes]

    return JsonResponse({"candidates": candidates, "scores": scores})


def recommend_job_roles(skills, experience):
    job_roles = {
        "Software Engineer": ["Python", "Java", "C++", "Software Development"],
        "Data Scientist": ["Python", "Data Analysis", "Machine Learning", "Statistics"],
        "Web Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js"],
        "Data Analyst": ["Excel", "SQL", "Data Visualization", "Python"],
        "Product Manager": ["Agile", "Project Management", "Team Leadership"],
        "UX Designer": ["Design", "UX/UI", "Prototyping", "Figma"]
    }

    if not skills:  # Ensure we handle the case where no skills are found
        return ["No skills found. Try adding skills to your resume."], {}

    skills = [skill.lower() for skill in skills if isinstance(skill, str)]
    recommended_roles = []
    missing_skills = {}

    for role, required_skills in job_roles.items():
        required_skills_lower = [skill.lower() for skill in required_skills]

        # Find matched skills
        matched_skills = [skill for skill in skills if skill in required_skills_lower]

        if matched_skills and experience >= 0:
            recommended_roles.append(role)

            # Ensure we add missing skills even if there are matches
            missing = [skill for skill in required_skills_lower if skill not in skills]

            if missing:  # Only add if some skills are missing
                missing_skills[role] = missing

    return recommended_roles, missing_skills



# ✅ User Authentication (Login, Signup, Logout)
def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("upload_resume")
        else:
            messages.error(request, "Invalid Credentials")
    return render(request, "resume_screening/login.html")


def user_signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        user = User.objects.create_user(username, email, password)
        user.save()
        messages.success(request, "Account Created Successfully! Please Log In.")
        return redirect("user_login")
    return render(request, "resume_screening/signup.html")


def user_logout(request):
    logout(request)
    return redirect("user_login")



