import re
from .llm import ask, parse_json, load_prompt


def run(cfg, topic, html):
    text = re.sub(r"<[^>]+>", " ", html)
    words = len(text.split())
    problems = []
    if words < cfg["min_words"]:
        problems.append(f"Too short: {words} words, need at least {cfg['min_words']}.")
    if len(re.findall(r"<h2", html)) < 2:
        problems.append("Needs at least 2 <h2> sections.")
    if problems:
        return False, 0, problems
    p = (load_prompt("qa")
         .replace("{title}", topic["title"])
         .replace("{article}", html))
    r = parse_json(ask(p, kind="qa"))
    score = float(r.get("score", 0))
    problems = list(r.get("problems", []))
    ok = score >= cfg["min_score"] and not r.get("fabricated_claims")
    if r.get("fabricated_claims"):
        problems.append("Contains invented facts, prices, or specs. Remove them.")
    return ok, score, problems
