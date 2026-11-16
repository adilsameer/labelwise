"""Cached HTTP GET.

Every response is stored once in cache/<sha1(url)>.json with the date it was
fetched. Later runs read the stored copy, so the same input gives the same
output. In offline mode a missing entry is an error, never a live call.
"""
import hashlib
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"
USER_AGENT = "labelwise/1.0 (adilsameer63@gmail.com)"

# Status codes that are a real answer from the source and safe to store.
# 404 = "no such record" (for example a name PubChem does not know).
CACHEABLE = {200, 400, 404}
MIN_GAP = 0.34  # seconds between live calls; NCBI allows 3/s without a key

offline = False
_last_call = 0.0

try:  # python.org builds on macOS often ship without CA certificates
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL = ssl.create_default_context()


class OfflineMiss(RuntimeError):
    pass


def cache_path(url):
    return CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest() + ".json")


def url_with(base, **params):
    return base + "?" + urllib.parse.urlencode(params) if params else base


def fetch(url):
    """Return {url, status, date, body}. body is the response text."""
    path = cache_path(url)
    if path.exists():
        return json.loads(path.read_text())
    if offline:
        raise OfflineMiss(url)

    entry = _get(url)
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(entry, indent=1, sort_keys=True))
    return entry


def fetch_json(url):
    """Return (entry, parsed body or None)."""
    entry = fetch(url)
    if entry["status"] != 200:
        return entry, None
    try:
        return entry, json.loads(entry["body"])
    except ValueError:
        return entry, None


def _get(url, tries=4):
    global _last_call
    for attempt in range(tries):
        wait = MIN_GAP - (time.monotonic() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30, context=_SSL) as resp:
                status, body = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError):
            status, body = None, None

        if status in CACHEABLE:
            return {"url": url, "status": status, "date": date.today().isoformat(), "body": body}
        time.sleep(2 ** attempt)  # 429, 5xx or network error: back off and retry
    raise RuntimeError(f"failed after {tries} tries: {url} (last status {status})")
