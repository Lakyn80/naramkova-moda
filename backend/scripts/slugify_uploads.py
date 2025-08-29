# backend/scripts/slugify_uploads.py
import os, re, unicodedata
from pathlib import Path

def slugify(name: str) -> str:
    base, ext = os.path.splitext(name)
    norm = unicodedata.normalize("NFKD", base)
    norm = "".join(c for c in norm if not unicodedata.combining(c))
    norm = norm.encode("ascii", "ignore").decode("ascii")
    norm = norm.lower()
    norm = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")
    if not norm:
        norm = "file"
    return f"{norm}{ext.lower()}"

def main():
    root = Path(__file__).resolve().parents[1] / "static" / "uploads"
    seen = set()
    print(f"Working dir: {root}")
    for p in sorted(root.glob("*")):
        if not p.is_file():
            continue
        new = slugify(p.name)
        # vyřešit kolize
        stem, ext = os.path.splitext(new)
        i = 1
        cand = new
        while cand in seen or ((p.parent / cand).exists() and (p.parent / cand) != p):
            cand = f"{stem}-{i}{ext}"
            i += 1
        seen.add(cand)
        if cand != p.name:
            print(f"{p.name} -> {cand}")
            p.rename(p.with_name(cand))
    print("Done.")

if __name__ == "__main__":
    main()
