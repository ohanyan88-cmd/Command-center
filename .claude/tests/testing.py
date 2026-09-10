# -*- coding: utf-8 -*-
"""Evidence mapping for certification. A test declares WHICH skills it evidences and WHAT KIND of evidence it is.
certify.py reads these attributes from every passing test and writes per-skill certification records.

    @covers("commitment_tracking", kinds=("unit","completion"))
    def test_x(self): ...

kinds: unit · failure (BLOCKED/FAILED path exercised) · adversarial · failure_injection · authority ·
       completion (ran through engine.run_skill and asserted validated/verified) · concurrency · enforcement · routing
"""
KINDS = {"unit", "failure", "adversarial", "failure_injection", "authority", "completion", "concurrency", "enforcement", "routing"}

def covers(*skills, kinds=("unit",)):
    bad = set(kinds) - KINDS
    if bad: raise ValueError(f"unknown evidence kinds {bad}")
    def deco(fn):
        fn._covers = tuple(skills); fn._kinds = tuple(kinds); return fn
    return deco
