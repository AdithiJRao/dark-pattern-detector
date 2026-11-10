import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# 1. Load
try:
    df = pd.read_csv("model/data.csv")
except UnicodeDecodeError:
    df = pd.read_csv("model/data.csv", encoding="latin-1")

print("Columns:", df.columns.tolist())
print("Raw shape:", df.shape)
print("\nCategory counts:")
print(df["Category"].value_counts())

# 2. Clean
df = df.dropna(subset=["Title", "Category"])
df["Title"] = df["Title"].astype(str).str.strip()
df = df.drop_duplicates(subset="Title")
print("\nShape after cleaning:", df.shape)

# 3. Binary label: 1 = dark pattern, 0 = not
df["label"] = (df["Category"].str.strip().str.lower() != "not dark pattern").astype(int)
print("\nBinary label counts:")
print(df["label"].value_counts())

# 4. Split
X_train, X_test, y_train, y_test = train_test_split(
    df["Title"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

# 5. Pipeline: TF-IDF + Logistic Regression
model = Pipeline([
    ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=2)),
    ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
])
model.fit(X_train, y_train)

# 6. Evaluate
print("\n", classification_report(y_test, model.predict(X_test),
      target_names=["Not Dark Pattern", "Dark Pattern"]))

# 7. Quick sanity test
tests = [
    "Only 2 items left in stock!",
    "Hurry, offer ends in 10 minutes",
    "15 people are viewing this right now",
    "Free shipping on orders over $50",
    "Add to cart",
]
for t, p in zip(tests, model.predict_proba(tests)[:, 1]):
    print(f"{p:.2f}  {t}")

# 8. Save
joblib.dump(model, "model/model.pkl")
print("\nSaved model/model.pkl")