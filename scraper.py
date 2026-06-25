"""
Wayback Machine scraper for site reconstruction.
Usage: python scraper.py <site> <domain>
  site:   folder name under trikkia/ (e.g. blue-room)
  domain: original domain (e.g. blue-room.it)
"""

import sys
import os
import json
import time
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse, urljoin
from pathlib import Path

WAYBACK = "https://web.archive.org"
CDX_API = f"{WAYBACK}/cdx/search/cdx"
DELAY   = 0.8   # seconds between requests — be polite


def cdx_urls(domain: str) -> list[dict]:
    """Return all unique URLs captured for domain, with best timestamp."""
    params = (
        f"?url={domain}/*"
        f"&output=json"
        f"&fl=timestamp,original,statuscode,mimetype"
        f"&collapse=urlkey"
        f"&filter=statuscode:200"
        f"&limit=5000"
    )
    url = CDX_API + params
    print(f"[CDX] querying {url}")
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.loads(r.read())
    if not data:
        return []
    keys = data[0]
    rows = [dict(zip(keys, row)) for row in data[1:]]
    print(f"[CDX] found {len(rows)} unique URLs")
    return rows


def wayback_url(timestamp: str, original: str) -> str:
    return f"{WAYBACK}/web/{timestamp}/{original}"


def local_path(out_dir: Path, original_url: str) -> Path:
    """Map an original URL to a local file path."""
    parsed = urlparse(original_url)
    path = parsed.path.lstrip("/")
    # strip query strings from filename
    if parsed.query:
        ext = Path(path).suffix or ".html"
        path = path + ext
    if not path or path.endswith("/"):
        path = path + "index.html"
    # ensure html extension for pages without one
    p = Path(path)
    if not p.suffix or p.suffix.lower() in ("", ".htm", ".html", ".php", ".asp"):
        if not p.suffix:
            path = path + ".html"
    return out_dir / path


def strip_wayback_toolbar(html: bytes) -> bytes:
    """Remove Wayback Machine injected toolbar and scripts (best effort)."""
    text = html.decode("utf-8", errors="replace")
    # remove toolbar div block
    text = re.sub(
        r"<!-- BEGIN WAYBACK TOOLBAR INSERT -->.*?<!-- END WAYBACK TOOLBAR INSERT -->",
        "",
        text,
        flags=re.DOTALL,
    )
    # rewrite /web/TIMESTAMP/http://... URLs back to relative paths
    text = re.sub(r"https?://web\.archive\.org/web/\d+[a-z_]*/", "", text)
    return text.encode("utf-8")


def download(wb_url: str, dest: Path, strip_toolbar: bool = True) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  [skip] {dest.name}")
        return True
    try:
        req = urllib.request.Request(wb_url, headers={"User-Agent": "trikkia-scraper/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if strip_toolbar and dest.suffix.lower() in (".html", ".htm", ""):
            data = strip_wayback_toolbar(data)
        dest.write_bytes(data)
        print(f"  [ok]   {dest.relative_to(dest.parents[3])}")
        return True
    except Exception as e:
        print(f"  [ERR]  {wb_url} → {e}")
        return False


def scrape(site: str, domain: str):
    out_dir = Path(__file__).parent / site / "scraped"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = cdx_urls(domain)
    if not rows:
        print("No URLs found — check domain name.")
        return

    # save raw CDX index for reference
    index_file = out_dir / "_cdx_index.json"
    index_file.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    print(f"[CDX] index saved → {index_file}")

    # separate HTML pages from assets
    html_mimes = {"text/html", "application/xhtml+xml"}
    pages  = [r for r in rows if r.get("mimetype", "").split(";")[0].strip() in html_mimes]
    assets = [r for r in rows if r not in pages]

    print(f"\n[SCRAPE] {len(pages)} HTML pages + {len(assets)} assets")
    print("=" * 60)

    failed = []

    print("\n--- HTML pages ---")
    for row in pages:
        wb = wayback_url(row["timestamp"], row["original"])
        dest = local_path(out_dir, row["original"])
        ok = download(wb, dest, strip_toolbar=True)
        if not ok:
            failed.append(row)
        time.sleep(DELAY)

    print("\n--- Assets (images, CSS, JS, SWF…) ---")
    for row in assets:
        wb = wayback_url(row["timestamp"], row["original"])
        dest = local_path(out_dir, row["original"])
        ok = download(wb, dest, strip_toolbar=False)
        if not ok:
            failed.append(row)
        time.sleep(DELAY)

    print(f"\n{'='*60}")
    print(f"Done. {len(rows)-len(failed)}/{len(rows)} downloaded.")
    if failed:
        fail_log = out_dir / "_failed.json"
        fail_log.write_text(json.dumps(failed, indent=2, ensure_ascii=False))
        print(f"{len(failed)} failed → {fail_log}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scraper.py <site-folder> <domain>")
        print("  e.g. python scraper.py blue-room blue-room.it")
        sys.exit(1)
    scrape(sys.argv[1], sys.argv[2])
