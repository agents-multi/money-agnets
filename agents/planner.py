def run(cfg, state):
    """Pick today's topics from the queue (front of queue first, so retried topics go first)."""
    n = cfg["posts_per_run"]
    picked, state["queue"] = state["queue"][:n], state["queue"][n:]
    return picked
