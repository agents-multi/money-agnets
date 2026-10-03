from .llm import ask, load_prompt, strip_fences


def run(cfg, topic, feedback=""):
    p = (load_prompt("writer")
         .replace("{niche}", cfg["niche"])
         .replace("{title}", topic["title"])
         .replace("{keyword}", topic.get("keyword", topic["title"]))
         .replace("{format}", topic.get("format", "how-to")))
    if feedback:
        p += "\n\nA reviewer rejected your last draft. Fix these problems:\n" + feedback
    return strip_fences(ask(p, kind="write"))
