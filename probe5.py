from playwright.sync_api import sync_playwright

URL = "https://mylearn.oracle.com/ou/course/application-integration-on-oracle-cloud/162997/272018"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
    pg = b.new_page(viewport={"width": 1500, "height": 1100})
    net = []
    pg.on("response", lambda r: net.append((r.status, r.request.resource_type, r.url[:180])) if r.request.resource_type in ("xhr", "fetch", "document", "media") else None)
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(12000)
    n0 = len(net)
    # click the big play button in the hero area
    pg.mouse.click(558, 455)
    pg.wait_for_timeout(10000)
    print("URL now:", pg.url)
    print("video tags:", pg.locator("video").count())
    print("tabs:", pg.eval_on_selector_all("[role=tab]", "els=>els.map(e=>e.id+'|'+(e.innerText||'').trim())"))
    dlg = pg.locator("[role=dialog], oj-dialog, .oj-dialog")
    for i in range(dlg.count()):
        t = dlg.nth(i).inner_text().strip()
        if t: print("DIALOG:", t[:400])
    tc = pg.locator(".p3sdk-interactive-transcript-content")
    print("transcript chars:", len(tc.first.inner_text()) if tc.count() else None)
    for s, t, u in net[n0:]:
        if "socket.io" not in u and "guidedlearning" not in u:
            print(s, t, u)
    pg.screenshot(path="/workspace/mylearn-scraper/probe5.png")
    b.close()
