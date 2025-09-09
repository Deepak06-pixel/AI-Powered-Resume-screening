import re
import spacy
from pdfminer.high_level import extract_text
from textblob import TextBlob

# Load NLP model
nlp = spacy.load("en_core_web_sm")

PHONE_REGEX = re.compile(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{4,5}[-.\s]?\d{5}')

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    """
    try:
        return extract_text(pdf_path)
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def extract_features(resume_text):
    """
    Extracts key features from the resume, including candidate name, email, phone, education, experience, and skills.
    """
    doc = nlp(resume_text)  # Process text with NLP model
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]

    candidate_name = "Unknown"

    #  Check the first few lines for a valid name
    for i in range(min(5, len(lines))):  # Only check top 5 lines
        cleaned_line = lines[i].strip()

        if (
                cleaned_line and  # Not empty
                not re.match(r"^\+?\d{10,}$", cleaned_line) and  # Not a phone number
                len(cleaned_line.split()) <= 4 and  # Name is usually 1-4 words
                not any(char in cleaned_line for char in "!@#$%^&*(){}[]<>?/|\\") and  # Avoid symbols
                "PROFILE" not in cleaned_line.upper() and  # Avoid section headers
                "EMAIL" not in cleaned_line.upper() and  # Avoid labels
                "PHONE" not in cleaned_line.upper() and
                not cleaned_line.isdigit()  # Ensure it is not just a number
        ):
            candidate_name = cleaned_line
            break

    # Fallback to NLP-based name detection if needed
    if candidate_name == "Unknown":
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                candidate_name = ent.text
                break

    # **Extract Email**
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", resume_text)
    candidate_email = email_match.group() if email_match else "Not Provided"

    # **Extract Phone Number**
    phone_match = PHONE_REGEX.search(resume_text)
    candidate_phone = phone_match.group() if phone_match else "Not Provided"

    # **Extract Education**
    education_keywords = ["Diploma", "Engineering", "Bachelors", "Masters", "PhD", "B.Sc", "BEng", "M.Sc"]
    candidate_education = next((word for word in education_keywords if word.lower() in resume_text.lower()), "Unknown")

    # **Extract Experience**
    experience_match = re.search(r"(\d+)\s+(years|yrs|year)", resume_text, re.I)
    candidate_experience = int(experience_match.group(1)) if experience_match else 0

    # **Extract Skills** (Using NLP)
    predefined_skills = [
        # Information Technology (IT) & Software Development
        "Python", "Java", "C", "C++", "C#", "Ruby", "Swift", "Kotlin", "Go", "Rust",
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Angular", "Vue.js", "Node.js",
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "Firebase", "Redis", "Oracle",
        "AWS", "Azure", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Jenkins",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "NLP", "Computer Vision",
        "Ethical Hacking", "Cybersecurity", "Network Security", "SIEM",

        # Data Science & Business Intelligence
        "Data Analysis", "Data Visualization", "Power BI", "Tableau", "Excel",
        "Big Data", "Hadoop", "Apache Spark", "Google Analytics",
        "Business Intelligence", "Market Research", "Data Mining",

        # Finance & Accounting
        "Financial Modeling", "Investment Analysis", "Risk Management",
        "Taxation", "Auditing", "Budgeting", "Forecasting",
        "QuickBooks", "SAP", "Tally", "Xero", "Oracle Financials",

        # Office Productivity & Microsoft Tools
        "MS Word", "MS Excel", "MS PowerPoint", "MS Outlook", "MS Teams",
        "Google Docs", "Google Sheets", "Google Slides",
        "Microsoft Office", "Google Workspace",

        # Healthcare & Medical
        "Medical Coding", "Patient Care", "Pharmacology", "Nursing",
        "Electronic Medical Records (EMR)", "Medical Billing", "Health Informatics",
        "Public Health", "Epidemiology", "Radiology",

        # Sales & Marketing
        "Digital Marketing", "SEO", "SEM", "PPC", "Social Media Marketing",
        "Content Marketing", "Email Marketing",
        "CRM", "Salesforce", "HubSpot", "Lead Generation", "Market Research",

        # Human Resources (HR) & Recruiting
        "Talent Acquisition", "Employee Relations", "HR Analytics",
        "Payroll Management", "Compensation & Benefits", "Labor Laws",
        "LinkedIn Recruiting", "Applicant Tracking System (ATS)",

        # Manufacturing & Supply Chain
        "Inventory Management", "Logistics", "Procurement", "Vendor Management",
        "Lean Manufacturing", "Six Sigma", "Quality Assurance (QA)",
        "SAP ERP", "Supply Chain Analytics",

        # Education & Training
        "Curriculum Development", "Instructional Design", "e-Learning",
        "Learning Management System (LMS)", "Online Teaching", "Public Speaking",
        "Academic Research", "Student Engagement",

        # Legal & Compliance
        "Corporate Law", "Intellectual Property (IP)", "Legal Research",
        "Contract Drafting", "Litigation", "Compliance & Risk Management",
        "Regulatory Affairs", "Government Relations",

        # Design & Creative Fields
        "Graphic Design", "UI/UX", "Adobe Photoshop", "Illustrator", "Figma",
        "3D Modeling", "Motion Graphics", "Animation", "Video Editing",
        "Interior Design", "Fashion Design", "CAD Software"
    ]
    extracted_skills = set()  # Use a set to remove duplicates

    for token in doc:
        if token.text.lower() in [skill.lower() for skill in predefined_skills]:
            extracted_skills.add(token.text.lower())  # Store in lowercase to avoid case mismatches

    candidate_skills = ", ".join(sorted(extracted_skills)) if extracted_skills else "None"

    return {
        "name": candidate_name,
        "email": candidate_email,
        "phone": candidate_phone,
        "education": candidate_education,
        "experience": candidate_experience,
        "skills": candidate_skills
    }
def analyze_sentiment(text):
    """
    Analyzes the sentiment of the text and returns a sentiment label.
    """
    blob = TextBlob(text)
    sentiment_score = blob.sentiment.polarity  # Returns a score between -1 and 1

    if sentiment_score > 0:
        return "Positive"
    elif sentiment_score == 0:
        return "Neutral"
    else:
        return "Negative"


def analyze_skills_gap(candidate_skills, job_description):
    # Debugging: Print input
    print("Candidate Skills:", candidate_skills)
    print("Job Description:", job_description)

    # Simulate missing skills calculation (replace this with actual logic)
    job_required_skills = {"Web Developer": ["css", "javascript", "react", "node.js"]}

    missing_skills = {}
    for role, skills in job_required_skills.items():
        missing = [skill for skill in skills if skill.lower() not in candidate_skills.lower()]
        missing_skills[role] = missing

    # Debugging: Print output
    print("Missing Skills Calculated:", missing_skills)

    return missing_skills  # Ensure this returns a dictionary

