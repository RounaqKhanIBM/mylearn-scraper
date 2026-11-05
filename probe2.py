import json, re
from playwright.sync_api import sync_playwright

URL = "https://mylearn.oracle.com/ou/course/application-integration-on-oracle-cloud/162997/272018"
store = {}
def on_resp(r):
    if "/api/" in r.url and r.request.resource_type in ("xhr", "fetch"):
        try:
            store[r.url] = r.json()
        except Exception:
            pass

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1500, "height": 1000})
    pg.on("response", on_resp)
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(12000)
    for u, j in store.items():
        if "courses/162997/metadata" in u or u.endswith("/api/eml-content/search") or "clist" in u:
            fn = "/workspace/mylearn-scraper/api_" + re.sub(r"\W+", "_", u.split("/api/")[1])[:60] + ".json"
            open(fn, "w").write(json.dumps(j, indent=1))
            print(fn, len(json.dumps(j)))
    # module/video DOM text
    txt = pg.inner_text("body")
    i = txt.find("Auto Play")
    print(txt[i:i+1500])
    pg.screenshot(path="/workspace/mylearn-scraper/probe.png", full_page=False)
    open("/workspace/mylearn-scraper/page.html", "w").write(pg.content())
    b.close()
