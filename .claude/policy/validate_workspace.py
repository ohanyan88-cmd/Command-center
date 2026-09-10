# -*- coding: utf-8 -*-
"""Workspace validator — inspects the ACTUAL filesystem against workspace_policy.json and exits non-zero on violations.

  python .claude/policy/validate_workspace.py [--root PATH] [--json] [--quiet]
  python .claude/policy/validate_workspace.py --check-path <path> [--root PATH]     # single target (used by workspace_guard.py)

The policy file itself is validated first (structure + regex compilation); a corrupt policy fails closed.
Unknown top-level entries fail closed. All functions are importable (the guard and tests reuse them — no duplicate rule sets)."""
import sys, os, re, json, pathlib, fnmatch, argparse
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parent.parent
POLICY_PATH = HERE / "workspace_policy.json"

class PolicyError(Exception): pass

# ───────────────────────── policy ─────────────────────────
REQUIRED_TOP = ["policy_version", "naming", "reserved_technical_names", "root", "canonical_files", "directories", "generated_exclusions", "semantics", "links"]

def load_policy(path=POLICY_PATH):
    try: pol = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e: raise PolicyError(f"policy unreadable: {type(e).__name__}: {e}")
    problems = validate_policy(pol)
    if problems: raise PolicyError("policy invalid: " + "; ".join(problems))
    return pol

def validate_policy(pol):
    p = []
    if not isinstance(pol, dict): return ["policy is not an object"]
    for k in REQUIRED_TOP:
        if k not in pol: p.append(f"missing section {k}")
    if p: return p
    for key in ("business_filename_regex", "business_folder_regex", "ordered_top_level_regex", "python_module_regex", "technical_filename_regex", "date_regex", "version_regex"):
        try: re.compile(pol["naming"][key])
        except (KeyError, re.error) as e: p.append(f"naming.{key}: {e}")
    for pat in pol["naming"].get("forbidden_patterns", []):
        try: re.compile(pat)
        except re.error as e: p.append(f"forbidden_pattern {pat!r}: {e}")
    root = pol["root"]
    for k in ("allowed_files", "required_files", "allowed_dirs", "required_dirs"):
        if not isinstance(root.get(k), list): p.append(f"root.{k} must be a list")
    if root.get("unknown_entries") != "fail": p.append("root.unknown_entries must be 'fail' (fail closed)")
    if not set(root.get("required_files", [])) <= set(root.get("allowed_files", [])): p.append("root.required_files not subset of allowed_files")
    if not set(root.get("required_dirs", [])) <= set(root.get("allowed_dirs", [])): p.append("root.required_dirs not subset of allowed_dirs")
    for d in root.get("required_dirs", []):
        if d not in pol["directories"]: p.append(f"required dir {d} has no directory contract")
    need = {"kind", "purpose"}
    for name, d in pol["directories"].items():
        if not need <= set(d): p.append(f"directories.{name}: missing {need - set(d)}")
        for sub in d.get("fixed_subdirs", []):
            rx = pol["naming"]["technical_filename_regex"] if name.startswith(".claude") else pol["naming"]["business_folder_regex"]   # technical subtree vs business tree
            if not re.match(rx, sub) and not sub.startswith("."): p.append(f"directories.{name}: fixed_subdir {sub} violates folder naming")
    return p

# ───────────────────────── naming checks (single source of rules) ─────────────────────────
def _rx(pol, key): return re.compile(pol["naming"][key])

def check_business_name(name, pol, is_dir=False):
    """Returns list of violations for a business-facing file/folder name."""
    v = []; n = pol["naming"]
    stem = name if is_dir else name.rsplit(".", 1)[0]
    for pat in n["forbidden_patterns"]:
        if re.search(pat, name): v.append(f"forbidden pattern {pat!r}")
    for w in n["forbidden_words"]:
        if re.search(rf"(^|[-_. ]){re.escape(w)}([-_. ]|$)", stem, re.I): v.append(f"forbidden word '{w}'")
    rx = _rx(pol, "business_folder_regex" if is_dir else "business_filename_regex")
    if not rx.match(name): v.append("does not match business naming (First-word-hyphenated[-vN.N][-YYYY-MM-DD].ext)")
    m = re.search(r"-(\d{4}-\d{2}-\d{2})", stem)
    if m:
        y, mo, d = map(int, m.group(1).split("-"))
        if not (2000 <= y <= 2100 and 1 <= mo <= 12 and 1 <= d <= 31): v.append("invalid date")
        if re.search(r"-\d{4}-\d{2}-\d{2}-v\d", stem): v.append("version must come before date")
    if re.search(r"-v\d+(\.\d+){2,}", stem): v.append("version must be vN or vN.N")
    if not is_dir and "." in name and name.rsplit(".", 1)[1] != name.rsplit(".", 1)[1].lower(): v.append("extension must be lowercase")
    return sorted(set(v))

def check_technical_name(name, pol, python=False):
    if python: return [] if _rx(pol, "python_module_regex").match(name) else ["python module must be lowercase snake_case.py"]
    return [] if _rx(pol, "technical_filename_regex").match(name) else ["technical filename: ASCII letters/digits/._- only"]

def _is_ignored(name, pol):
    g = pol["generated_exclusions"]
    return name in g["ignored_dir_names"] or any(fnmatch.fnmatch(name, pat) for pat in g["ignored_file_globs"])

def _is_garbage(name, pol):
    return any(fnmatch.fnmatch(name.lower(), pat) for pat in pol["generated_exclusions"]["garbage_globs"])

def _rel(root, p): return pathlib.Path(p).resolve().relative_to(pathlib.Path(root).resolve()).as_posix()

def _area(rel):
    parts = rel.split("/")
    if parts[0] == ".claude" and len(parts) > 1: return ".claude/" + parts[1]
    return parts[0]

def _matches_any(name, patterns): return any(re.search(p, name) for p in patterns)

# ───────────────────────── single-path check (guard + validator share it) ─────────────────────────
def check_path(path, pol, root=DEFAULT_ROOT, is_dir=None):
    """Violations for ONE prospective or existing path inside the workspace. Used by workspace_guard before a write."""
    root = pathlib.Path(root).resolve(); p = pathlib.Path(path)
    p = (root / p) if not p.is_absolute() else p
    try: rel = p.resolve().relative_to(root).as_posix()
    except ValueError: return []                                  # outside the workspace: not this policy's business
    parts = rel.split("/"); name = parts[-1]; v = []
    if is_dir is None: is_dir = p.is_dir()
    if _is_ignored(name, pol) and name != "desktop.ini": return []
    if name in pol["reserved_technical_names"]["anywhere_files"]: return []
    if _is_garbage(name, pol): v.append(f"{rel}: generated garbage name")
    top = parts[0]; rt = pol["root"]
    if len(parts) == 1:
        if is_dir:
            if top not in rt["allowed_dirs"]: v.append(f"{rel}: unknown top-level directory (allowed: {rt['allowed_dirs']})")
        elif name not in rt["allowed_files"]: v.append(f"{rel}: unknown top-level file (allowed: {rt['allowed_files']})")
        return v
    if top not in rt["allowed_dirs"]: v.append(f"{rel}: under unknown top-level directory {top}"); return v
    area = _area(rel); dc = pol["directories"].get(area) or pol["directories"].get(top, {})
    kind = dc.get("kind", "")
    sem = pol["semantics"]
    # semantic placement
    if not is_dir:
        if _matches_any(name, sem["code_markers"]["patterns"]) and not any(rel.startswith(a + "/") for a in sem["code_markers"]["must_live_under"]):
            v.append(f"{rel}: code may only live under {sem['code_markers']['must_live_under']}")
        if _matches_any(name, sem["runtime_markers"]["patterns"]) and not any(rel.startswith(a + "/") for a in sem["runtime_markers"]["must_live_under"]):
            v.append(f"{rel}: runtime/state file may only live under {sem['runtime_markers']['must_live_under']}")
        if _matches_any(name, sem["test_markers"]["patterns"]) and not any(rel.startswith(a + "/") for a in sem["test_markers"]["must_live_under"]):
            v.append(f"{rel}: tests may only live under {sem['test_markers']['must_live_under']}")
        if _matches_any(name, sem["source_markers"]["patterns"]) and not (rel.startswith("04_Sources/") or rel.startswith("05_Archive/") or rel.startswith("00_Inbox/")):
            v.append(f"{rel}: raw source/media may only live under 04_Sources (or 05_Archive)")
    # area rules
    if top == "00_Inbox":
        if is_dir: v.append(f"{rel}: subdirectories are forbidden in 00_Inbox")
        return v
    if top in ("01_Active", "02_Reference", "04_Sources"):
        fixed = dc.get("fixed_subdirs", [])
        if len(parts) == 2 and is_dir and name not in fixed: v.append(f"{rel}: only fixed subdomains allowed in {top}: {fixed}")
        if len(parts) == 2 and not is_dir: v.append(f"{rel}: files must live inside a subdomain of {top} {fixed}")
        if len(parts) >= 3 and parts[1] not in fixed: v.append(f"{rel}: unknown subdomain {parts[1]} (allowed {fixed})")
        if top == "04_Sources":
            if len(parts) == 3 and is_dir and not re.match(dc["source_naming"]["folder_regex"], name): v.append(f"{rel}: source folder must be Name-YYYY-MM-DD[-suffix]")
            if not is_dir and not (_rx(pol, "technical_filename_regex").match(name) or not check_business_name(name, pol)): v.append(f"{rel}: source file name must be technical (no spaces/parentheses) or business form")
            if not is_dir and (_matches_any(name, sem["code_markers"]["patterns"]) or _matches_any(name, sem["runtime_markers"]["patterns"])): v.append(f"{rel}: runtime code inside 04_Sources")
            return v
        if len(parts) >= 3 and top in ("01_Active", "02_Reference"):
            if is_dir and len(parts) >= 3: v.append(f"{rel}: arbitrary subdirectories are forbidden in {top}")
            if not is_dir:
                v += [f"{rel}: {x}" for x in check_business_name(name, pol)]
                ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                if dc.get("allowed_extensions") != "*" and ext not in dc.get("allowed_extensions", []): v.append(f"{rel}: extension .{ext} not allowed in {top}")
        return v
    if top in ("03_Completed", "05_Archive"):
        if is_dir: v += [f"{rel}: {x}" for x in check_business_name(name, pol, is_dir=True)]
        else:
            ok_business = not check_business_name(name, pol)
            ok_tech = top == "05_Archive" and not check_technical_name(name, pol) and not re.search(r"\s|[()]", name)
            if not (ok_business or ok_tech): v += [f"{rel}: {x}" for x in check_business_name(name, pol)]
            if top == "03_Completed":
                ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                if ext not in dc.get("allowed_extensions", []): v.append(f"{rel}: extension .{ext} not allowed in 03_Completed")
        return v
    if top == ".claude":
        if len(parts) == 2:
            fixed = pol["directories"][".claude"].get("fixed_subdirs", [])
            if is_dir and name not in fixed and name not in ("__pycache__",): v.append(f"{rel}: unknown .claude subdirectory (allowed {fixed})")
            if not is_dir and name not in pol["directories"][".claude"].get("allowed_files", []): v.append(f"{rel}: unknown file in .claude root (allowed {pol['directories']['.claude'].get('allowed_files')})")
            return v
        sub = pol["directories"].get(area, {})
        if is_dir:
            if sub.get("subdirs") == "forbidden" and name not in sub.get("generated_ok", []): v.append(f"{rel}: subdirectories forbidden in {area}")
            if area == ".claude/skills" and name not in sub.get("allowed_subdirs", []): v.append(f"{rel}: subdirectory not allowed in .claude/skills (allowed {sub.get('allowed_subdirs')})")
            return v
        for g in sub.get("forbidden_globs", []):
            if fnmatch.fnmatch(name, g): v.append(f"{rel}: '{g}' is forbidden in {area}")
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        ae = sub.get("allowed_extensions", "*")
        if ae != "*" and ext not in ae and len(parts) == 3: v.append(f"{rel}: extension .{ext} not allowed in {area}")
        rule = sub.get("naming_rule", "technical")
        if rule == "python_module" and name.endswith(".py"): v += [f"{rel}: {x}" for x in check_technical_name(name, pol, python=True)]
        elif rule == "business" and len(parts) == 3: v += [f"{rel}: {x}" for x in check_business_name(name, pol)]
        elif rule in ("technical", "python_module"):
            if name.endswith(".py"): v += [f"{rel}: {x}" for x in check_technical_name(name, pol, python=True)]
            else: v += [f"{rel}: {x}" for x in check_technical_name(name, pol)]
        return v
    return v

# ───────────────────────── whole-tree validation ─────────────────────────
def validate_tree(root=DEFAULT_ROOT, pol=None, policy_path=POLICY_PATH):
    root = pathlib.Path(root).resolve(); problems = []
    try: pol = pol or load_policy(policy_path)
    except PolicyError as e: return [f"POLICY: {e}"]
    rt = pol["root"]
    entries = list(root.iterdir())
    names = {e.name for e in entries}
    for f in rt["required_files"]:
        if f not in names: problems.append(f"missing required root file {f}")
    for d in rt["required_dirs"]:
        if not (root / d).is_dir(): problems.append(f"missing required root directory {d}")
    for area, dc in pol["directories"].items():
        base = root / area
        if dc.get("required") and not base.is_dir(): problems.append(f"missing required directory {area}"); continue
        if not base.is_dir(): continue
        for sub in dc.get("fixed_subdirs", []):
            if not (base / sub).is_dir(): problems.append(f"missing fixed subdirectory {area}/{sub}")
        for rf in dc.get("required_files", []):
            if not (base / rf).exists(): problems.append(f"missing required file {area}/{rf}")
    for cf, spec in pol["canonical_files"].items():
        if not (root / cf).exists() and cf in rt["required_files"] + ["00_Inbox/Input.md"]: problems.append(f"missing canonical file {cf}")
    # walk
    for dirpath, dirnames, filenames in os.walk(root):
        dp = pathlib.Path(dirpath); rel_dir = _rel(root, dp) if dp != root else ""
        dirnames[:] = [d for d in dirnames if d not in pol["generated_exclusions"]["ignored_dir_names"] or d == "__pycache__"]
        for d in list(dirnames):
            rel = f"{rel_dir}/{d}" if rel_dir else d
            if d == "__pycache__":
                if not any(rel_dir == a for a in pol["generated_exclusions"]["pycache_allowed_under"]): problems.append(f"{rel}: __pycache__ outside allowed runtime directories")
                dirnames.remove(d); continue
            problems += check_path(dp / d, pol, root, is_dir=True)
        for f in filenames:
            rel = f"{rel_dir}/{f}" if rel_dir else f
            if _is_ignored(f, pol) and f != "desktop.ini": continue
            problems += check_path(dp / f, pol, root, is_dir=False)
    # inbox invariant
    inbox = root / "00_Inbox"
    if inbox.is_dir():
        extra = [e.name for e in inbox.iterdir() if e.name != "Input.md" and not _is_ignored(e.name, pol)]
        if extra: problems.append(f"00_Inbox not in steady state: unclassified items {extra}")
    # single canonical artifacts
    for cf, spec in pol["canonical_files"].items():
        if not spec.get("single_canonical"): continue
        base = pathlib.Path(cf).name
        for g in spec.get("duplicates_forbidden_globs", []) + [f"**/{base}"]:
            for hit in root.glob(g):
                if hit.is_dir(): continue
                rel = _rel(root, hit)
                if rel == cf: continue
                if any(rel.startswith(a + "/") for a in spec.get("duplicates_allowed_under", [])): continue
                if any(part in pol["generated_exclusions"]["ignored_dir_names"] for part in rel.split("/")): continue
                problems.append(f"duplicate canonical artifact for {cf}: {rel}")
    # reference vs completed: same base document in both
    ref = {p.name: p for p in (root / "02_Reference").rglob("*") if p.is_file()} if (root / "02_Reference").is_dir() else {}
    comp = {p.name for p in (root / "03_Completed").rglob("*") if p.is_file()} if (root / "03_Completed").is_dir() else set()
    for n in ref.keys() & comp: problems.append(f"{n}: exists in both 02_Reference and 03_Completed (one canonical location)")
    # markdown links
    for md in pol["links"]["check_markdown_links_in"]:
        p = root / md
        if not p.exists(): continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", txt):
            target = m.group(1)
            if re.match(r"^[a-z]+:", target): continue
            t = (p.parent / target)
            if not t.exists(): problems.append(f"{md}: broken link → {target}")
    # README ↔ policy consistency (structure block)
    readme = root / "README.md"
    if readme.exists():
        txt = readme.read_text(encoding="utf-8", errors="replace")
        for d in rt["required_dirs"]:
            if d not in txt: problems.append(f"README.md does not mention required directory {d}")
        for f in rt["required_files"]:
            if f not in txt: problems.append(f"README.md does not mention required file {f}")
    problems += check_identity(root, pol)
    return sorted(set(problems))

def check_identity(root, pol):
    """Identity/configuration drift: active files must agree on workspace + agent names; stale canonical names fail."""
    root = pathlib.Path(root); problems = []
    ident = pol.get("identity"); enf = pol.get("identity_enforcement")
    if not ident or not enf: return ["POLICY: identity / identity_enforcement sections missing"]
    for k in ("name", "role", "workspace", "owner"):
        if not ident.get(k): problems.append(f"POLICY: identity.{k} missing")
    if ident.get("workspace") != pol.get("workspace_name"): problems.append("POLICY: identity.workspace disagrees with workspace_name")
    markers = re.compile("|".join(re.escape(m) for m in enf["historical_line_markers"]), re.I)
    stale = [(p, re.compile(re.escape(p))) for p in enf["stale_patterns"]]
    for rel in enf["active_files"]:
        p = root / rel
        if not p.exists(): continue
        try: txt = p.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        for need in enf.get("must_mention", {}).get(rel, []):
            if need not in txt: problems.append(f"{rel}: must mention canonical identity {need!r}")
        for i, line in enumerate(txt.splitlines(), 1):
            if markers.search(line): continue
            if rel == ".claude/policy/validate_workspace.py" or rel.endswith("workspace_policy.json"): continue
            for pat, rx in stale:
                if rx.search(line): problems.append(f"{rel}:{i}: stale canonical reference {pat!r} (add a historical marker or update)")
    # settings.json hooks must point at existing scripts
    settings = root / ".claude" / "settings.json"
    if settings.exists():
        try:
            cfg = json.loads(settings.read_text(encoding="utf-8"))
            for ev, groups in cfg.get("hooks", {}).items():
                for g in groups:
                    for h in g.get("hooks", []):
                        m = re.search(r"\.claude/[\w/.-]+\.py", h.get("command", ""))
                        if m and not (root / m.group(0)).exists(): problems.append(f"settings.json: {ev} hook references missing script {m.group(0)}")
        except json.JSONDecodeError: problems.append("settings.json: invalid JSON")
    return problems

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default=str(DEFAULT_ROOT)); ap.add_argument("--policy", default=str(POLICY_PATH))
    ap.add_argument("--check-path"); ap.add_argument("--json", action="store_true"); ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    try: pol = load_policy(a.policy)
    except PolicyError as e:
        print(json.dumps({"ok": False, "problems": [str(e)]}) if a.json else f"✗ {e}"); return 2
    if a.check_path:
        probs = check_path(a.check_path, pol, a.root)
    else:
        probs = validate_tree(a.root, pol, a.policy)
    if a.json: print(json.dumps({"ok": not probs, "problems": probs}, ensure_ascii=False))
    elif not a.quiet:
        print(f"workspace: {a.root}\npolicy {pol['policy_version']} · {'OK — contract satisfied' if not probs else str(len(probs)) + ' violation(s)'}")
        for p in probs: print("  ✗", p)
    return 0 if not probs else 1

if __name__ == "__main__":
    sys.exit(main())
