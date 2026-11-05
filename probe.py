import json, sys
from playwright.sync_api import sync_playwright

URL = "https://mylearn.oracle.com/ou/course/application-integration-on-oracle-cloud/162997/272018"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    pg = b.new_page()
    calls = []
    pg.on("response", lambda r: calls.append((r.status, r.request.resource_type, r.url)))
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(12000)
    print("TITLE:", pg.title())
    print("FINAL URL:", pg.url)
    for s, t, u in calls:
        if t in ("xhr", "fetch", "document"):
            print(s, t, u[:200])
    print("---- TEXT ----")
    print(pg.inner_text("body")[:2000])
    pg.screenshot(path="/workspace/mylearn-scraper/probe.png")
    b.close()
