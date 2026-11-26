#!/usr/bin/env python3
"""Scrape GUR War & Sanctions "components in weapons" into a dated raw snapshot.

    python scripts/pipeline/scrape_gur.py                    # full scrape
    python scripts/pipeline/scrape_gur.py --max-pages 2      # quick test
    python scripts/pipeline/scrape_gur.py --resume FILE      # continue a broken run

Writes data/raw/gur/gur_raw_<YYYY-MM-DD>.jsonl.gz: one JSON object per
component page, with every labelled field GUR shows (name, marking,
headquarters country, manufacturer, production date, publication date,
importers and so on), the weapon it was found in, and the page URL.
Then run scripts/pipeline/normalise.py to turn it into the flat CSV the
scoring step reads.

Standard library only. Polite: one request at a time, at least 1.5 seconds
apart, exponential back-off on errors, a descriptive User-Agent. A full run
is about 540 list pages plus one page per component (6,377 on 25 Nov 2026),
so roughly three hours.
"""
import argparse
import datetime as dt
import gzip
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://war-sanctions.gur.gov.ua"
LIST = BASE + "/en/components?page={page}&per-page=12"
ITEM = BASE + "/en/components/{id}"
HEADERS = {"User-Agent": "teardown-index research scraper (open data; contact via GitHub repo)"}
DELAY = 1.5
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data", "raw", "gur")

_last = [0.0]


def fetch(url, tries=6):
    for i in range(tries):
        wait = DELAY - (time.time() - _last[0])
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            err = e
        back = DELAY * 2 ** (i + 1)
        print(f"  retry {i + 1} in {back:.0f}s ({err})", file=sys.stderr)
        time.sleep(back)
    raise SystemExit(f"Giving up on {url}")


def text(fragment):
    """HTML fragment to plain text, keeping <br> as newlines."""
    s = re.sub(r"<br\s*/?>", "\n", fragment)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    return "\n".join(line.strip() for line in s.split("\n")).strip()


def last_page(page_html):
    pages = [int(p) for p in re.findall(r"[?&]page=(\d+)&(?:amp;)?per-page=12", page_html)]
    return max(pages) if pages else 1


def item_ids(page_html):
    ids = re.findall(r'href="(?:https://war-sanctions\.gur\.gov\.ua)?/en/components/(\d+)"', page_html)
    return list(dict.fromkeys(ids))  # keep order, drop repeats


def parse_item(cid, page_html):
    rec = {"id": int(cid), "url": ITEM.format(id=cid)}
    weapon = re.search(r'class="preview-level preview-level-1[^"]*"[^>]*>(.*?)</a>', page_html, re.S)
    rec["weapon"] = text(weapon.group(1)) if weapon else ""
    levels = re.findall(r'class="preview-level preview-level-(\d)[^"]*"[^>]*>(.*?)</(?:a|div)>', page_html, re.S)
    rec["tree"] = [[int(n), text(v)] for n, v in levels]
    # Every labelled field: <div class="component-value-row ..."><div>Label</div> value ... </div>
    for block in re.findall(r'<div class="component-value-row(.*?)(?=<div class="component-value-row|<div class="mt-3 mb-3">)',
                            page_html, re.S):
        m = re.search(r"<div>(.*?)</div>(.*)", block, re.S)
        if not m:
            continue
        label = text(m.group(1))
        value = m.group(2)
        if label == "Name and marking":
            parts = re.findall(r"<div[^>]*>(.*?)</div>", value, re.S)
            rec["part_name"] = text(parts[0]) if parts else ""
            rec["marking"] = text(parts[1]) if len(parts) > 1 else ""
        else:
            rec[label] = text(value)
    return rec


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--max-pages", type=int, default=0, help="stop after this many list pages (testing)")
    p.add_argument("--resume", help="existing .jsonl.gz to continue; ids already in it are skipped")
    a = p.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    today = dt.date.today().isoformat()
    out = a.resume or os.path.join(OUT_DIR, f"gur_raw_{today}.jsonl.gz")
    done = set()
    if a.resume and os.path.exists(a.resume):
        # A scrape that was killed leaves a truncated gzip stream: keep every
        # complete record, rewrite the file cleanly, then append to it.
        lines = []
        try:
            with gzip.open(a.resume, "rt", encoding="utf-8") as f:
                for line in f:
                    lines.append(line)
        except EOFError:
            print("Resume file was cut off mid-write; keeping the complete records")
        while lines and not lines[-1].endswith("\n"):
            lines.pop()
        good = []
        for line in lines:
            try:
                done.add(json.loads(line)["id"])
                good.append(line)
            except (ValueError, KeyError):
                pass
        with gzip.open(a.resume, "wt", encoding="utf-8") as f:
            f.writelines(good)
        print(f"Resuming: {len(done):,} components already saved")

    first = fetch(LIST.format(page=1))
    n_pages = last_page(first)
    if a.max_pages:
        n_pages = min(n_pages, a.max_pages)
    total = re.search(r"Total number:\s*([\d][\d\s]*)", text(first))
    print(f"{n_pages} list pages to read; GUR reports total {total.group(1).strip() if total else '?'}")

    ids = []
    for page in range(1, n_pages + 1):
        page_html = first if page == 1 else fetch(LIST.format(page=page))
        ids.extend(item_ids(page_html))
        if page % 50 == 0:
            print(f"list page {page}/{n_pages}: {len(ids):,} ids", flush=True)
    ids = list(dict.fromkeys(ids))
    print(f"{len(ids):,} component ids")

    with gzip.open(out, "at", encoding="utf-8") as f:
        for k, cid in enumerate(ids, 1):
            if int(cid) in done:
                continue
            page_html = fetch(ITEM.format(id=cid))
            if page_html is None:
                continue
            rec = parse_item(cid, page_html)
            rec["retrieved"] = today
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if k % 250 == 0:
                print(f"component {k:,}/{len(ids):,}", flush=True)
    print(f"Saved to {out}")


if __name__ == "__main__":
    main()
