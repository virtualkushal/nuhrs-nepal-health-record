"""
Cross-facility seed consistency checker (repo-local, no Django needed).

Verifies the invariants the demo federation depends on:
  1. Demographics are CANONICAL per NID: name / dob / gender / phone must be
     identical in every facility seed that mentions that NID.
  2. Every lab analyte name used by the two lab seeds exists in the shared
     lab catalog (else FHIR LOINC translation degrades to uncoded text).
  3. Every hospital lab test/panel referenced in a JOURNEY exists in that
     hospital's local PANELS table.

Run:  python tools/check_seed_consistency.py
Exits non-zero (and prints PROBLEM lines) if any invariant is broken.
"""
import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
problems = []


def _literal(node):
    """ast.literal_eval, but tolerate dict(...) calls used by the hospital seeds."""
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "dict":
        return {kw.arg: _literal(kw.value) for kw in node.keywords}
    if isinstance(node, ast.Dict):
        return {_literal(k): _literal(v) for k, v in zip(node.keys, node.values)}
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_literal(e) for e in node.elts]
    return ast.literal_eval(node)


def load_module_consts(path, names):
    """Safely eval selected top-level literal assignments from a .py file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                out[target.id] = _literal(node.value)
    return out


# ---------------------------------------------------------------- load seeds
med = load_module_consts(
    ROOT / "mediciti-hospital/clinical/management/commands/seed.py",
    {"PATIENTS", "JOURNEYS", "PANELS"})
nor = load_module_consts(
    ROOT / "norvic-hospital/clinical/management/commands/seed.py",
    {"PATIENTS", "JOURNEYS", "PANELS"})
gra = load_module_consts(
    ROOT / "grandi-hospital/clinical/management/commands/seed.py",
    {"PATIENTS", "JOURNEYS", "PANELS"})
cdl = load_module_consts(
    ROOT / "central-diagnostic-lab/lab/management/commands/seed.py",
    {"DEMOGRAPHICS", "REPORTS_LAB001"})
pat = load_module_consts(
    ROOT / "pathlabs-nepal/lab/management/commands/seed.py",
    {"DEMOGRAPHICS", "REPORTS_LAB002"})
catalog = load_module_consts(ROOT / "pathlabs-nepal/lab/catalog.py", {"ANALYTES", "PANELS"})
swa = load_module_consts(
    ROOT / "swastha-ehr/backend/core/management/commands/seed_demo.py", {"DEMO_NIDS"})

# ------------------------------------------------- 1. canonical demographics
canon = {}


def register(source, nid, name, dob, gender, phone):
    key = (name, str(dob), gender, phone)
    if nid in canon:
        prev_src, prev_key = canon[nid]
        if prev_key != key:
            problems.append(
                f"DEMOGRAPHICS MISMATCH for {nid}: {prev_src}={prev_key} vs {source}={key}")
    else:
        canon[nid] = (source, key)


for nid, d in med["PATIENTS"].items():
    register("mediciti", nid, d["name"], d["dob"], d["gender"], d["phone"])
for nid, d in nor["PATIENTS"].items():
    register("norvic", nid, f"{d['first']} {d['last']}", d["dob"], d["gender"], d["phone"])
for nid, d in gra["PATIENTS"].items():
    register("grandi", nid, f"{d['first']} {d['last']}", d["dob"], d["gender"], d["phone"])
for nid, d in cdl["DEMOGRAPHICS"].items():
    register("central", nid, d["name"], d["dob"], d["gender"], d["phone"])
for nid, d in pat["DEMOGRAPHICS"].items():
    register("pathlabs", nid, d["name"], d["dob"], d["gender"], d["phone"])

# ------------------------------------------------------- 2. lab catalog names
known_analytes = set(catalog["ANALYTES"])
known_panels = set(catalog["PANELS"])
for label, reports in (("central", cdl["REPORTS_LAB001"]), ("pathlabs", pat["REPORTS_LAB002"])):
    for row in reports:
        if row["panel"] not in known_panels:
            problems.append(f"{label}: panel '{row['panel']}' not in catalog.PANELS")
        for _date, _concl, values in row["visits"]:
            for analyte in values:
                if analyte not in known_analytes:
                    problems.append(
                        f"{label}: analyte '{analyte}' (panel {row['panel']}) not in catalog.ANALYTES")

# --------------------------------------------- 3. hospital panels / test names
for label, seed in (("mediciti", med), ("norvic", nor), ("grandi", gra)):
    panels = seed["PANELS"]
    for nid, episodes in seed["JOURNEYS"].items():
        if nid not in seed["PATIENTS"]:
            problems.append(f"{label}: JOURNEY for {nid} has no PATIENTS entry")
        for ep in episodes:
            for panel, _date, overrides in ep.get("labs", []) or []:
                if panel not in panels:
                    problems.append(f"{label}: panel '{panel}' missing from local PANELS ({nid})")
                    continue
                valid = {t[0] for t in panels[panel]}
                for test in (overrides or {}):
                    if test not in valid:
                        problems.append(
                            f"{label}: test '{test}' not in panel '{panel}' ({nid})")

# ------------------------------------------------------------------- summary
nids = sorted(canon)
print(f"NIDs seen across facilities: {len(nids)}")
print(f"  mediciti={len(med['PATIENTS'])} norvic={len(nor['PATIENTS'])} grandi={len(gra['PATIENTS'])} "
      f"central={len(cdl['DEMOGRAPHICS'])} pathlabs={len(pat['DEMOGRAPHICS'])} "
      f"swastha={len(swa['DEMO_NIDS'])}")
for nid in nids:
    at = []
    if nid in med["PATIENTS"]:
        at.append("MED")
    if nid in nor["PATIENTS"]:
        at.append("NOR")
    if nid in gra["PATIENTS"]:
        at.append("GRA")
    if nid in cdl["DEMOGRAPHICS"]:
        at.append("CDL")
    if nid in pat["DEMOGRAPHICS"]:
        at.append("PATH")
    if nid in swa["DEMO_NIDS"]:
        at.append("SWA")
    print(f"  {nid}  {canon[nid][1][0]:<26} {','.join(at)}")

if problems:
    print(f"\n{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  " + p)
    sys.exit(1)
print("\n0 problems - demographics canonical, all lab names resolvable.")
