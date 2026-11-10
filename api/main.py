import os
import secrets
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import List

import joblib
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "model.pkl"
model = joblib.load(MODEL_PATH)

THRESHOLD = 0.8  # raise to reduce false positives

app = FastAPI(title="Dark Pattern Detector")

# CHANGE 1: only your site and local testing can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://adithijrao.github.io",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------- Prediction ----------

class PredictRequest(BaseModel):
    texts: List[str]


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/predict")
def predict(req: PredictRequest):
    texts = req.texts[:200]  # cap batch size
    if not texts:
        return {"results": []}
    probs = model.predict_proba(texts)[:, 1]
    return {
        "results": [
            {"text": t, "score": round(float(p), 3), "is_dark": bool(p >= THRESHOLD)}
            for t, p in zip(texts, probs)
        ]
    }


# ---------- User reports ----------

DB_PATH = Path(__file__).resolve().parent / "reports.db"
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "")  # set a real password before deploying
KINDS = {"missed": "Reported Dark Pattern", "false_alarm": "Not Dark Pattern"}

security = HTTPBasic()
hits = defaultdict(list)


def db():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS reports "
        "(id INTEGER PRIMARY KEY, text TEXT, category TEXT, created REAL)"
    )
    return con


class Report(BaseModel):
    text: str
    kind: str


@app.post("/report")
def report(r: Report, request: Request):
    ip = request.client.host
    now = time.time()
    hits[ip] = [t for t in hits[ip] if now - t < 3600]
    if len(hits[ip]) >= 20:
        raise HTTPException(429, "Too many reports. Try again later.")
    text = " ".join(r.text.split())
    if not 10 <= len(text) <= 150 or r.kind not in KINDS:
        raise HTTPException(400, "Text must be 10-150 characters and kind must be valid.")
    hits[ip].append(now)
    con = db()
    con.execute(
        "INSERT INTO reports (text, category, created) VALUES (?, ?, ?)",
        (text, KINDS[r.kind], now),
    )
    con.commit()
    con.close()
    return {"ok": True}


# CHANGE 2: powers the live counter on the website
@app.get("/stats")
def stats():
    con = db()
    n = con.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    con.close()
    return {"reports": n}


def admin_only(c: HTTPBasicCredentials = Depends(security)):
    ok = (
        ADMIN_PASS
        and secrets.compare_digest(c.password, ADMIN_PASS)
        and secrets.compare_digest(c.username, ADMIN_USER)
    )
    if not ok:
        raise HTTPException(401, "Unauthorized", headers={"WWW-Authenticate": "Basic"})


@app.get("/admin/export.csv", response_class=PlainTextResponse)
def export(_: None = Depends(admin_only)):
    con = db()
    rows = con.execute("SELECT text, category FROM reports ORDER BY id").fetchall()
    con.close()
    lines = ["Title,Category"] + ['"%s",%s' % (t.replace('"', '""'), c) for t, c in rows]
    return "\n".join(lines)