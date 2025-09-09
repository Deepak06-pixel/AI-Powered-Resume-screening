import spacy

# Load spaCy English NLP model
nlp = spacy.load("en_core_web_sm")

# Sample skill set (You can expand this list)
SKILL_KEYWORDS = {"python", "java", "machine learning", "data science", "django", "flask", "tensorflow", "pytorch", 
                  "sql", "nlp", "deep learning", "react", "javascript", "html", "css", "cloud computing", "aws"}

def extract_skills(text):
    """Extract skills from resume text using keyword matching."""
    extracted_skills = set()
    doc = nlp(text.lower())  # Convert text to lowercase and process with spaCy
    
    for token in doc:
        if token.text in SKILL_KEYWORDS:
            extracted_skills.add(token.text)

    return list(extracted_skills)
