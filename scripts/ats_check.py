#!/usr/bin/env python3
"""ATS readiness check for the resume PDFs.

Usage: ats_check.py FILE.pdf [FILE.pdf ...]   (a .txt file is read as extracted text)

Extracts text with `pdftotext -layout` (what most ATS parsers see) and scores it
against a transparent 100-point checklist. This is NOT a vendor score; it checks
the things we control. Exit code is 1 only for hard failures:
  garbled/private-use glyphs, more than 2 pages, a missing required heading,
  or missing email/phone.

Score = parseability (30) + contact/structure (15) + keywords (30) + content (25)

Set ATS_EXTRA_KEYWORDS="term one,term two" to add job-description keywords.
Writes a markdown report to $GITHUB_STEP_SUMMARY when that variable is set.
"""
import collections
import os
import re
import subprocess
import sys
import unicodedata

REQUIRED = ["SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION"]
MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
DATE_RANGE = re.compile(MONTH + r" \d{4} [–-]+ (?:" + MONTH + r" \d{4}|Present)")

# (label, weight, [lowercase alternatives; any match counts])
KEYWORDS = [
    ("Swift", 3, ["swift"]), ("SwiftUI", 3, ["swiftui"]), ("UIKit", 3, ["uikit"]),
    ("Objective-C", 1, ["objective-c"]), ("Combine", 2, ["combine"]),
    ("async/await", 2, ["async/await", "swift concurrency"]),
    ("Core Data", 2, ["core data"]), ("MVVM", 3, ["mvvm"]),
    ("Clean Architecture", 2, ["clean architecture"]),
    ("Dependency Injection", 1, ["dependency injection"]),
    ("GCD / Operation Queues", 2, ["gcd", "operation queues"]),
    ("REST API", 3, ["rest api"]), ("Firebase", 1, ["firebase"]),
    ("Push Notifications", 1, ["push notification", "apns"]),
    ("Deep Linking", 1, ["deep link"]), ("Accessibility", 1, ["accessibility"]),
    ("XCTest", 3, ["xctest"]), ("UI Testing", 1, ["xcuitest", "ui testing"]),
    ("Unit Testing", 2, ["unit testing", "unit/ui testing"]), ("TDD/BDD", 1, ["tdd", "bdd"]),
    ("CI/CD", 3, ["ci/cd"]), ("Fastlane", 2, ["fastlane"]), ("GitHub Actions", 1, ["github actions"]),
    ("Git", 2, ["git"]), ("Xcode", 2, ["xcode"]), ("TestFlight", 1, ["testflight"]),
    ("App Store", 2, ["app store"]), ("Swift Package Manager", 1, ["swift package manager"]),
    ("CocoaPods", 1, ["cocoapods"]), ("Agile", 1, ["agile"]),
    ("Kotlin Multiplatform", 1, ["kotlin multiplatform"]),
    ("Keychain/Biometrics", 1, ["keychain", "biometrics"]),
]
for term in filter(None, (t.strip().lower() for t in os.environ.get("ATS_EXTRA_KEYWORDS", "").split(","))):
    KEYWORDS.append((term, 2, [term]))


def extract(path):
    if path.endswith(".txt"):
        text = open(path, encoding="utf-8", errors="replace").read()
        return text, text.strip().count("\f") + 1
    text = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True,
                          text=True, check=True).stdout
    info = subprocess.run(["pdfinfo", path], capture_output=True, text=True, check=True).stdout
    return text, int(re.search(r"Pages:\s+(\d+)", info).group(1))


def check(path):
    text, pages = extract(path)
    low = text.lower()
    lines = text.replace("\f", "\n").split("\n")
    is_full = "full" in os.path.basename(path).lower()
    hard, warn = [], []

    # --- parseability (30) ---
    odd = collections.Counter(c for c in text if ord(c) > 127)
    garbage = [c for c in odd if 0xE000 <= ord(c) <= 0xF8FF or unicodedata.category(c) in ("Co", "Cn")]
    pars = 0
    if garbage:
        hard.append("private-use/garbled glyphs: " + " ".join(f"U+{ord(c):04X}" for c in garbage))
    else:
        pars += 15
    if pages > 2:
        hard.append(f"{pages} pages (limit 2)")
    else:
        pars += 10
        if pages > 1 and not is_full:
            warn.append(f"Brief variant is {pages} pages (1 preferred)")
    name_ok = any("rehan ali" in l.lower() for l in lines[:6])
    pars += 5 if name_ok else 0
    if not name_ok:
        warn.append("name not in the first lines (reading order?)")

    # --- contact & structure (15) ---
    struct = 0
    headings = [h for h in REQUIRED + (["PROJECTS"] if is_full else [])
                if re.search(rf"^\s*{h}\s*$", text.replace("\f", "\n"), re.M)]
    missing = [h for h in REQUIRED + (["PROJECTS"] if is_full else []) if h not in headings]
    if missing:
        hard.append("missing headings: " + ", ".join(missing))
    else:
        struct += 3
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    phone = re.search(r"\+\d[\d -]{9,}", text)
    if not email:
        hard.append("no email found")
    else:
        struct += 3
    if not phone:
        hard.append("no phone found")
    else:
        struct += 2
    struct += 2 if re.search(r"pakistan", low) else 0
    li = re.search(r"linkedin\.com/in/\S+", low)
    gh = re.search(r"(?<![\w/])github\.com/\w[\w-]*", low)
    struct += (2 if li else 0) + (2 if gh else 0)
    if not li:
        warn.append("no linkedin.com/in/... text")
    if not gh:
        warn.append("no github.com/... text")
    ranges = DATE_RANGE.findall(text)
    # every date-looking range should use the Mon YYYY format
    rest = DATE_RANGE.sub("", text)
    loose = re.findall(r"\b\d{4}\s*[–-]\s*(?:\d{4}|Present)\b", rest)
    if len(ranges) >= 5:
        struct += 1
    else:
        warn.append(f"only {len(ranges)} 'Mon YYYY – Mon YYYY' ranges found")
    # one year-only range is expected (the degree); more means mixed formats
    if len(loose) > 1:
        warn.append("inconsistent date format: " + ", ".join(loose))

    # --- keywords (30) ---
    total = sum(w for _, w, _ in KEYWORDS)
    got = sum(w for _, w, alts in KEYWORDS if any(a in low for a in alts))
    kw_missing = [l for l, _, alts in KEYWORDS if not any(a in low for a in alts)]
    kw = round(30 * got / total, 1)

    # --- content (25) ---
    bullets = [l.strip() for l in lines if l.strip().startswith("•")]
    with_num = [b for b in bullets if re.search(r"\d", b)]
    pct = len(with_num) / len(bullets) if bullets else 0
    verbs = collections.Counter(b.lstrip("• ").split()[0] for b in bullets if b.lstrip("• ").split())
    repeats = {v: n for v, n in verbs.items() if n > 2}
    content = max(0.0, 25 * min(1.0, pct / 0.5) - min(3.0, 0.5 * sum(n - 2 for n in repeats.values())))
    content = round(content, 1)
    if pct < 0.5:
        warn.append(f"only {round(100 * pct)}% of bullets contain a number (aim for 50%+)")
    if repeats:
        warn.append("overused lead verbs: " + ", ".join(f"{v} x{n}" for v, n in repeats.items()))

    score = round(pars + struct + kw + content, 1)
    return dict(path=path, text=text, pages=pages, score=score, hard=hard, warn=warn,
                parts=[("Parseability", pars, 30), ("Contact & structure", struct, 15),
                       ("Keywords", kw, 30), ("Content", content, 25)],
                kw_missing=kw_missing, bullets=len(bullets), with_num=len(with_num))


def main(paths):
    results = [check(p) for p in paths]
    md = ["## ATS check", "", "| File | Pages | Score | Hard failures |", "|---|---|---|---|"]
    failed = False
    for r in results:
        name = os.path.basename(r["path"])
        print(f"\n===== {name}  |  pages: {r['pages']}  |  score: {r['score']}/100 =====")
        for label, got, mx in r["parts"]:
            print(f"  {label:<22}{got:>5} / {mx}")
        print(f"  bullets with a number: {r['with_num']}/{r['bullets']}")
        print("  keywords missing: " + (", ".join(r["kw_missing"]) or "none"))
        for w in r["warn"]:
            print("  WARN:", w)
        for h in r["hard"]:
            print("  FAIL:", h)
        failed = failed or bool(r["hard"])
        md.append(f"| {name} | {r['pages']} | **{r['score']}/100** | {'; '.join(r['hard']) or 'none'} |")
    for r in results:
        md += ["", f"### {os.path.basename(r['path'])}", "", "| Area | Score |", "|---|---|"]
        md += [f"| {l} | {g} / {m} |" for l, g, m in r["parts"]]
        md += ["", "Keywords missing: " + (", ".join(r["kw_missing"]) or "none")]
        md += [f"- warning: {w}" for w in r["warn"]]
        md += ["", "<details><summary>Extracted text (pdftotext -layout)</summary>", "", "```", r["text"], "```", "</details>"]
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
    print("\nRESULT:", "FAIL (hard failures above)" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
