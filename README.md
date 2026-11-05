# MyLearn Transcript Scraper

Downloads the video transcripts from an Oracle MyLearn course into plain-text files, organized by module and in playlist order.

## Requirements

- macOS or Linux (the launcher is a bash script; on Windows use WSL or Git Bash)
- Python 3 (`python3` on your PATH)
- An Oracle account that can view the course. Transcripts are only served to signed-in users.

Everything else (a virtual environment, Playwright, and Chromium) is installed by the setup step below.

## Quick start

```bash
# 1. Set up the environment (once). Creates .venv/, installs Playwright, downloads Chromium.
./run.sh setup

# 2. Sign in once. A browser window opens; sign in, make sure a video plays,
#    then press Enter in the terminal.
./run.sh login "https://mylearn.oracle.com/ou/course/<course-name>/<course-id>"

# 3. (Optional) Preview what would be saved. Nothing is written.
./run.sh preview "https://mylearn.oracle.com/ou/course/<course-name>/<course-id>"

# 4. Download the transcripts.
./run.sh scrape "https://mylearn.oracle.com/ou/course/<course-name>/<course-id>"
```

Setup takes a minute or two the first time because of the Chromium download. Running it again does nothing if everything is already installed, and it reinstalls if `requirements.txt` has changed. `./setup.sh` does the same thing as `./run.sh setup`.

The other commands refuse to run until setup has been done.

Any URL for the course works, with or without a trailing video ID. Put the URL in quotes.

## Commands

| Command | What it does |
|---|---|
| `./run.sh setup` | Creates the virtual environment and installs the dependencies and browser. Run once before anything else. |
| `./run.sh login "<url>"` | Opens a browser so you can sign in. The session is saved for later runs. |
| `./run.sh preview "<url>" [options]` | Dry run. Lists every module folder and file that would be created. Writes nothing and does not need a saved login. |
| `./run.sh scrape "<url>" [options]` | Downloads the transcripts. |

### Options

Options go after the URL and are passed through to the scraper.

| Option | Description |
|---|---|
| `--only-module N` | Only scrape module number N (1-based). Repeat it for several modules, e.g. `--only-module 1 --only-module 3`. |
| `--out DIR` | Output folder. Default: `./output` |
| `--fail-fast` | Stop at the first video that has no transcript. |
| `--headed` | Show the browser while scraping. |
| `--browser PATH` | Use a specific Chrome/Chromium binary instead of the one Playwright installs. |

Example, for modules 1 and 2 only:

```bash
./run.sh scrape "https://mylearn.oracle.com/ou/course/<course-name>/<course-id>" --only-module 1 --only-module 2
```

## Output

```
output/
└── <Course_Name>/
    ├── 01_<Module_Name>/
    │   ├── 01_<Video_Name>.txt
    │   ├── 02_<Video_Name>.txt
    │   └── ...
    ├── 02_<Module_Name>/
    │   └── ...
    └── MISSING_TRANSCRIPTS.txt      (only if some videos had no transcript)
```

- Module and video numbers are zero-padded playlist positions, so files sort in course order. A module keeps its number even if you scrape it alone with `--only-module`.
- Names are cleaned for the file system: spaces become `_`, `&` becomes `and`, and anything other than letters, digits, `_`, `.` and `-` is removed.
- Quizzes and skill checks are skipped. Only videos are saved, and the video numbering counts only videos.

Each file looks like this:

```
Video: <video title>
Module: <module title>
URL: <video url>

===== TRANSCRIPT =====
[AUDIO LOGO]

<paragraph>

<paragraph>
...
```

The `[AUDIO LOGO]` text comes from the transcript on MyLearn.

## Videos without a transcript

Some videos have no transcript on MyLearn. For these, the scraper:

- writes no file for the video,
- prints a note in the terminal listing each one with its URL,
- saves the full list to `<course folder>/MISSING_TRANSCRIPTS.txt`, and
- still exits with code 0.

The list reflects the most recent run that had missing videos. A run with none does not clear an older file. Each video is given 45 seconds to show a transcript, so a very slow page load could also land on this list. If a video you expect to have a transcript is listed, run it again.

## Troubleshooting

**"The environment is not set up yet. Run: ./run.sh setup"**
Setup has not been run in this folder, or `requirements.txt` changed since it last ran. Run `./run.sh setup`.

**"Not signed in (MyLearn is treating this session as a guest)"**
Your saved session is missing or has expired. Run `./run.sh login "<url>"` again.

**"Can't parse course id from URL"**
The URL needs the form `https://mylearn.oracle.com/ou/course/<name>/<course-id>`.

**"Could not capture course metadata"**
The course page did not load its data within 60 seconds, or the page structure has changed. Try again, or add `--headed` to watch what the browser is doing.

**No browser window appears during login**
The Playwright browser may be hidden behind other windows. It is a separate Chromium window, not your normal Chrome.

## Notes on your saved login

`login` stores the browser profile, including your session cookies, in `~/.mylearn_profile`. Treat it like a password. Anyone with access to that folder can use your MyLearn session. Delete the folder to sign out.

`.gitignore` excludes `.venv/` and `output/`, so downloaded transcripts and the virtual environment are not committed.

## Files

| File | Purpose |
|---|---|
| `run.sh` | Launcher for `setup`, `login`, `preview` and `scrape` |
| `setup.sh` | Creates the virtual environment and installs the dependencies and browser (also available as `./run.sh setup`) |
| `scrape_course.py` | The scraper itself. Run it directly with `python3 scrape_course.py --help` for the full flag list |
| `requirements.txt` | Pinned Python dependency (Playwright) |
