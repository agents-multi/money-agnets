from .llm import ask, parse_json, load_prompt


def run(cfg, state):
    known = [p["title"] for p in state["published"]] + [t["title"] for t in state["queue"]]
    prompt = (load_prompt("researcher")
              .replace("{niche}", cfg["niche"])
              .replace("{existing}", "; ".join(known[-60:]) or "none"))
    topics = parse_json(ask(prompt, kind="topics"))
    return [t for t in topics if t.get("title") and t["title"] not in known]
