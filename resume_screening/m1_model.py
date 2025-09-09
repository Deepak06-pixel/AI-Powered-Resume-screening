import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import pickle

# Load dataset
df = pd.read_csv("D:/resume_screening_system/resume_ranking_dataset.csv")

# Train-test split
X = df[["education", "experience", "skills"]]
y = df["ranking_score"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Random Forest Model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save model to a file
with open("resume_ranking_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model trained and saved successfully!")