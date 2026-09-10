# -*- coding: utf-8 -*-
"""Workspace contract tests — drive the REAL validator (.claude/policy/validate_workspace.py) and the REAL guard hook
(.claude/hooks/workspace_guard.py) against synthetic trees built from the canonical policy. Nothing touches the live workspace."""
import unittest, json, pathlib, tempfile, shutil, subprocess, sys, os, copy
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
POLICY_DIR = ROOT / ".claude" / "policy"
sys.path.insert(0, str(POLICY_DIR)); sys.path.insert(0, str(HERE))
import validate_workspace as vw
from testing import covers

POLICY = json.loads((POLICY_DIR / "workspace_policy.json").read_text(encoding="utf-8"))
GUARD = ROOT / ".claude" / "hooks" / "workspace_guard.py"

def clean_tree():
    """Minimal tree that satisfies the contract (files are empty placeholders)."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="ws_")); pol = POLICY
    ident_line = " ".join(sorted({tok for toks in pol["identity_enforcement"]["must_mention"].values() for tok in toks})) + "\n"
    for f in pol["root"]["required_files"]: (d / f).write_text("# x\n" + ident_line, encoding="utf-8")
    (d / "README.md").write_text("\n".join(pol["root"]["required_dirs"] + pol["root"]["required_files"]) + "\n" + ident_line, encoding="utf-8")
    for dd in pol["root"]["required_dirs"]: (d / dd).mkdir(parents=True, exist_ok=True)
    for area, dc in pol["directories"].items():
        base = d / area; base.mkdir(parents=True, exist_ok=True)
        for sub in dc.get("fixed_subdirs", []): (base / sub).mkdir(exist_ok=True)
        for rf in dc.get("required_files", []): (base / rf).write_text(ident_line if rf.endswith(".md") else "", encoding="utf-8")
    (d / "00_Inbox" / "Input.md").write_text("# inbox\n", encoding="utf-8")
    return d

def problems(d): return vw.validate_tree(d, POLICY)

class W01_Tree(unittest.TestCase):
    @covers("source_verification", kinds=("unit",))
    def test_valid_clean_tree_passes(self):
        d = clean_tree(); self.assertEqual(problems(d), [])
        (d / "01_Active/Sales/Sales-strategy-v1.1-2026-09-10.docx").write_bytes(b""); (d / "02_Reference/People/Staffing-plan-2026-09-07.xlsx").write_bytes(b"")
        (d / "04_Sources/Whatsapp/Principal-2026-09-09").mkdir(); (d / "04_Sources/Whatsapp/Principal-2026-09-09/chat.txt").write_text("", encoding="utf-8")
        (d / "05_Archive/Drafts-2026-09-09").mkdir(); (d / "05_Archive/Drafts-2026-09-09/run.py").write_text("", encoding="utf-8")
        self.assertEqual(problems(d), [])
    def test_unknown_root_file_fails(self):
        d = clean_tree(); (d / "Notes.md").write_text("", encoding="utf-8"); self.assertTrue(any("unknown top-level file" in p for p in problems(d)))
    def test_unknown_root_folder_fails(self):
        d = clean_tree(); (d / "06_Misc").mkdir(); self.assertTrue(any("unknown top-level directory" in p for p in problems(d)))
    def test_armenian_business_filename_fails(self):
        d = clean_tree(); (d / "01_Active/Sales/Ռազմավարություն-2026-09-10.docx").write_bytes(b""); self.assertTrue(any("forbidden pattern" in p for p in problems(d)))
    def test_spaces_fail(self):
        d = clean_tree(); (d / "01_Active/Sales/Sales strategy.docx").write_bytes(b""); self.assertTrue(any("Sales strategy.docx" in p for p in problems(d)))
    def test_parenthesized_duplicate_fails(self):
        d = clean_tree(); (d / "01_Active/Sales/Save-list (2).xlsx").write_bytes(b""); self.assertTrue(any("(2)" in p or "forbidden pattern" in p for p in problems(d)))
    def test_final2_fails(self):
        d = clean_tree(); (d / "01_Active/Sales/Sales-strategy-final2.docx").write_bytes(b""); self.assertTrue(any("forbidden word" in p for p in problems(d)))
    def test_wrong_date_format_fails(self):
        d = clean_tree(); (d / "01_Active/Sales/Sales-strategy-10.09.2026.docx").write_bytes(b""); self.assertTrue(any("Sales-strategy-10.09.2026" in p for p in problems(d)))
        (d / "01_Active/Sales/Sales-strategy-2026_09_10.docx").write_bytes(b""); self.assertTrue(any("2026_09_10" in p for p in problems(d)))
    def test_wrong_version_format_fails(self):
        d = clean_tree(); (d / "01_Active/Systems/Billing-roadmap-v2.0.1-2026-09-07.docx").write_bytes(b""); self.assertTrue(any("v2.0.1" in p for p in problems(d)))
        (d / "01_Active/Systems/Billing-roadmap-2026-09-07-v2.docx").write_bytes(b""); self.assertTrue(any("version must come before date" in p for p in problems(d)))
    def test_wrong_extension_placement_fails(self):
        d = clean_tree(); (d / "01_Active/Sales/Sales-strategy.DOCX").write_bytes(b""); self.assertTrue(any("Sales-strategy.DOCX" in p for p in problems(d)))
        (d / "02_Reference/Sales/Sales-plan-2026-09-10.py").write_text("", encoding="utf-8"); self.assertTrue(any("Sales-plan-2026-09-10.py" in p for p in problems(d)))
    def test_raw_whatsapp_source_in_active_fails(self):
        d = clean_tree(); (d / "01_Active/Operations/chat.txt").write_text("", encoding="utf-8"); (d / "01_Active/Sales/Principal.zip").write_bytes(b"")
        pr = problems(d); self.assertTrue(any("chat.txt" in p and "04_Sources" in p for p in pr)); self.assertTrue(any("Principal.zip" in p for p in pr))
    def test_python_tool_inside_sources_fails(self):
        d = clean_tree(); (d / "04_Sources/Imports/helper.py").write_text("", encoding="utf-8"); self.assertTrue(any("helper.py" in p for p in problems(d)))
    def test_test_file_inside_skills_fails(self):
        d = clean_tree(); (d / ".claude/skills/test_engine.py").write_text("", encoding="utf-8"); self.assertTrue(any("test_engine.py" in p for p in problems(d)))
    def test_audit_log_inside_skills_fails(self):
        d = clean_tree(); (d / ".claude/skills/skill_audit.jsonl").write_text("", encoding="utf-8"); self.assertTrue(any("skill_audit.jsonl" in p and ".claude/skills" in p for p in problems(d)))
        (d / ".claude/skills/state").mkdir(); self.assertTrue(any(".claude/skills/state" in p for p in problems(d)))
    def test_missing_required_canonical_root_file_fails(self):
        d = clean_tree(); (d / "Tasks.xlsx").unlink(); self.assertTrue(any("missing required root file Tasks.xlsx" in p for p in problems(d)))
    def test_duplicate_canonical_task_register_fails(self):
        d = clean_tree(); (d / "01_Active/Operations/Tasks.xlsx").write_bytes(b""); self.assertTrue(any("duplicate canonical artifact for Tasks.xlsx" in p for p in problems(d)))
        (d / "03_Completed/Tasks-copy-2026-09-10.xlsx").write_bytes(b""); self.assertTrue(any("Tasks-copy" in p for p in problems(d)))
    def test_technical_reserved_filenames_allowed(self):
        d = clean_tree()
        for f in ("CLAUDE.md", "README.md", ".gitignore", ".gitattributes", "desktop.ini"): (d / f).write_text("Deputy Command-center\n" if f != "README.md" else (d / "README.md").read_text(encoding="utf-8"), encoding="utf-8")
        (d / ".claude/settings.json").write_text("{}", encoding="utf-8"); self.assertEqual(problems(d), [])
    def test_python_module_naming_exception_works(self):
        d = clean_tree(); (d / ".claude/tools/build_task_workbook.py").write_text("", encoding="utf-8"); self.assertEqual(problems(d), [])
        (d / ".claude/tools/Build-Task-Workbook.py").write_text("", encoding="utf-8"); self.assertTrue(any("snake_case" in p for p in problems(d)))
    def test_inbox_invariant(self):
        d = clean_tree(); (d / "00_Inbox/random.docx").write_bytes(b""); self.assertTrue(any("00_Inbox not in steady state" in p for p in problems(d)))
        (d / "00_Inbox/random.docx").unlink(); (d / "00_Inbox/sub").mkdir(); self.assertTrue(any("subdirectories are forbidden in 00_Inbox" in p for p in problems(d)))
    def test_reference_and_completed_semantics(self):
        d = clean_tree(); (d / "02_Reference/People/Staffing-plan-2026-09-07.xlsx").write_bytes(b""); (d / "03_Completed/Staffing-plan-2026-09-07.xlsx").write_bytes(b"")
        self.assertTrue(any("both 02_Reference and 03_Completed" in p for p in problems(d)))
        (d / "02_Reference/Sales/Sales-plan-draft2.docx").write_bytes(b""); self.assertTrue(any("draft2" in p for p in problems(d)))
    def test_arbitrary_subdirs_forbidden_in_active_and_reference(self):
        d = clean_tree(); (d / "01_Active/Sales/Misc").mkdir(); self.assertTrue(any("arbitrary subdirectories" in p for p in problems(d)))
        (d / "02_Reference/Marketing").mkdir(); self.assertTrue(any("only fixed subdomains" in p for p in problems(d)))
    def test_pycache_and_garbage(self):
        d = clean_tree(); (d / "01_Active/__pycache__").mkdir(); self.assertTrue(any("__pycache__ outside" in p for p in problems(d)))
        (d / "03_Completed/Report-2026-09-10.tmp").write_bytes(b""); self.assertTrue(any("garbage" in p for p in problems(d)))
    def test_broken_link_detected(self):
        d = clean_tree(); (d / "Journal.md").write_text("see [x](01_Active/Sales/Nope.docx)\n", encoding="utf-8"); self.assertTrue(any("broken link" in p for p in problems(d)))
    def test_readme_policy_consistency(self):
        d = clean_tree(); (d / "README.md").write_text("nothing\n", encoding="utf-8"); self.assertTrue(any("README.md does not mention" in p for p in problems(d)))
    def test_policy_corruption_fails_closed(self):
        bad = pathlib.Path(tempfile.mkdtemp()) / "workspace_policy.json"; bad.write_text("{not json", encoding="utf-8")
        with self.assertRaises(vw.PolicyError): vw.load_policy(bad)
        self.assertTrue(any("POLICY" in p for p in vw.validate_tree(clean_tree(), None, bad)))
        p2 = copy.deepcopy(POLICY); p2["root"]["unknown_entries"] = "allow"; self.assertTrue(vw.validate_policy(p2))
        p3 = copy.deepcopy(POLICY); p3["naming"]["business_filename_regex"] = "(["; self.assertTrue(vw.validate_policy(p3))
        rc = subprocess.run([sys.executable, str(POLICY_DIR / "validate_workspace.py"), "--policy", str(bad), "--root", str(clean_tree())], capture_output=True).returncode
        self.assertEqual(rc, 2)
    def test_cli_exit_codes(self):
        d = clean_tree()
        self.assertEqual(subprocess.run([sys.executable, str(POLICY_DIR / "validate_workspace.py"), "--root", str(d), "--quiet"]).returncode, 0)
        (d / "Junk.txt").write_text("", encoding="utf-8")
        self.assertEqual(subprocess.run([sys.executable, str(POLICY_DIR / "validate_workspace.py"), "--root", str(d), "--quiet"]).returncode, 1)

class W03_Identity(unittest.TestCase):
    def test_policy_is_the_single_identity_source(self):
        ident = POLICY["identity"]
        self.assertEqual(ident["name"], "Deputy"); self.assertEqual(ident["workspace"], "Command-center"); self.assertEqual(ident["workspace"], POLICY["workspace_name"])
        self.assertEqual(ident["owner"], "Gev"); self.assertIn("Chief of Staff", ident["role"])
        sys.path.insert(0, str(ROOT / ".claude" / "skills")); import engine
        self.assertEqual(engine.identity()["name"], "Deputy")
    def test_identity_drift_fails(self):
        d = clean_tree(); (d / "CLAUDE.md").write_text("Deputy · Command-center\ncanonical agent = Assistant\n", encoding="utf-8")
        self.assertTrue(any("stale canonical reference" in p and "CLAUDE.md" in p for p in problems(d)))
        (d / "README.md").write_text((d / "README.md").read_text(encoding="utf-8") + "\nworkspace = Sales-operations-control\n", encoding="utf-8")
        self.assertTrue(any("Sales-operations-control" in p for p in problems(d)))
        (d / "README.md").write_text("\n".join(POLICY["root"]["required_dirs"] + POLICY["root"]["required_files"]) + "\nagent Deputy in Command-center\n", encoding="utf-8")
        (d / "CLAUDE.md").write_text("Deputy · Command-center\nformerly: Daily check (historical)\n", encoding="utf-8")   # historical marker → allowed
        for f in (".claude/docs/Role.md", ".claude/docs/Job-description.md"): (d / f).write_text("Deputy\n", encoding="utf-8")
        self.assertEqual([p for p in problems(d) if "stale" in p or "must mention" in p], [])
    def test_missing_identity_mention_fails(self):
        d = clean_tree(); (d / "CLAUDE.md").write_text("no names here\n", encoding="utf-8")
        self.assertTrue(any("must mention canonical identity 'Deputy'" in p for p in problems(d)))
    def test_policy_without_identity_fails_closed(self):
        p2 = copy.deepcopy(POLICY); del p2["identity"]
        self.assertTrue(any("identity" in p for p in vw.check_identity(clean_tree(), p2)))

class W02_Guard(unittest.TestCase):
    def guard(self, ev, tool, inp, root):
        d = {"hook_event_name": ev, "session_id": "ws-test", "tool_name": tool, "tool_input": inp, "cwd": str(root)}
        p = subprocess.run([sys.executable, str(GUARD), ev], input=json.dumps(d), capture_output=True, text=True, encoding="utf-8", env={**os.environ, "WORKSPACE_ROOT": str(root)})
        dec = None
        for line in p.stdout.splitlines():
            if line.startswith("{"): dec = json.loads(line).get("hookSpecificOutput", {})
        return (dec or {}).get("permissionDecision"), (dec or {}).get("permissionDecisionReason", ""), p.stdout
    def test_guard_uses_canonical_policy_not_a_duplicate_ruleset(self):
        src = GUARD.read_text(encoding="utf-8")
        self.assertIn("validate_workspace", src); self.assertIn("check_path", src)
        self.assertNotIn("forbidden_words = [", src); self.assertNotIn("business_filename_regex\"", src.replace("pol[\"naming\"]", ""))
    def test_guard_denies_invalid_write_targets(self):
        d = clean_tree()
        for path in ("01_Active/Sales/Sales strategy final2.docx", "Notes.md", "04_Sources/Imports/helper.py", ".claude/skills/test_x.py", "01_Active/Sales/Ռազմ.docx"):
            dec, why, _ = self.guard("PreToolUse", "Write", {"file_path": str(d / path), "content": "x"}, d); self.assertEqual(dec, "deny", path)
    def test_guard_allows_valid_business_and_technical_targets(self):
        d = clean_tree()
        for path in ("01_Active/Sales/Sales-strategy-v1.1-2026-09-10.docx", "Journal.md", ".claude/tools/build_task_workbook.py", "02_Reference/People/Staffing-plan-2026-09-07.xlsx", "00_Inbox/Input.md"):
            dec, why, _ = self.guard("PreToolUse", "Write", {"file_path": str(d / path), "content": "x"}, d); self.assertIsNone(dec, (path, why))
    def test_guard_bash_move_targets(self):
        d = clean_tree()
        dec, why, _ = self.guard("PreToolUse", "Bash", {"command": f'mv "{d}/Journal.md" "{d}/01_Active/Sales/journal copy (2).md"'}, d); self.assertEqual(dec, "deny")
        dec, why, _ = self.guard("PreToolUse", "Bash", {"command": f'mv "{d}/Journal.md" "{d}/05_Archive/Journal-2026-09-10.md"'}, d); self.assertIsNone(dec, why)
        dec, why, _ = self.guard("PreToolUse", "Bash", {"command": f'mkdir "{d}/06_New"'}, d); self.assertEqual(dec, "deny")
    def test_guard_post_mutation_validates_and_flags(self):
        d = clean_tree(); (d / "Junk.txt").write_text("", encoding="utf-8")
        dec, why, out = self.guard("PostToolUse", "Bash", {"command": "echo x"}, d)
        self.assertIn("WORKSPACE VIOLATION", out)
    def test_guard_fails_closed_on_corrupt_policy(self):
        d = clean_tree(); bad = pathlib.Path(tempfile.mkdtemp()) / "workspace_policy.json"; bad.write_text("{", encoding="utf-8")
        p = subprocess.run([sys.executable, str(GUARD), "PreToolUse"], input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": str(d / "Journal.md")}}),
                           capture_output=True, text=True, encoding="utf-8", env={**os.environ, "WORKSPACE_ROOT": str(d), "WORKSPACE_POLICY": str(bad)})
        self.assertIn('"deny"', p.stdout)

if __name__ == "__main__":
    unittest.main(verbosity=2)
