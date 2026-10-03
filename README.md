# money-agents

Free, cloud-run multi-agent content site. Runs daily on GitHub Actions; nothing runs on your laptop.

Pipeline: Researcher -> Planner -> Writer -> QA (max 2 retries) -> Monetizer -> Publisher.

- Change the niche and site name in `config.json`.
- Kill switch: set `"paused": true` in `config.json`.
- Add affiliate links in `config.json` under `affiliate_links`, e.g. `{"Acer Aspire": "https://your-affiliate-link"}`.
- Failed articles go to `failed.json` and are retried (up to 3 times).
- After 3 failed runs in a row the system pauses itself (and sends a Telegram alert if you add the secrets).
