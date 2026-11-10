#!/usr/bin/env python3
"""Build a single-file executable for the current OS (PyInstaller cannot cross-compile).

    pip install -r requirements-build.txt
    python build.py

Output: dist/mylearn-scraper (macOS/Linux) or dist/mylearn-scraper.exe (Windows).
"""
import PyInstaller.__main__

PyInstaller.__main__.run([
    "scrape_course.py",
    "--name", "mylearn-scraper",
    "--onefile",
    "--console",          # the tool is terminal-based (interactive prompts)
    "--noconfirm",
    "--clean",
    "--collect-all", "playwright",   # bundles the Playwright Node driver
])
