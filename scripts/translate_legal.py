#!/usr/bin/env python3
"""Translate assets/legal/*.html (English) into assets/legal/ro/*.html with the DeepL API.

Needs the DEEPL_API_KEY environment variable (free keys end in ":fx").
Only re-translates files whose source changed (hash stored in assets/legal/ro/.hashes.json).
Use --force to re-translate everything.
"""
import hashlib, json, os, sys, urllib.parse, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "legal"
OUT = SRC / "ro"
HASHES = OUT / ".hashes.json"
FILES = ["terms.html", "privacy.html"]


def translate(html, key):
    host = "api-free.deepl.com" if key.endswith(":fx") else "api.deepl.com"
    data = urllib.parse.urlencode({
        "text": html,
        "source_lang": "EN",
        "target_lang": "RO",
        "tag_handling": "html",
        "preserve_formatting": "1",
    }).encode()
    req = urllib.request.Request(
        f"https://{host}/v2/translate", data=data,
        headers={"Authorization": f"DeepL-Auth-Key {key}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)["translations"][0]["text"]
    except urllib.error.HTTPError as e:
        sys.exit(f"DeepL error {e.code}: {e.read().decode(errors='replace')}")


def main():
    key = os.environ.get("DEEPL_API_KEY", "").strip()
    if not key:
        sys.exit("DEEPL_API_KEY is not set")
    force = "--force" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    hashes = json.loads(HASHES.read_text()) if HASHES.exists() else {}
    for name in FILES:
        text = (SRC / name).read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode()).hexdigest()
        if not force and hashes.get(name) == digest and (OUT / name).exists():
            print(f"{name}: unchanged, skipped")
            continue
        (OUT / name).write_text(translate(text, key).rstrip() + "\n", encoding="utf-8")
        hashes[name] = digest
        print(f"{name}: translated")
    HASHES.write_text(json.dumps(hashes, indent=2) + "\n")


if __name__ == "__main__":
    main()
