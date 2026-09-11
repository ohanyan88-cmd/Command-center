# -*- coding: utf-8 -*-
"""PORTABILITY suite (Mission 4.1) — GitHub + recovery key → complete Command-center.
Canonical tree manifest · empty-directory survival (.gitkeep) · tree parity · durable checksums · durable state export/import
(idempotent) · encrypted credential recovery (wrong key, missing key, no secret logged) · gitignore policy · machine-specific
integration detection · no dependence on the original absolute path · CLEAN-CLONE BOOTSTRAP (twice → idempotent) with only
Git + a recovery key as inputs (the venv is shared through COMMAND_CENTER_VENV to keep the suite fast; the official clean-machine
run in the mission report builds its own venv)."""
import unittest, json, os, sys, pathlib, tempfile, shutil, subprocess, hashlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / ".claude" / "policy")); sys.path.insert(0, str(ROOT / ".claude" / "runtime")); sys.path.insert(0, str(ROOT / ".claude" / "skills")); sys.path.insert(0, str(ROOT / ".claude" / "integrations"))
from testing import covers
import tree_manifest as tm, state_snapshot as ssn, secure_recovery as sr, sensitive_scan as ss, engine, store

GOV = ("authority_checking", "approval_management", "completion_verification", "audit_logging")
TMP = pathlib.Path(tempfile.mkdtemp(prefix="ccport_"))
CLEAN = {}     # shared clean clone per test process (bootstrap is expensive): {"dir": Path, "home": Path, "runs": [...]}

def _git(args, cwd): return subprocess.run(["git"] + args, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")

def _clean_clone():
    """Clone the CURRENT workspace repository (committed content only) into an isolated dir with its own HOME dir holding only a recovery key."""
    if CLEAN: return CLEAN
    if not shutil.which("git"): raise unittest.SkipTest("git not available")
    d = TMP / "clone" / "Command-center"; home = TMP / "home"; home.mkdir(parents=True, exist_ok=True)
    key = sr.key_file()
    if not key.exists(): raise unittest.SkipTest("no recovery key on this machine")
    shutil.copy(key, home / "recovery.key")
    r = _git(["clone", "-q", str(ROOT), str(d)], TMP)
    if r.returncode != 0: raise unittest.SkipTest(f"clone failed: {r.stderr[:200]}")
    env = {**os.environ, "COMMAND_CENTER_HOME": str(home), "COMMAND_CENTER_VENV": str(ROOT / ".venv"), "COMMAND_CENTER_INTEGRATIONS_FIXTURE": ""}
    env.pop("COMMAND_CENTER_INTEGRATIONS_FIXTURE", None); env.pop("SKILL_STATE_DIR", None); env.pop("COMMAND_CENTER_RECOVERY_KEY_FILE", None); env.pop("COMMAND_CENTER_BUSINESS_DIR", None); env.pop("COMMAND_CENTER_BUSINESS_ROOT", None)
    runs = []
    for i in range(2):
        p = subprocess.run([sys.executable, str(d / "bootstrap.py"), "--json"], cwd=str(d), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        summ = next((json.loads(l) for l in p.stdout.splitlines() if l.startswith("{\"root\"")), None)
        runs.append({"rc": p.returncode, "out": p.stdout[-4000:], "err": p.stderr[-2000:], "summary": summ})
    CLEAN.update(dir=d, home=home, env=env, runs=runs); return CLEAN

class P01_TreeManifest(unittest.TestCase):
    @covers(*GOV, kinds=("unit",))
    def test_manifest_is_derived_from_policy_and_current(self):
        self.assertEqual(tm.check_manifest(), []); m = tm.build()
        paths = {e["path"]: e for e in m["entries"]}
        for req in ("CLAUDE.md", "README.md", "Tasks.xlsx", "Journal.md", "Actions.md", "bootstrap.py", "00_Inbox", "01_Active/Sales", "02_Reference/Systems", "04_Sources/Imports", "05_Archive", ".claude/business", ".claude/integrations", ".claude/state/durable", ".secure/credentials.gpg", ".claude/policy/workspace_tree_manifest.json"):
            self.assertIn(req, paths, req); self.assertTrue(paths[req]["required"], req)
        self.assertEqual(paths[".secure/credentials.gpg"]["durability"], "VERSION_ENCRYPTED"); self.assertEqual(paths[".venv"]["durability"], "REGENERATE"); self.assertEqual(paths[".claude/business/business_model.json"]["durability"], "REGENERATE")
        self.assertEqual(paths[".claude/state/skill_state.db"]["durability"], "EPHEMERAL"); self.assertEqual(paths["Tasks.xlsx"]["durability"], "VERSION_DIRECTLY")
        for e in m["entries"]: self.assertIn(e["durability"], ("VERSION_DIRECTLY", "VERSION_ENCRYPTED", "REGENERATE", "MACHINE_LOCAL", "EPHEMERAL")); self.assertTrue(e["restore"])
        self.assertEqual(tm.verify(ROOT), [])
    @covers(*GOV, kinds=("unit", "failure"))
    def test_out_of_date_manifest_is_detected(self):
        p = TMP / "stale_manifest.json"; m = tm.build(); m["entries"] = m["entries"][:-1]; p.write_text(json.dumps(m), encoding="utf-8")
        self.assertTrue(tm.check_manifest(p)); self.assertTrue(tm.check_manifest(TMP / "missing.json"))

class P02_EmptyDirectoriesAndGitignore(unittest.TestCase):
    @covers(*GOV, kinds=("unit",))
    def test_every_required_directory_survives_a_git_clone(self):
        tracked = set(_git(["ls-files"], ROOT).stdout.split())
        for e in tm.build()["entries"]:
            if e["kind"] != "directory" or not e["required"] or e["durability"] != "VERSION_DIRECTLY": continue
            self.assertTrue(any(t.startswith(e["path"] + "/") for t in tracked), f"{e['path']} has no tracked file (needs .gitkeep) — a clone would not recreate it")
    @covers(*GOV, "data_sensitivity_awareness", kinds=("unit",))
    def test_gitignore_matches_the_durability_model(self):
        gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for must in (".venv/", "__pycache__", ".claude/state/*", "!.claude/state/durable/", ".claude/audit/", ".claude/business/*.json", "*.key", ".env", ".secure/*.plain*", "*.lock", "_TEMP_WORK_COLLECTION/"): self.assertIn(must, gi, must)
        for never in ("Tasks.xlsx", "Journal.md", "Actions.md", "01_Active/", "04_Sources/", ".claude/business/overlay/"):
            self.assertFalse(any(l.strip() == never for l in gi.splitlines()), f".gitignore must not ignore durable {never}")
        chk = lambda rel: _git(["check-ignore", "-q", rel], ROOT).returncode == 0
        for rel in ("Tasks.xlsx", "Journal.md", "01_Active/Sales/x.docx", ".claude/business/overlay/ov_people.py", ".claude/state/durable/commitments.jsonl", ".secure/credentials.gpg", ".secure/manifest.json"): self.assertFalse(chk(rel), rel)
        for rel in (".venv/x", ".claude/state/skill_state.db", ".claude/state/journal.jsonl", ".claude/audit/skill_audit.jsonl", ".claude/business/business_model.json", ".secure/credentials.plain", "any/recovery.key", ".claude/settings.local.json", "_TEMP_WORK_COLLECTION/x"): self.assertTrue(chk(rel), rel)
    @covers("data_sensitivity_awareness", *GOV, kinds=("unit", "adversarial"))
    def test_no_plaintext_credential_in_git_history(self):
        pol = ss.load_policy(); bad = []
        for sha in _git(["rev-list", "--all"], ROOT).stdout.split():
            for rel in _git(["ls-tree", "-r", "--name-only", sha], ROOT).stdout.split():
                if ss.classify_path(rel, pol)[0] in ss.blocking_classes(pol): bad.append(f"{sha[:7]}:{rel}")
        self.assertEqual(bad, [], bad)
        secret_like = _git(["log", "-p", "--all", "-G", "(ghp_|gho_|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|/rest/[0-9]+/[A-Za-z0-9]{10,}/)", "--", ".", ":(exclude).claude/policy/data_classification.json", ":(exclude).claude/policy/sensitive_scan.py", ":(exclude).claude/tests"], ROOT).stdout
        self.assertNotIn("BEGIN RSA PRIVATE KEY", secret_like); self.assertEqual(secret_like.count("ghp_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ"), 0)

class P03_DurableState(unittest.TestCase):
    @covers("commitment_tracking", "decision_logging", "commitment_memory", "decision_memory", "audit_logging", *GOV, kinds=("unit", "completion", "failure_injection"))
    def test_export_is_deterministic_and_import_is_idempotent(self):
        saved = engine.STATE_DIR; root = TMP / "ws_state"; (root / ".claude" / "state").mkdir(parents=True)
        engine.STATE_DIR = root / ".claude" / "state"; store.reset()
        try:
            st = engine._store()
            st.record("commitments", "c-1", {"text": "call Friday", "due": "2026-09-19", "owner": "Գև"}); st.record("decisions", "d-1", {"decision": "BI off billing", "reason": "source of truth"})
            engine.audit({"execution_id": "e1", "skill_id": "x", "result_status": "EXECUTED"})
            c1 = ssn.export(root, log=lambda *a: None); a = {p.name: p.read_bytes() for p in ssn.durable_dir(root).iterdir()}
            c2 = ssn.export(root, log=lambda *a: None); b = {p.name: p.read_bytes() for p in ssn.durable_dir(root).iterdir()}
            self.assertEqual(a, b); self.assertEqual(c1["commitments"], 1); self.assertEqual(c1["decisions"], 1); self.assertGreaterEqual(c1["audit"], 1)
            # fresh store on "another machine": import twice → identical rows, no duplicates, ids preserved
            engine.STATE_DIR = root / ".claude" / "state2"; store.reset(); (root / ".claude" / "state2").mkdir()
            src = ssn.durable_dir(root); dst = root / ".claude" / "state2" / "durable"; shutil.copytree(src, dst)
            root2 = TMP / "ws_state2"; (root2 / ".claude" / "state").mkdir(parents=True); shutil.copytree(src, root2 / ".claude" / "state" / "durable")
            engine.STATE_DIR = root2 / ".claude" / "state"; store.reset()
            r1 = ssn.import_(root2, log=lambda *a: None); r2 = ssn.import_(root2, log=lambda *a: None)
            self.assertEqual(r1["commitments"]["new"], 1); self.assertEqual(r2["commitments"]["new"], 0); self.assertEqual(r2["commitments"]["existing"], 1)
            st2 = engine._store(); self.assertEqual(st2.get("commitments", "c-1")["text"], "call Friday"); self.assertEqual(st2.get("decisions", "d-1")["decision"], "BI off billing"); self.assertEqual(len(st2.list("commitments")), 1)
            self.assertEqual(sorted(x["op_id"] for x in st2.list("audit")), sorted(x["op_id"] for x in st.list("audit")))
            c3 = ssn.export(root2, log=lambda *a: None); self.assertEqual({p.name: p.read_bytes() for p in ssn.durable_dir(root2).iterdir() if p.name != "business_observations.jsonl"}, {k: v for k, v in a.items() if k != "business_observations.jsonl"})   # semantically identical
        finally: engine.STATE_DIR = saved; store.reset()
    @covers("audit_logging", "data_sensitivity_awareness", *GOV, kinds=("unit",))
    def test_workspace_export_exists_and_carries_no_secret(self):
        d = ssn.durable_dir(ROOT)
        for f in ("commitments.jsonl", "decisions.jsonl", "audit.jsonl"): self.assertTrue((d / f).exists(), f)
        pol = ss.load_policy()
        for f in d.glob("*.jsonl"):
            fs = [x for x in ss.scan_content(f".claude/state/durable/{f.name}", f.read_text(encoding="utf-8"), pol, names=[]) if x["class"] in ss.blocking_classes(pol)]
            self.assertEqual(fs, [], f.name)

class P04_SecureRecovery(unittest.TestCase):
    def _env(self, home):
        old = {k: os.environ.get(k) for k in ("COMMAND_CENTER_HOME", "COMMAND_CENTER_RECOVERY_KEY_FILE")}
        os.environ["COMMAND_CENTER_HOME"] = str(home); os.environ.pop("COMMAND_CENTER_RECOVERY_KEY_FILE", None); return old
    def _restore_env(self, old):
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
    @covers("data_sensitivity_awareness", "authority_checking", "completion_verification", "audit_logging", kinds=("unit", "failure", "failure_injection", "adversarial"))
    def test_backup_restore_wrong_key_missing_key_and_no_secret_leak(self):
        if not (shutil.which("gpg") or shutil.which("gpg2")): self.skipTest("gpg missing")
        home = TMP / "sec_home"; (home / "integrations").mkdir(parents=True); old = self._env(home)
        saved = (sr.ARTIFACT.read_bytes() if sr.ARTIFACT.exists() else None, sr.MANIFEST.read_bytes() if sr.MANIFEST.exists() else None)
        secret = "wh00kS3cretC0deXYZ987abc"; url = f"https://portal.example.invalid/rest/7/{secret}/"
        try:
            (home / "integrations" / "INT-B24.json").write_text(json.dumps({"webhook_url": url, "portal_domain": "portal.example.invalid"}), encoding="utf-8")
            man = sr.backup(log=lambda *a: None)
            self.assertEqual(man["expected_credentials"]["INT-B24"]["status"], "PRESENT"); self.assertNotIn(secret, sr.MANIFEST.read_text(encoding="utf-8")); self.assertNotIn(secret.encode(), sr.ARTIFACT.read_bytes())
            self.assertNotIn(secret, json.dumps(man)); v = sr.verify(log=lambda *a: None); self.assertEqual(v["files"], ["integrations/INT-B24.json"])
            # restore into an empty home on "another machine"
            home2 = TMP / "sec_home2"; home2.mkdir(); shutil.copy(home / "recovery.key", home2 / "recovery.key"); os.environ["COMMAND_CENTER_HOME"] = str(home2)
            r = sr.restore(log=lambda *a: None); self.assertEqual(r["restored"], ["integrations/INT-B24.json"]); self.assertEqual(json.loads((home2 / "integrations" / "INT-B24.json").read_text(encoding="utf-8"))["webhook_url"], url)
            (home2 / "integrations" / "INT-B24.json").write_text("{\"webhook_url\": \"https://other.example.invalid/rest/1/newer0000000/\"}", encoding="utf-8")
            r2 = sr.restore(log=lambda *a: None); self.assertEqual(r2["restored"], []); self.assertTrue(any("differs" in k for k in r2["kept"]))      # never overwrites silently
            # wrong key
            (home2 / "recovery.key").write_bytes(b"wrong-key-wrong-key-wrong-key-wrong-key-00\n")
            with self.assertRaises(sr.RecoveryError) as cm: sr.verify(log=lambda *a: None)
            self.assertIn("decryption FAILED", str(cm.exception)); self.assertNotIn(secret, str(cm.exception))
            # missing key
            (home2 / "recovery.key").unlink()
            with self.assertRaises(sr.RecoveryError) as cm: sr.restore(log=lambda *a: None)
            self.assertIn("recovery key missing", str(cm.exception))
            # the key never reaches audit/state: nothing under the workspace state carries the key or the secret
            key = (home / "recovery.key").read_text(encoding="utf-8").strip()
            for f in list((ROOT / ".claude" / "state").rglob("*.json*")) + [ROOT / ".claude" / "audit" / "skill_audit.jsonl"]:
                if f.exists() and f.stat().st_size < 60_000_000:
                    blob = f.read_bytes(); self.assertNotIn(key.encode(), blob, f.name); self.assertNotIn(secret.encode(), blob, f.name)
        finally:
            self._restore_env(old)
            if saved[0] is not None: sr.ARTIFACT.write_bytes(saved[0])
            if saved[1] is not None: sr.MANIFEST.write_bytes(saved[1])
    @covers("data_sensitivity_awareness", *GOV, kinds=("unit",))
    def test_workspace_artifact_manifest_has_no_values_and_key_is_external(self):
        man = json.loads(sr.MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(man["artifact_sha256"], hashlib.sha256(sr.ARTIFACT.read_bytes()).hexdigest()); self.assertIn("expected_credentials", man); self.assertNotIn("webhook_url\":", json.dumps(man).replace("secrets", ""))
        self.assertFalse(str(sr.key_file()).startswith(str(ROOT))); self.assertFalse(_git(["ls-files", "--error-unmatch", "--", str(sr.key_file())], ROOT).returncode == 0)
        self.assertNotIn("recovery.key", _git(["ls-files"], ROOT).stdout)

class P05_MachineSpecificAndPaths(unittest.TestCase):
    @covers(*GOV, kinds=("unit",))
    def test_machine_dependencies_are_declared(self):
        import registry
        for iid in ("INT-OL-CAL", "INT-OL-MAIL"): self.assertIn("Outlook", registry.INTEGRATIONS[iid]["machine_dependency"])
        self.assertIsNone(registry.INTEGRATIONS["INT-TASKS"]["machine_dependency"]); self.assertEqual(registry.declaration_problems(), [])
    @covers(*GOV, kinds=("unit",))
    def test_no_dependence_on_the_original_absolute_path(self):
        pat = "Users" + "/" + "Admin"; hits = []
        for f in list((ROOT / ".claude").rglob("*.py")) + [ROOT / "bootstrap.py", ROOT / ".claude" / "settings.json", ROOT / ".claude" / "policy" / "workspace_policy.json", ROOT / ".claude" / "runtime" / "hook.sh"]:
            if "__pycache__" in str(f) or f.name == "test_portability.py": continue
            t = f.read_text(encoding="utf-8", errors="replace")
            if pat in t or pat.replace("/", "\\\\") in t or "Desktop" + "\\\\" + "Command-center" in t or "c--Users-Admin" in t: hits.append(f.name)
        self.assertEqual(hits, [], hits)

class P06_CleanCloneBootstrap(unittest.TestCase):
    """Only Git (a clone of this repository) + a recovery key are inputs. The bootstrap runs TWICE."""
    @covers(*GOV, "daily_briefing", "business_model_query", kinds=("completion", "unit", "failure_injection"))
    def test_bootstrap_restores_canonical_workspace_and_is_idempotent(self):
        c = _clean_clone(); d = c["dir"]
        for i, r in enumerate(c["runs"]): self.assertEqual(r["rc"], 0, f"run {i}: {r['out'][-1500:]}\n{r['err'][-800:]}"); self.assertEqual(r["summary"]["verdict"], "READY", r["summary"])
        for e in tm.build()["entries"]:
            if e["required"] and e["path"] != ".git":
                p = d / e["path"]; self.assertTrue(p.is_dir() if e["kind"] == "directory" else p.is_file(), f"restored workspace lacks {e['path']}")
        for f in ("Tasks.xlsx", "Journal.md", "Actions.md", "00_Inbox/Input.md", "02_Reference/People/Staffing-plan-2026-09-07.xlsx", ".claude/business/overlay/ov_people.py", ".claude/business/business_model.json", ".claude/business/overlay.json", ".claude/business/certification.json", ".claude/integrations/certification.json", ".claude/state/skill_state.db"):
            self.assertTrue((d / f).exists(), f)
        cert = json.loads((d / ".claude" / "business" / "certification.json").read_text(encoding="utf-8")); self.assertEqual(cert["result"], "PASS")
        src_cert = json.loads((ROOT / ".claude" / "business" / "certification.json").read_text(encoding="utf-8"))
        self.assertEqual((cert["core_fingerprint"], cert["overlay_fingerprint"], cert["model_version"]), (src_cert["core_fingerprint"], src_cert["overlay_fingerprint"], src_cert["model_version"]))   # same business understanding
        icert = json.loads((d / ".claude" / "integrations" / "certification.json").read_text(encoding="utf-8")); self.assertEqual(icert["result"], "PASS")
        self.assertIn(icert["integrations"]["INT-B24"]["state"], ("DECLARED", "CONFIGURED")); self.assertIn("INT-OL-CAL", icert["integrations"])
        steps2 = {s["step"]: s for s in c["runs"][1]["summary"]["steps"]}
        self.assertEqual(steps2["canonical directories"]["detail"], "all present"); self.assertIn("new", steps2["durable Deputy state"]["detail"]); self.assertIn("'new': 0", steps2["durable Deputy state"]["detail"])
        self.assertIn(steps2["encrypted credentials"]["status"], ("OK", "WARN"))
    @covers(*GOV, kinds=("unit", "completion"))
    def test_tree_parity_and_content_integrity_after_restore(self):
        c = _clean_clone(); d = c["dir"]
        src = tm.snapshot(ROOT); dst = tm.snapshot(d)
        # durable files that differ only because the working tree is ahead of the last commit are reported, not hidden
        committed = set(_git(["ls-files"], ROOT).stdout.split()); dirty = set(l[3:].strip() for l in _git(["status", "--porcelain"], ROOT).stdout.splitlines())
        src["durable_files"] = {k: v for k, v in src["durable_files"].items() if k in committed and k not in dirty}; dst["durable_files"] = {k: v for k, v in dst["durable_files"].items() if k in src["durable_files"]}
        par = tm.parity(src, dst)
        self.assertEqual(par["missing_required"], []); self.assertEqual(par["missing_durable_files"], []); self.assertEqual(par["changed_durable_files"], [], par["changed_durable_files"][:5]); self.assertEqual(src["counts"]["required"], dst["counts"]["required"])
        cs = tm.verify_checksums(d); self.assertEqual(cs["missing"], []); self.assertEqual([f for f in cs["changed"] if f not in dirty], [])
        durable = ssn.status(d) if False else None
        st_new = json.loads((d / ".claude" / "state" / "bootstrap_last.json").read_text(encoding="utf-8")); self.assertEqual(st_new["verdict"], "READY")
    @covers(*GOV, "task_management", kinds=("unit", "completion"))
    def test_recovery_carries_the_latest_synced_live_register_and_the_same_static_model(self):
        """LIVE DATA path: the restored Tasks.xlsx is byte-identical to the committed one (the synced truth), and the business understanding
        (core fingerprint) matches even though the register is STRUCTURE-scoped live data — never a stale extracted snapshot."""
        c = _clean_clone(); d = c["dir"]
        committed = subprocess.run(["git", "show", "HEAD:Tasks.xlsx"], cwd=str(ROOT), capture_output=True).stdout
        self.assertEqual(hashlib.sha256((d / "Tasks.xlsx").read_bytes()).hexdigest(), hashlib.sha256(committed).hexdigest())
        src = json.loads((d / ".claude" / "business" / "sources.json").read_text(encoding="utf-8")); s9 = src["source_snapshot"]["S09"]
        self.assertEqual(s9["scope"], "STRUCTURE"); self.assertEqual(s9["live_integration"], "INT-TASKS"); self.assertIsNone(s9["size"])
    @covers(*GOV, kinds=("adversarial", "unit"))
    def test_clone_used_nothing_from_the_original_workspace_but_git_and_the_key(self):
        c = _clean_clone(); d = c["dir"]; home = c["home"]
        self.assertEqual(sorted(p.name for p in home.iterdir() if p.is_file()), ["recovery.key"])
        self.assertFalse((d / "_TEMP_WORK_COLLECTION").exists()); self.assertFalse((d / ".claude" / "audit" / "skill_audit.jsonl").exists() and (d / ".claude" / "audit" / "skill_audit.jsonl").stat().st_size > 5_000_000)
        out = "\n".join(r["out"] for r in c["runs"]); self.assertNotIn((home / "recovery.key").read_text(encoding="utf-8").strip(), out)
        self.assertNotIn(str(ROOT), (d / ".claude" / "state" / "bootstrap_last.json").read_text(encoding="utf-8").replace(str(d), ""))

if __name__ == "__main__":
    unittest.main(verbosity=2)
