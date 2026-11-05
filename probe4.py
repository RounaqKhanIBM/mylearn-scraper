from playwright.sync_api import sync_playwright

URL = "https://mylearn.oracle.com/ou/course/application-integration-on-oracle-cloud/162997/272018"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 1500, "height": 1100})
    net = []
    pg.on("response", lambda r: net.append((r.status, r.request.resource_type, r.url[:170])))
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(15000)
    pg.screenshot(path="/workspace/mylearn-scraper/probe4.png")
    print("video tags:", pg.locator("video").count(), "iframes:", pg.locator("iframe").count())
    print("tab-ish ids:", pg.eval_on_selector_all("[id*=tab]", "els=>els.map(e=>e.id+'|'+e.getAttribute('role')+'|'+(e.innerText||'').slice(0,20))")[:20])
    for s, t, u in net:
        if any(k in u for k in ("video", "media", "player", "3play", "p3", "transcript", "brightcove", "vtt", "caption", "m3u8", "mp4", "token")):
            print(s, t, u)
    b.close()
