# Dark Pattern Detector

A browser extension that reads the text on shopping pages and puts a red outline around wording designed to pressure you, such as "Only 2 left!" or "15 people are viewing this right now."

The classifier is trained in Python with scikit-learn, then exported to JSON and re-implemented in JavaScript, so it runs **entirely inside the browser**. There is no server, no API key, and no page text leaves your computer.

**Live page and download:** https://adithijrao.github.io/dark-pattern-detector/

## What it does

- Scans visible text on any page after it loads, and again when the page adds new content.
- Scores each short text block with a TF-IDF + logistic regression model.
- Draws a red outline around text scoring 0.8 or higher, with the score in a tooltip.
- Shows the number of flagged items on the extension icon.
- Falls back to a small regex list (for example "only N left", "hurry") for very common phrases.

## How it works

```
 TRAINING (once, in Python)                     RUNNING (every page, in the browser)
 --------------------------                     ------------------------------------
 Kaggle dataset (~3,000 phrases)                content.js collects visible text
        |                                              |
 train.py: TF-IDF + Logistic Regression         score(): TF-IDF -> L2 norm -> sigmoid
        |                                              |
 export.py: vocabulary, IDF weights,            red outline if score >= 0.8
 coefficients, intercept -> model.js            badge count via background.js
```

1. `model/train.py` trains a scikit-learn pipeline (TF-IDF with unigrams and bigrams, then logistic regression) and saves `model.pkl`.
2. `model/export.py` writes the learned vocabulary, IDF weights, coefficients and intercept to `extension/model.js`.
3. `extension/content.js` reproduces the same math in JavaScript: tokenise, build unigrams and bigrams, weight by IDF, L2-normalise, apply the coefficients, then the sigmoid.

An earlier version called a FastAPI server on localhost. That version is still in `api/main.py` and is useful for testing the model over HTTP, but the extension no longer needs it.

## Results

Evaluated on a stratified 20% hold-out split (`random_state=42`) after removing duplicate texts.

| Class | Precision | Recall | F1 |
|---|---|---|---|
| Not Dark Pattern | XX | XX | XX |
| Dark Pattern | XX | XX | XX |

> Replace the XX values with the table printed by `python model/train.py`.

The hold-out set comes from the same dataset as the training data, so these numbers say how well the model fits that data's style. Real pages are noisier, and the extension will produce some false positives and misses.

## Tech stack

| Area | Tools |
|---|---|
| Machine learning | Python, pandas, scikit-learn (TF-IDF, logistic regression), joblib |
| Extension | JavaScript, Chrome Extension Manifest V3 (content script, service worker) |
| Optional API | FastAPI, uvicorn, pydantic, SQLite |
| Website | HTML, CSS, GitHub Pages |
| Tooling | Git, GitHub, VS Code, Pillow (icon generation) |

## Install the extension

Works in Chrome, Edge and Brave on a laptop or desktop.

1. Download `dark-pattern-extension.zip` from the (https://adithijrao.github.io/dark-pattern-detector/) or from the `docs/` folder.
2. Extract it to a folder you will keep. Deleting the folder removes the extension.
3. Open `chrome://extensions` (or `edge://extensions`) and turn on **Developer mode**.
4. Click **Load unpacked** and select the extracted folder, the one containing `manifest.json`.
5. Open a shopping site. Flagged text gets a red outline.

It is loaded manually because Chrome allows one-click installs only from its Web Store, which charges a developer fee.

## Run the project from source

```bat
git clone https://github.com/AdithiJRao/dark-pattern-detector.git
cd dark-pattern-detector
python -m venv venv
venv\Scripts\activate
pip install pandas scikit-learn joblib fastapi uvicorn python-multipart pillow
```

Train and export the model:

```bat
python model/train.py
python model/export.py
```

Optional: run the API and try it at http://127.0.0.1:8000/docs

```bat
uvicorn api.main:app --reload
```

## Project structure

```
dark-pattern-detector/
├── model/
│   ├── data.csv              training data (Kaggle, MIT licensed)
│   ├── DATASET_LICENSE.txt   dataset license and credit
│   ├── train.py              trains and evaluates the classifier
│   ├── export.py             exports the model to extension/model.js
│   └── model.pkl             trained scikit-learn pipeline
├── extension/                the browser extension (this folder is what gets zipped)
│   ├── manifest.json
│   ├── content.js            scans the page and scores text
│   ├── background.js         updates the badge count
│   ├── model.js              exported model weights
│   └── icon48.png, icon128.png
├── api/main.py               optional FastAPI server (/predict, /report, /stats)
├── docs/                     website served by GitHub Pages
│   ├── index.html, style.css, privacy.html
│   └── dark-pattern-extension.zip
└── make_icon.py              generates the extension icons
```

## Limitations

- **Wording only.** It cannot detect hidden fees, pre-ticked boxes, trick buttons or confusing checkout flows, because those are layout problems, not text.
- **Binary output.** It says "dark pattern" or "not", not which type. The dataset categories were merged for training.
- **Small, English-only dataset.** New phrasings and other languages will be missed.
- **False positives.** A red outline means "look twice", not proof. The 0.8 threshold trades recall for precision.
- **Evaluated on data like the training data.** It has been tried on a few real sites but not benchmarked at scale.
- **Manual install on Chrome.** An unpacked extension does not update automatically.

## Privacy

The extension reads visible page text to score it. Scoring happens locally. It does not send, store or share page content, and it skips editable fields such as text boxes. See [privacy.html](docs/privacy.html).

## Future work

- Detect pre-checked boxes and hidden fees by analysing the DOM, not just text.
- Multi-class detection (scarcity, urgency, social proof, and others).
- Compare against a fine-tuned DistilBERT model for accuracy, size and speed.
- A "report this phrase" flow with human review, used to grow the dataset and retrain.
- A popup with an on/off switch and a per-page summary.
- Store listings (Edge Add-ons, Chrome Web Store) for one-click install and automatic updates.

## Dataset and credits

Trained on a dark pattern text dataset from Kaggle (`dp_final_dataset_april_3k.csv`), released under the MIT License. See `model/DATASET_LICENSE.txt`.


