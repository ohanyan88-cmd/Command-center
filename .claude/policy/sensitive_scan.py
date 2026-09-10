# -*- coding: utf-8 -*-
"""SENSITIVE-DATA BOUNDARY SCANNER — mechanical enforcement of .claude/policy/data_classification.json.

  python .claude/policy/sensitive_scan.py --staged                 # git index (pre-commit hook)
  python .claude/policy/sensitive_scan.py --range <base>..<head>   # commits about to be pushed (pre-push hook)
  python .claude/policy/sensitive_scan.py --paths a b c            # working-tree files (validator / certification)
  python .claude/policy/sensitive_scan.py --install-hooks          # writes .git/hooks/pre-commit + pre-push (idempotent)

A file is BLOCKED when its path matches a CONFIDENTIAL/RESTRICTED path rule, its content matches a content rule, or it
contains a person name known from the local sensitive overlay (never stored here). Allow rules are narrow and explicit.
Exit 1 on any finding (fail closed). Applies regardless of repository visibility."""
import sys, os, re, json, pathlib, subprocess, fnmatch
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "runtime")); import python_runtime; python_runtime.ensure()
POLICY = HERE / "data_classification.json"
OVERLAY_JSON = ROOT / ".claude" / "business" / "overlay.json"
TEXT_EXT = {".py", ".json", ".md", ".txt", ".sh", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".lock", ".csv", ".gitignore", ".gitattributes", ""}

def load_policy(path=POLICY):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))

def overlay_names(overlay_path=OVERLAY_JSON):
    """Person names from the local overlay (if present) — the list itself never leaves this machine."""
    try: ov = json.loads(pathlib.Path(overlay_path).read_text(encoding="utf-8"))
    except (OSError, ValueError): return []
    names = []
    for p in ov.get("persons", []):
        for n in [p.get("name")] + list(p.get("aliases", [])):
            if n and len(n) >= 3: names.append(n)
    return sorted(set(names), key=len, reverse=True)

def classify_path(rel, pol):
    rel = rel.replace("\\", "/")
    for r in pol["path_rules"]:
        if re.search(r["pattern"], rel): return r["class"], r["reason"]
    return "PUBLIC", "no path rule"

def _allowed_path(rel, pol):
    return any(re.search(p, rel.replace("\\", "/")) for a in pol.get("allow_rules", []) for p in a.get("paths", []))

def scan_content(rel, text, pol, names=()):
    """Return list of findings {rule, class, line, sample}."""
    out = []
    if _allowed_path(rel, pol): return out
    literals = {l for a in pol.get("allow_rules", []) for l in a.get("literals", [])}
    for i, line in enumerate(text.splitlines(), 1):
        for r in pol["content_rules"]:
            m = re.search(r["pattern"], line)
            if m: out.append({"rule": r["id"], "class": r["class"], "line": i, "sample": line.strip()[:80]})
        for n in names:
            if n in literals: continue
            if n in line: out.append({"rule": "person_name_from_overlay", "class": "CONFIDENTIAL", "line": i, "sample": "<name withheld>"})
    return out

def scan_blob(rel, data, pol, names=()):
    """Findings for one file (path + content)."""
    findings = []
    cls, why = classify_path(rel, pol)
    if cls in ("CONFIDENTIAL", "RESTRICTED") and not _allowed_path(rel, pol):
        findings.append({"rule": "path_rule", "class": cls, "line": 0, "sample": why})
    ext = pathlib.Path(rel).suffix.lower()
    if ext in TEXT_EXT and data is not None:
        try: text = data.decode("utf-8")
        except UnicodeDecodeError: return findings
        findings += scan_content(rel, text, pol, names)
    return findings

def scan_paths(paths, root=ROOT, pol=None, names=None):
    pol = pol or load_policy(); names = overlay_names() if names is None else names; report = {}
    for p in paths:
        p = pathlib.Path(p); ap = p if p.is_absolute() else root / p
        if not ap.is_file(): continue
        rel = ap.resolve().relative_to(pathlib.Path(root).resolve()).as_posix()
        f = scan_blob(rel, ap.read_bytes(), pol, names)
        if f: report[rel] = f
    return report

def _git(args, cwd=ROOT):
    return subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")

def scan_staged(root=ROOT, pol=None, names=None):
    pol = pol or load_policy(); names = overlay_names() if names is None else names; report = {}
    r = _git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], root)
    for rel in [l.strip() for l in r.stdout.splitlines() if l.strip()]:
        blob = subprocess.run(["git", "show", f":{rel}"], cwd=str(root), capture_output=True).stdout
        f = scan_blob(rel, blob, pol, names)
        if f: report[rel] = f
    return report

def scan_range(rng, root=ROOT, pol=None, names=None):
    pol = pol or load_policy(); names = overlay_names() if names is None else names; report = {}
    r = _git(["diff", "--name-only", "--diff-filter=ACMR", rng], root)
    head = rng.split("..")[-1] or "HEAD"
    for rel in [l.strip() for l in r.stdout.splitlines() if l.strip()]:
        blob = subprocess.run(["git", "show", f"{head}:{rel}"], cwd=str(root), capture_output=True)
        if blob.returncode != 0: continue
        f = scan_blob(rel, blob.stdout, pol, names)
        if f: report[rel] = f
    return report

HOOK_PRE_COMMIT = """#!/usr/bin/env bash
# Command-center boundary: CONFIDENTIAL/RESTRICTED data never enters the repository (installed by sensitive_scan.py --install-hooks)
R="$(git rev-parse --show-toplevel)"
P="$R/.venv/Scripts/python.exe"; [ -x "$P" ] || P="$R/.venv/bin/python"; [ -x "$P" ] || P=python
exec "$P" "$R/.claude/policy/sensitive_scan.py" --staged
"""
HOOK_PRE_PUSH = """#!/usr/bin/env bash
# Command-center boundary (pre-push): scan every commit about to leave this machine
R="$(git rev-parse --show-toplevel)"
P="$R/.venv/Scripts/python.exe"; [ -x "$P" ] || P="$R/.venv/bin/python"; [ -x "$P" ] || P=python
rc=0
while read local_ref local_sha remote_ref remote_sha; do
  [ -z "$local_sha" ] && continue
  if [ "$remote_sha" = "0000000000000000000000000000000000000000" ] || [ -z "$remote_sha" ]; then range="$local_sha"; else range="$remote_sha..$local_sha"; fi
  "$P" "$R/.claude/policy/sensitive_scan.py" --range "$range" || rc=1
done
exit $rc
"""

def install_hooks(root=ROOT):
    hooks = pathlib.Path(root) / ".git" / "hooks"
    if not hooks.is_dir(): return False
    for name, body in (("pre-commit", HOOK_PRE_COMMIT), ("pre-push", HOOK_PRE_PUSH)):
        p = hooks / name
        if not p.exists() or p.read_text(encoding="utf-8", errors="replace") != body:
            p.write_text(body, encoding="utf-8", newline="\n")
        try: p.chmod(p.stat().st_mode | 0o111)
        except OSError: pass
    return True

def hooks_installed(root=ROOT):
    hooks = pathlib.Path(root) / ".git" / "hooks"
    return all((hooks / n).exists() and "sensitive_scan.py" in (hooks / n).read_text(encoding="utf-8", errors="replace") for n in ("pre-commit", "pre-push"))

def report(rep, title):
    if not rep: print(f"✓ boundary clean — {title}"); return 0
    print(f"⛔ BOUNDARY VIOLATION — {title}: {len(rep)} file(s) carry CONFIDENTIAL/RESTRICTED data")
    for rel, fs in rep.items():
        for f in fs[:5]: print(f"   {rel}:{f['line']}  [{f['class']}] {f['rule']}  {f['sample']}")
    print("   → keep it in the sensitive overlay / local registers; never in the repository (see .claude/policy/data_classification.json)")
    return 1

def main(argv):
    if not argv: print(__doc__); return 2
    if argv[0] == "--install-hooks": print("hooks installed" if install_hooks() else "no .git/hooks"); return 0
    if argv[0] == "--staged": return report(scan_staged(), "staged index")
    if argv[0] == "--range" and len(argv) > 1:
        rng = argv[1] if ".." in argv[1] else f"{argv[1]}~1..{argv[1]}"
        try: return report(scan_range(rng), f"range {rng}")
        except Exception as e: print(f"⛔ scan failed ({e}) — fail closed"); return 1
    if argv[0] == "--paths": return report(scan_paths(argv[1:]), "paths")
    print(__doc__); return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
