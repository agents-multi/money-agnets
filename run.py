"""Orchestrator: runs the whole pipeline once. Triggered daily by GitHub Actions."""
import json, sys, traceback
from datetime import date
from pathlib import Path

from agents import researcher, planner, writer, qa, monetizer, publisher
from agents.notify import alert

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text())
STATE_FILE, DEAD_FILE = ROOT / "state.json", ROOT / "failed.json"
MAX_WRITER_RETRIES, MAX_ATTEMPTS_PER_TOPIC, BREAKER = 2, 3, 3


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, data):
    path.write_text(json.dumps(data, indent=2))


def produce(topic):
    """Writer -> QA (with retries) -> Monetizer -> Publisher. Returns URL or raises."""
    feedback, last = "", []
    for attempt in range(MAX_WRITER_RETRIES + 1):
        draft = writer.run(CFG, topic, feedback)
        ok, score, problems = qa.run(CFG, topic, draft)
        print(f"  QA attempt {attempt + 1}: score={score} ok={ok} problems={problems}")
        if ok:
            return publisher.run(CFG, topic, monetizer.run(CFG, draft))
        feedback, last = "\n".join(problems), problems
    raise RuntimeError("QA rejected after retries: " + "; ".join(last))


def main():
    state = load(STATE_FILE, {"paused": False, "consecutive_failures": 0, "queue": [], "published": []})
    dead = load(DEAD_FILE, [])

    if CFG.get("paused") or state["paused"]:
        print("Paused (kill switch). Nothing to do.")
        return

    # Retry dead letters first (up to MAX_ATTEMPTS_PER_TOPIC times in total)
    retry = [d["topic"] for d in dead if d["attempts"] < MAX_ATTEMPTS_PER_TOPIC]
    state["queue"] = retry + state["queue"]
    dead_keep = [d for d in dead if d["attempts"] >= MAX_ATTEMPTS_PER_TOPIC]
    attempts = {d["topic"]["title"]: d["attempts"] for d in dead}
    dead = dead_keep

    run_failed = False
    try:
        if len(state["queue"]) < CFG["posts_per_run"]:
            state["queue"] += researcher.run(CFG, state)
        todo = planner.run(CFG, state)
    except Exception as e:
        print("Research/planning failed:", e)
        todo, run_failed = [], True
        last_error = str(e)

    ok_count = 0
    for topic in todo:
        print("Producing:", topic["title"])
        try:
            url = produce(topic)
            if url:
                state["published"].append({"title": topic["title"], "date": date.today().isoformat(), "url": url})
                ok_count += 1
                print("  Published:", url)
        except Exception as e:
            traceback.print_exc()
            last_error = str(e)
            dead.append({"topic": topic, "attempts": attempts.get(topic["title"], 0) + 1,
                         "error": str(e), "date": date.today().isoformat()})

    if todo and ok_count == 0 or run_failed:
        state["consecutive_failures"] += 1
        if state["consecutive_failures"] >= BREAKER:
            state["paused"] = True
            alert(f"money-agents PAUSED after {BREAKER} failed runs. Last error: {last_error}")
    elif ok_count:
        state["consecutive_failures"] = 0

    save(STATE_FILE, state)
    save(DEAD_FILE, dead)
    print(f"Done. Published {ok_count}. Queue: {len(state['queue'])}. Failures in a row: {state['consecutive_failures']}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(0)  # never crash the workflow; state is committed either way
