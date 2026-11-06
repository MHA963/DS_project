"""Shared helpers: config, version parsing, throttled sending."""
import re, time, hashlib

REPLICAS = 3                       # task 1: three full copies on three distinct nodes
BASE_PORT = 8001                   # storage node i listens on BASE_PORT + i
LEAD_PORT = 8000
CHUNK = 64 * 1024

# "report_v3.txt" -> ("report.txt", 3);  "report.txt" -> ("report.txt", None)
_VER = re.compile(r"^(?P<stem>.*?)(?:_v(?P<ver>\d+))?(?P<ext>\.[^.]*)?$")

def parse_name(filename):
    m = _VER.match(filename)
    stem, ver, ext = m.group("stem"), m.group("ver"), m.group("ext") or ""
    return stem + ext, (int(ver) if ver is not None else None)

def blob_key(base, version):
    """Name under which a given version is stored on a node (filesystem safe)."""
    safe = base.replace("/", "_")
    return f"{safe}__v{version}"

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def throttled(data: bytes, rate_bps):
    """Yield data in chunks no faster than rate_bps bits/s (emulates a link of bandwidth R).
    rate_bps=None -> full speed."""
    if not rate_bps:
        yield data
        return
    t0 = time.perf_counter()
    sent = 0
    for i in range(0, len(data), CHUNK):
        chunk = data[i:i + CHUNK]
        yield chunk
        sent += len(chunk)
        due = t0 + sent * 8 / rate_bps
        d = due - time.perf_counter()
        if d > 0:
            time.sleep(d)
