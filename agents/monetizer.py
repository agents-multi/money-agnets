import re

PATTERN = re.compile(r"\[\[AFFILIATE:\s*(.*?)\]\]")


def run(cfg, html):
    links = {k.lower(): v for k, v in cfg.get("affiliate_links", {}).items()}

    def repl(m):
        name = m.group(1).strip()
        for key, url in links.items():
            if key in name.lower() or name.lower() in key:
                return f'<a href="{url}" rel="sponsored nofollow noopener" target="_blank">{name}</a>'
        return name  # no link configured: keep plain text

    html = PATTERN.sub(repl, html)
    if 'rel="sponsored' in html:
        html = f'<p><em>{cfg["disclosure"]}</em></p>\n' + html
    return html
