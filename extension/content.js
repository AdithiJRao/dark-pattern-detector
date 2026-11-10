const SELECTOR = "p,span,h1,h2,h3,h4,h5,h6,li,label,button,a,div";
const MIN_LEN = 10;
const MAX_LEN = 150;
const THRESHOLD = 0.8;

const REGEX = /only \d+ (items? |rooms? )?left|hurry|selling fast|\d+ (people|others|customers) (are )?(viewing|looking|watching)|limited time|offer ends|almost gone|last chance|act now/i;

// Same math as scikit-learn: TF-IDF (1-2 grams) -> L2 normalise -> logistic regression
function score(text) {
  const toks = text.toLowerCase().match(/\b\w\w+\b/g) || [];
  const terms = [...toks];
  for (let i = 0; i < toks.length - 1; i++) terms.push(toks[i] + " " + toks[i + 1]);

  const counts = {};
  for (const t of terms) {
    const idx = MODEL.vocab[t];
    if (idx !== undefined) counts[idx] = (counts[idx] || 0) + 1;
  }
  let dot = 0, norm = 0;
  for (const idx in counts) {
    const v = counts[idx] * MODEL.idf[idx];
    dot += v * MODEL.coef[idx];
    norm += v * v;
  }
  const z = (norm > 0 ? dot / Math.sqrt(norm) : 0) + MODEL.intercept;
  return 1 / (1 + Math.exp(-z));
}

function flag(el, s) {
  el.dataset.dpFlag = "1";
  el.style.outline = "3px solid red";
  el.style.outlineOffset = "2px";
  el.title = "Possible dark pattern" + (s ? " (score " + s.toFixed(2) + ")" : "");
}

function scan() {
  document.querySelectorAll(SELECTOR).forEach((el) => {
    if (el.dataset.dpChecked) return;
    // NEW: never read text the user is typing
    if (el.isContentEditable || el.closest("textarea,input,[contenteditable='true']")) return;
    if (el.childElementCount !== 0) return;
    if (el.getClientRects().length === 0) return;
    const text = (el.innerText || "").trim().replace(/\s+/g, " ");
    if (text.length < MIN_LEN || text.length > MAX_LEN) return;
    el.dataset.dpChecked = "1";
    const s = score(text);
    if (s >= THRESHOLD) flag(el, s);
    else if (REGEX.test(text)) flag(el);
  });
  chrome.runtime.sendMessage({
    type: "COUNT",
    count: document.querySelectorAll("[data-dp-flag]").length,
  });
}

setTimeout(scan, 1500);
let timer;
new MutationObserver(() => {
  clearTimeout(timer);
  timer = setTimeout(scan, 1500);
}).observe(document.body, { childList: true, subtree: true });