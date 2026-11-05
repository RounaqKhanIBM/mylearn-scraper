#!/usr/bin/env python3
"""
Scrape an Oracle MyLearn course into local transcript files.

    <OUT>/<Course_Name>/<MM>_<Module_Name>/<NN>_<Video_Name>.txt

* <MM> / <NN> are zero-padded playlist positions (module within the course, video within the module).
* Spaces become '_' (e.g. "Intro to OCI" -> 01_Intro_to_OCI.txt, module "Networking" -> 02_Networking/).
* Each .txt contains the video title/URL followed by the text of its Transcript tab.
* If a video has no transcript, no file is written for it. It is reported in the terminal and listed in
  <OUT>/<Course_Name>/MISSING_TRANSCRIPTS.txt, and the script still exits 0 (--fail-fast stops at the first one).

Transcripts are only served to signed-in users, so log in once:

    python3 scrape_course.py --login "<course url>"      # opens a real browser; sign in; press Enter
    python3 scrape_course.py "<course url>"              # reuses that saved session (headless)

Useful flags:
    --dry-run        only list modules/videos and the files that WOULD be created (no login needed)
    --out DIR        output root (default ./output)
    --only-module N  only module number N (1-based); repeatable
    --fail-fast      stop at the first video without a transcript
    --headed         show the browser while scraping
    --browser PATH   path to a Chrome/Chromium binary (auto-detected otherwise)
"""
import argparse
import html
import re
import shutil
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

VIDEO_TYPE_ID = "1"          # component typeId for videos (2 = skill check, etc.)
TRANSCRIPT_SEL = ".p3sdk-interactive-transcript-content"
PROFILE_DIR = Path.home() / ".mylearn_profile"
DEFAULT_OUT = Path("output")


class NotLoggedIn(RuntimeError):
    pass


class MissingTranscript(RuntimeError):
    pass


def safe_name(s: str) -> str:
    """'Demo: Using Projects' -> 'Demo_Using_Projects' (spaces -> '_', '&' -> 'and', only [\\w.-] kept)."""
    s = html.unescape(s).strip()
    s = s.replace("&", " and ")
    s = re.sub(r'[\\/:*?"<>|]+', "", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^\w.\-]+", "", s)
    s = re.sub(r"_+", "_", s).strip("_.")
    return s or "untitled"


def parse_url(url: str):
    m = re.search(r"/course/([^/]+)/(\d+)(?:/(\d+))?", url)
    if not m:
        sys.exit(f"Can't parse course id from URL: {url}")
    return m.group(1), m.group(2), m.group(3)  # slug, course_id, component_id


def find_browser(explicit):
    if explicit:
        return explicit
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    return None  # fall back to Playwright's bundled Chromium


def launch(p, args, headless):
    kw = dict(
        headless=headless,
        viewport={"width": 1500, "height": 1100},
        args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"],
    )
    exe = find_browser(args.browser)
    if exe:
        kw["executable_path"] = exe
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return p.chromium.launch_persistent_context(str(PROFILE_DIR), **kw)


def get_course_metadata(page, course_id, url):
    """Load the course page and capture the metadata JSON the SPA fetches (modules + components)."""
    box = {}

    def on_resp(r):
        if f"/api/eml-content/courses/{course_id}/metadata" in r.url and r.status == 200:
            try:
                box["meta"] = r.json()
            except Exception:
                pass

    page.on("response", on_resp)
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    deadline = time.time() + 60
    while "meta" not in box and time.time() < deadline:
        page.wait_for_timeout(500)
    page.remove_listener("response", on_resp)
    if "meta" not in box:
        sys.exit("Could not capture course metadata (page changed or blocked?).")
    return box["meta"]


def build_plan(meta, slug, only_modules):
    plan = []
    for i, mod in enumerate(meta["modules"], 1):
        if only_modules and i not in only_modules:
            continue
        mod_dir = f"{i:02d}_{safe_name(mod['name'])}"
        seen = {}
        vids = []
        for c in mod.get("components", []):
            if str(c.get("typeId")) != VIDEO_TYPE_ID:
                continue  # skill checks, quizzes, etc.
            fname = safe_name(c["name"])
            seen[fname] = seen.get(fname, 0) + 1
            if seen[fname] > 1:
                fname = f"{fname}_{seen[fname]}"
            vids.append(dict(id=str(c["id"]), title=html.unescape(c["name"]), file=f"{len(vids) + 1:02d}_{fname}.txt"))
        plan.append(dict(index=i, module=html.unescape(mod["name"]), dir=mod_dir, videos=vids))
    return plan


def extract_transcript(page, video_url, timeout_s=45):
    page.goto(video_url, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(4000)

    body = ""
    try:
        body = page.inner_text("body")
    except Exception:
        pass
    # Guest/unauthenticated sessions get sign-in / "consumed the free content" dialogs.
    if page.locator("text=Returning User?").count() or "consumed the free digital content" in body:
        raise NotLoggedIn("Not signed in (MyLearn is treating this session as a guest).")

    # Open the Transcript tab if the tab strip exposes one.
    for sel in ("#transcript-tab", "[role=tab]:has-text('Transcript')"):
        loc = page.locator(sel)
        if loc.count():
            try:
                loc.first.click(timeout=3000)
            except Exception:
                pass
            break

    deadline = time.time() + timeout_s
    text = ""
    while time.time() < deadline:
        loc = page.locator(TRANSCRIPT_SEL)
        if loc.count():
            try:
                # textContent per <p> (not inner_text) so paragraph breaks don't depend on layout/render timing.
                paras = loc.first.evaluate(
                    "el => Array.from(el.querySelectorAll('p'))"
                    ".map(p => p.textContent.replace(/\\s+/g, ' ').trim()).filter(Boolean)")
                text = "\n\n".join(paras) if paras else loc.first.text_content().strip()
            except Exception:
                text = ""
            if len(text) > 20:
                break
        page.wait_for_timeout(1000)
    if len(text) <= 20:
        raise MissingTranscript("Transcript tab empty / not found after %ds" % timeout_s)
    return text


def write_missing_report(path, failures, total):
    """Human-readable list of videos whose MyLearn page has no transcript."""
    lines = [
        "Videos without a transcript on MyLearn",
        f"{len(failures)} of {total} videos in this run had no transcript, so no file was written for them.",
        "",
    ]
    for label, url, why in failures:
        lines += [label, f"  {url}", f"  {why}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--fail-fast", action="store_true")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--only-module", type=int, action="append")
    ap.add_argument("--browser")
    args = ap.parse_args()

    slug, course_id, _ = parse_url(args.url)

    with sync_playwright() as p:
        if args.login:
            ctx = launch(p, args, headless=False)
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto(args.url, wait_until="domcontentloaded")
            input("\nSign in to your Oracle account in the browser window, make sure a video plays,\n"
                  "then press Enter here to save the session... ")
            ctx.close()
            print(f"Session saved in {PROFILE_DIR}. Now run without --login.")
            return 0

        ctx = launch(p, args, headless=not args.headed)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        meta = get_course_metadata(page, course_id, args.url)
        course_name = safe_name(meta["name"])
        plan = build_plan(meta, slug, set(args.only_module or []))
        root = Path(args.out) / course_name

        total = sum(len(m["videos"]) for m in plan)
        print(f"Course: {meta['name']}  ->  {root}\n{len(plan)} modules, {total} videos")

        if args.dry_run:
            for m in plan:
                print(f"\n[{m['index']}] {m['dir']}/")
                for v in m["videos"]:
                    print(f"      {v['file']}")
            ctx.close()
            return 0

        ok, failures = 0, []
        for m in plan:
            mdir = root / m["dir"]
            mdir.mkdir(parents=True, exist_ok=True)
            for v in m["videos"]:
                vurl = f"https://mylearn.oracle.com/ou/course/{slug}/{course_id}/{v['id']}"
                label = f"{m['dir']}/{v['file']}"
                try:
                    text = extract_transcript(page, vurl)
                except NotLoggedIn as e:
                    ctx.close()
                    sys.exit(f"\nABORT: {e}\nRun once with --login to sign in, then retry.")
                except MissingTranscript as e:
                    print(f"  [MISSING] {label}: {e}")
                    failures.append((label, vurl, str(e)))
                    if args.fail_fast:
                        break
                    continue
                (mdir / v["file"]).write_text(
                    f"Video: {v['title']}\nModule: {m['module']}\nURL: {vurl}\n\n"
                    f"===== TRANSCRIPT =====\n{text}\n",
                    encoding="utf-8",
                )
                ok += 1
                print(f"  [ok] {label} ({len(text)} chars)")
            if failures and args.fail_fast:
                break
        ctx.close()

        print(f"\nDone: {ok}/{total} transcripts saved under {root}")
        if failures:
            print(f"\nNOTE: {len(failures)} video(s) have no transcript on MyLearn (no file written):")
            for label, u, why in failures:
                print(f"   - {label}\n     {u}")
            report = root / "MISSING_TRANSCRIPTS.txt"
            write_missing_report(report, failures, total)
            print(f"\nFull list saved to {report}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
