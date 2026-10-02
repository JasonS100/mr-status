#!/usr/bin/env python3
"""External observation only: public heartbeat times, no SSH, keys or broker calls."""
from datetime import datetime, timezone
import json
import os
import sys
import time
import urllib.request

BASE = "https://raw.githubusercontent.com/JasonS100/mr-status/main/"


def health(payload, field, now, max_age):
    value = payload.get(field)
    if value is None:
        return False, "missing timestamp"
    try:
        stamp = (datetime.fromtimestamp(value, timezone.utc) if isinstance(value, (int, float))
                 else datetime.fromisoformat(str(value).replace("Z", "+00:00")))
        if stamp.tzinfo is None:
            return False, "timestamp has no timezone"
        age = (now - stamp).total_seconds()
        if age < -120:
            return False, "timestamp is in the future"
        return age <= max_age, f"age={round(age)}s; limit={max_age}s"
    except (ValueError, TypeError, OverflowError):
        return False, "invalid timestamp"


def probe():
    now = datetime.now(timezone.utc)
    okay = True
    nonce = str(time.time_ns())
    for filename, field, max_age in (("all_servers.json", "pushed_at_iso", 900),
                                     ("tdp_heartbeat.json", "generated_at", 1200)):
        try:
            req = urllib.request.Request(BASE + filename + "?probe=" + nonce,
                                         headers={"Cache-Control": "no-cache", "User-Agent": "TDP-offsite-observer/1"})
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read(2_000_000)
            payload = json.loads(raw)
            valid, message = health(payload, field, now, max_age)
        except Exception as e:
            valid, message = False, type(e).__name__ + " retrieving heartbeat"
        print(f"{filename}: {'PASS' if valid else 'FAIL'} {message}", flush=True)
        okay = okay and valid
    return okay


def self_test():
    now = datetime(2026, 10, 2, tzinfo=timezone.utc)
    tests = [({}, False), ({"t": "broken"}, False), ({"t": "2026-10-02T00:00:00"}, False),
             ({"t": "2026-10-02T00:00:00Z"}, True),
             ({"t": "2026-10-01T00:00:00Z"}, False),
             ({"t": "2030-01-01T00:00:00Z"}, False)]
    for data, expected in tests:
        assert health(data, "t", now, 900)[0] == expected
    print("6 watchdog fixture tests passed")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    elif probe():
        print("External host-publisher and engine-observer heartbeats are current.")
    else:
        print("Rechecking after 30 seconds; no remediation will be performed.", flush=True)
        time.sleep(30)
        if not probe():
            print("::error::TDP heartbeat unavailable or stale. Host, observer, publisher or GitHub delivery may be down. Inspect; do not auto-restart trading.")
            sys.exit(1)
