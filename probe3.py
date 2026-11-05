import re
from playwright.sync_api import sync_playwright

URL = "https://mylearn.oracle.com/ou/course/application-integration-on-oracle-cloud/162997/272018"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1500, "height": 1000})
    reqs = []
    pg.on("response", lambda r: reqs.append((r.status, r.url)) if ("3play" in r.url or "transcript" in r.url.lower()) else None)
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(10000)
    tabs = pg.locator("[role=tab]")
    print("TABS:", [tabs.nth(i).inner_text() for i in range(tabs.count())])
    try:
        pg.locator("#transcript-tab").click(timeout=5000)
    except Exception as e:
        print("click err", str(e)[:150])
    pg.wait_for_timeout(5000)
    sel = ".p3sdk-interactive-transcript"
    print("count:", pg.locator(sel).count())
    t = pg.locator(sel).first.inner_text() if pg.locator(sel).count() else ""
    print("LEN", len(t)); print(t[:900])
    html = pg.locator(sel).first.inner_html()
    print(html[:1800])
    for r in reqs: print(r[0], r[1][:200])
    b.close()
