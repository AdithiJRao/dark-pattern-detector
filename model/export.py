import joblib, json

m = joblib.load("model/model.pkl")
tf = m.named_steps["tfidf"]
clf = m.named_steps["clf"]

data = {
    "vocab": {t: int(i) for t, i in tf.vocabulary_.items()},
    "idf": [round(float(x), 5) for x in tf.idf_],
    "coef": [round(float(x), 5) for x in clf.coef_[0]],
    "intercept": float(clf.intercept_[0]),
}

with open("extension/model.js", "w", encoding="utf-8") as f:
    f.write("const MODEL = " + json.dumps(data) + ";")

print("Terms:", len(data["vocab"]), "-> saved extension/model.js")