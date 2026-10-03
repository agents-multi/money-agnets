"""LLM access with retries and a fallback chain: Gemini, then Groq (optional)."""
import json, os, re, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MOCKS = {
    "topics": json.dumps([
        {"title": "Best Budget Laptops for Students in 2026", "keyword": "best budget laptops students", "format": "comparison"},
        {"title": "How to Choose a Laptop Under 40000", "keyword": "laptop under 40000", "format": "how-to"},
        {"title": "Best Laptop Bags for College", "keyword": "laptop bag college", "format": "review"},
    ]),
    "write": "<h2>Intro</h2><p>" + "Useful words here. " * 120 + "</p><h2>Top pick</h2><p>We like the [[AFFILIATE: Acer Aspire]] for value. "
             + "More useful words. " * 120 + "</p><h2>Final thoughts</h2><p>" + "Closing words. " * 60 + "</p>",
    "qa": json.dumps({"score": 9, "fabricated_claims": False, "problems": []}),
}


def load_prompt(name):
    return (ROOT / "prompts" / f"{name}.txt").read_text(encoding="utf-8")


def _post(url, headers, payload, timeout=120):
    h = {"Content-Type": "application/json", "User-Agent": "money-agents/1.0", **headers}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _gemini(prompt):
    model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    d = _post(url, {"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
              {"contents": [{"parts": [{"text": prompt}]}]})
    return d["candidates"][0]["content"]["parts"][0]["text"]


def _groq(prompt):
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    d = _post("https://api.groq.com/openai/v1/chat/completions",
              {"Authorization": "Bearer " + os.environ["GROQ_API_KEY"]},
              {"model": model, "messages": [{"role": "user", "content": prompt}]})
    return d["choices"][0]["message"]["content"]


def ask(prompt, kind="write"):
    if os.environ.get("MOCK_LLM"):
        return MOCKS[kind]
    providers = []
    if os.environ.get("GEMINI_API_KEY"):
        providers.append(("gemini", _gemini))
    if os.environ.get("GROQ_API_KEY"):
        providers.append(("groq", _groq))
    if not providers:
        raise RuntimeError("No API key found. Add GEMINI_API_KEY as a GitHub secret.")
    last = None
    for name, fn in providers:
        for attempt in range(3):
            try:
                return fn(prompt)
            except Exception as e:  # rate limit, network, bad response
                last = e
                time.sleep(5 * 2 ** attempt)
    raise RuntimeError(f"All LLM providers failed: {last}")


def parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    starts = [i for i in (text.find("["), text.find("{")) if i != -1]
    if not starts:
        raise ValueError("No JSON found in model output")
    s = min(starts)
    end = max(text.rfind("]"), text.rfind("}"))
    return json.loads(text[s:end + 1])


def strip_fences(text):
    return re.sub(r"^```(?:html)?\s*|\s*```$", "", text.strip())
