# -*- coding: utf-8 -*-
"""SENSITIVE BOUNDARY suite — data classification + scanner: CONFIDENTIAL/RESTRICTED fixtures are BLOCKED, safe business-model
Core files are ALLOWED, and the git staging boundary (pre-commit hook) rejects a staged sensitive file in a temp repository.
All fixtures below are synthetic (FIXTURE) — no real person, subscriber or secret appears here."""
import unittest, json, os, sys, pathlib, tempfile, subprocess, shutil
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / ".claude" / "policy")); sys.path.insert(0, str(ROOT / ".claude" / "skills"))
from testing import covers
import sensitive_scan as ss

GOV = ("authority_checking", "approval_management", "completion_verification", "audit_logging", "data_sensitivity_awareness")
POL = ss.load_policy()
FAKE_NAMES = ["Zorbulak Q.", "Fixturina Test"]      # synthetic overlay names for the name check

def findings(rel, text): return ss.scan_blob(rel, text.encode("utf-8"), POL, FAKE_NAMES)
def classes(fs): return {f["class"] for f in fs}

class S01_Classification(unittest.TestCase):
    @covers(*GOV, kinds=("unit",))
    def test_classes_defined_and_not_one_bucket(self):
        self.assertEqual(set(POL["classes"]), {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"})
        items = POL["items"]; self.assertGreaterEqual(len(set(items.values())), 4)
        for k in ("repository_code", "role_definitions_without_compensation", "process_definitions", "kpi_definitions_and_formulas", "targets_and_thresholds", "employee_names_and_person_role_mappings", "salaries_compensation_payroll", "customer_subscriber_data_and_derived_lists", "phone_numbers_emails_addresses_of_individuals", "billing_account_and_subscriber_identifiers", "credentials_tokens_keys", "system_access_data", "raw_whatsapp_exports_and_quotes", "screenshots_and_images", "management_decisions_with_personal_content"):
            self.assertIn(k, items, k)
        self.assertEqual(items["salaries_compensation_payroll"], "CONFIDENTIAL"); self.assertEqual(items["credentials_tokens_keys"], "RESTRICTED"); self.assertEqual(items["process_definitions"], "INTERNAL")
    @covers(*GOV, kinds=("unit",))
    def test_path_rules_classify_overlay_and_generated_as_non_versionable(self):
        for rel, cls in ((".claude/business/overlay/ov_people.py", "CONFIDENTIAL"), (".claude/business/overlay.json", "CONFIDENTIAL"), (".claude/business/business_model.json", "CONFIDENTIAL"), (".claude/business/Business-model.md", "CONFIDENTIAL"),
                         ("04_Sources/Whatsapp/Principal-2026-09-09/chat.md", "CONFIDENTIAL"), ("Tasks.xlsx", "CONFIDENTIAL"), (".claude/state/skill_state.db", "RESTRICTED"), (".claude/settings.local.json", "RESTRICTED"),
                         (".claude/business/bm_processes.py", "PUBLIC"), (".claude/business/build_business_model.py", "PUBLIC"), (".claude/skills/business.py", "PUBLIC"), (".claude/business/certification.json", "INTERNAL")):
            self.assertEqual(ss.classify_path(rel, POL)[0], cls, rel)

class S02_ContentDetection(unittest.TestCase):
    @covers(*GOV, kinds=("unit", "adversarial"))
    def test_secrets_detected(self):
        for txt in ("token = gho_0123456789abcdefghijklmnopqrstuvwxyz", "aws AKIAABCDEFGHIJKLMNOP", "-----BEGIN RSA PRIVATE KEY-----", 'password: "hunter2hunter2"', "api_key=ABCDEFGHIJKLMNOP1234"):
            self.assertIn("RESTRICTED", classes(findings("x.py", txt)), txt)
    @covers(*GOV, kinds=("unit", "adversarial"))
    def test_salary_and_subscriber_leakage_detected(self):
        self.assertIn("CONFIDENTIAL", classes(findings("core.json", '"fix_salary_net_amd": 350000')))
        self.assertIn("CONFIDENTIAL", classes(findings("core.py", 'FIX_SALARY_NET_AMD = {"1.1": 350000}')))
        self.assertIn("CONFIDENTIAL", classes(findings("x.txt", "Rank | Score | Band | Login | Name | Tariff")))
        self.assertIn("RESTRICTED", classes(findings("x.txt", "login User_013135 balance 19.79")))
        self.assertIn("RESTRICTED", classes(findings("x.txt", "call 094401002 today")))
        self.assertIn("RESTRICTED", classes(findings("x.txt", "mail someone.person@gmail.com")))
        self.assertIn("CONFIDENTIAL", classes(findings("x.md", "# WhatsApp Chat Export: Someone")))
        self.assertIn("CONFIDENTIAL", classes(findings("bm_x.py", "the owner is Zorbulak Q. now")))      # overlay name literal
    @covers(*GOV, kinds=("unit",))
    def test_safe_core_content_allowed(self):
        safe = ('{"code": "1.1", "title": "Sales Head", "manager": "Head of S&O", "positions": 1, "filled": 1, "compensation": "OVERLAY", "src": ["S01"], "conf": "CONFIRMED"}\n'
                '{"process_id": "P-OPS-01", "steps": ["TRIGGER task", "VERIFY closed"], "owner": "Installation group head (2.3)", "sla": "TG-SLA-INSTALL (UNKNOWN)"}\n'
                '{"kpi_id": "K-NEW", "target": "UNKNOWN", "formula": "count(activations)"}\n'
                'owner @P2 (DERIVED); Gev approves; tariff Plus 7000 (7,000 AMD/month); phone-shaped id 2026-09-10 is a date; KPI weight 0.35\n')
        self.assertEqual(findings("bm_company.py", safe), [], findings("bm_company.py", safe))
        self.assertEqual(findings(".claude/skills/business.py", "def compensation_for(code): return 'OVERLAY'"), [])
    @covers(*GOV, kinds=("unit",))
    def test_real_core_files_are_clean(self):
        core = sorted((ROOT / ".claude" / "business").glob("bm_*.py")) + [ROOT / ".claude" / "business" / "build_business_model.py", ROOT / ".claude" / "business" / "certify_business.py", ROOT / ".claude" / "skills" / "business.py"]
        rep = ss.scan_paths([p for p in core if p.exists()], names=ss.overlay_names())
        self.assertEqual(rep, {}, rep)

@unittest.skipUnless(shutil.which("git"), "git not available")
class S03_GitStagingBoundary(unittest.TestCase):
    def _repo(self):
        d = pathlib.Path(tempfile.mkdtemp(prefix="bnd_")); subprocess.run(["git", "init", "-q", str(d)], check=True)
        subprocess.run(["git", "-C", str(d), "config", "user.email", "fixture@example.org"], check=True); subprocess.run(["git", "-C", str(d), "config", "user.name", "Fixture"], check=True)
        (d / ".claude" / "policy").mkdir(parents=True); (d / ".claude" / "business" / "overlay").mkdir(parents=True); (d / ".claude" / "runtime").mkdir(parents=True)
        shutil.copy(ROOT / ".claude" / "policy" / "data_classification.json", d / ".claude" / "policy" / "data_classification.json")
        shutil.copy(ROOT / ".claude" / "policy" / "sensitive_scan.py", d / ".claude" / "policy" / "sensitive_scan.py")
        shutil.copy(ROOT / ".claude" / "runtime" / "python_runtime.py", d / ".claude" / "runtime" / "python_runtime.py")
        shutil.copy(ROOT / ".claude" / "runtime" / "requirements.txt", d / ".claude" / "runtime" / "requirements.txt"); shutil.copy(ROOT / ".claude" / "runtime" / "requirements.lock", d / ".claude" / "runtime" / "requirements.lock")
        return d
    def _scan_staged(self, d):
        env = {**os.environ, "COMMAND_CENTER_VENV": str(ROOT / ".venv")}
        return subprocess.run([sys.executable, str(d / ".claude" / "policy" / "sensitive_scan.py"), "--staged"], cwd=str(d), capture_output=True, text=True, encoding="utf-8", env=env)
    @covers(*GOV, kinds=("unit", "adversarial", "failure_injection"))
    def test_staged_sensitive_files_blocked_and_safe_core_allowed(self):
        d = self._repo()
        (d / ".claude" / "business" / "bm_processes.py").write_text('PROCESSES = [{"process_id": "P-OPS-01", "owner": "Installation head (2.3)", "src": ["S02"]}]\n', encoding="utf-8")
        subprocess.run(["git", "-C", str(d), "add", ".claude/business/bm_processes.py", ".claude/policy"], check=True)
        r = self._scan_staged(d); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)          # safe core + policy allowed
        (d / ".claude" / "business" / "overlay" / "ov_people.py").write_text('OVERLAY_DATA = True\nPERSONS = [{"id": "@P9", "name": "Fixturina Test"}]\n', encoding="utf-8")
        subprocess.run(["git", "-C", str(d), "add", "-f", ".claude/business/overlay/ov_people.py"], check=True)
        r = self._scan_staged(d); self.assertEqual(r.returncode, 1); self.assertIn("BOUNDARY VIOLATION", r.stdout); self.assertIn("overlay", r.stdout)
        subprocess.run(["git", "-C", str(d), "reset", "-q", ".claude/business/overlay/ov_people.py"], check=True)
        (d / "notes.md").write_text("contact 094 40 10 02 and token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(d), "add", "notes.md"], check=True)
        r = self._scan_staged(d); self.assertEqual(r.returncode, 1); self.assertIn("RESTRICTED", r.stdout)
        subprocess.run(["git", "-C", str(d), "reset", "-q", "notes.md"], check=True)
        (d / "export.jsonl").write_text('{"x": 1}\n', encoding="utf-8"); subprocess.run(["git", "-C", str(d), "add", "export.jsonl"], check=True)
        r = self._scan_staged(d); self.assertEqual(r.returncode, 1)                                 # raw operational export path
    @covers(*GOV, kinds=("unit", "failure_injection"))
    def test_pre_commit_hook_installed_and_blocks_commit(self):
        d = self._repo(); (d / "keep.txt").write_text("safe\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(d), "add", "keep.txt"], check=True)
        self.assertTrue(ss.install_hooks(d)); self.assertTrue(ss.hooks_installed(d))
        # the hook uses .venv of the repo or PATH python; point it at the workspace venv through PATH
        env = {**os.environ, "PATH": str(ROOT / ".venv" / "Scripts") + os.pathsep + os.environ.get("PATH", "")}
        r = subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", "safe"], capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        (d / "secret.txt").write_text("password = supersecretvalue123\n", encoding="utf-8"); subprocess.run(["git", "-C", str(d), "add", "secret.txt"], check=True)
        r = subprocess.run(["git", "-C", str(d), "commit", "-q", "-m", "leak"], capture_output=True, text=True, encoding="utf-8", env=env)
        self.assertNotEqual(r.returncode, 0); self.assertIn("BOUNDARY VIOLATION", r.stdout + r.stderr)
    @covers(*GOV, kinds=("unit",))
    def test_workspace_repository_index_is_clean(self):
        out = subprocess.run(["git", "ls-files"], cwd=str(ROOT), capture_output=True, text=True).stdout.split()
        bad = [rel for rel in out if ss.classify_path(rel, POL)[0] in ("CONFIDENTIAL", "RESTRICTED")]
        self.assertEqual(bad, [], bad)
        self.assertTrue(ss.hooks_installed(ROOT))

if __name__ == "__main__":
    unittest.main(verbosity=2)
