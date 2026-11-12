"""Generate the Part-3 test reports into docs/ with one command.

    pip install coverage
    python scripts/generate_reports.py

Writes (all under docs/):
    Unit_Test_Report.md          every test, grouped by file, with totals
    Code_Coverage_Report.md      statement coverage per file
    Branch_Coverage_Report.md    branch coverage per file, with missed branch lines
    Test_Case_Document.md        every STP test case, its automated tests and result
    System_Validation_Report.md  end-to-end checklist (created once; your entries are kept)
    reports/                     raw unit_tests.xml, coverage.json and coverage_html/

Options:  --skip-run   rebuild the Markdown from the existing raw files without running tests
          --force-validation   recreate System_Validation_Report.md (discards your entries)
"""
import argparse
import ast
import json
import os
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict, defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = "Railway Reservation System (RRS), Team 13 Jackfruit Phase-1"
LINE_TARGET = 80.0

# Test cases from the STP/SRS: id, requirement, what must be true, level.
STP_CASES = [
    ("TC-Auth-01", "RRS-F-001", "Valid registration creates an account; duplicate email is rejected", "Unit"),
    ("TC-Auth-02", "RRS-F-002", "Correct credentials grant access to the dashboard", "Unit"),
    ("TC-Auth-03", "RRS-F-003", "After 5 failed logins further attempts are blocked temporarily", "Unit"),
    ("TC-Search-01", "RRS-F-010", "Matching trains are returned with class and timing", "Unit"),
    ("TC-Search-02", "RRS-F-011", "'No trains found' message for an unmatched route or date", "Unit"),
    ("TC-Book-01", "RRS-F-020", "Availability count matches the allocation state", "Unit"),
    ("TC-Book-02", "RRS-F-021", "Provisional booking is created and held for a limited time", "Unit"),
    ("TC-Book-03", "RRS-F-022", "Missing or invalid booking fields are flagged", "Unit"),
    ("TC-Pay-01", "RRS-F-030", "Booking becomes Confirmed only after a Success payment", "Integration"),
    ("TC-Pay-02", "RRS-F-031", "Failed or timed-out payment releases the seat", "Integration"),
    ("TC-PNR-01", "RRS-F-040", "A confirmed booking returns a valid PNR; lookup shows the right status", "Unit"),
    ("TC-Cancel-01", "RRS-F-041", "Confirmed cancellation sets Cancelled and releases the seat", "Unit"),
    ("TC-Cancel-02", "RRS-F-042", "Refund amount matches the cancellation policy", "Unit"),
    ("TC-Alloc-01", "RRS-F-050", "Assigned status matches current capacity", "Unit"),
    ("TC-Alloc-02", "RRS-F-051", "A cancellation promotes the earliest eligible waiting booking", "Integration"),
    ("TC-Admin-01", "RRS-F-060", "Schedule changes are reflected in search results", "Unit"),
    ("TC-Admin-02", "RRS-F-061", "Report figures match the underlying booking data", "Unit"),
    ("TC-Perf-01", "RRS-NF-001", "90th percentile transaction time is 5 seconds or less", "Performance"),
    ("TC-Sec-01", "RRS-NF-003", "No sensitive data is stored or exposed in plaintext", "Security"),
    ("TC-Ops-01", "RRS-NF-004", "Timestamped audit logs can be retrieved for sample bookings", "Integration"),
    ("TC-UX-01", "RRS-NF-005", "Labels, defaults and contrast pass; walkthrough done without help", "Usability"),
    ("TC-Sec-02", "PRJ-SR-001", "Connections without TLS are rejected; TLS 1.2 or newer only", "Security"),
    ("TC-Sec-03", "PRJ-SR-002", "Passwords are stored only as salted hashes", "Security"),
    ("TC-Sec-04", "PRJ-SR-003", "Direct API calls to admin endpoints are rejected for passengers", "Security"),
    ("TC-Sec-05", "PRJ-SR-004", "Session ends after the idle timeout", "Security"),
    ("TC-Sec-06", "PRJ-SR-005", "No raw card-like data is stored; only reference and status", "Security"),
    ("TC-Sec-07", "PRJ-SR-006", "An audit entry exists for every admin action", "Security"),
]
# Test files that predate the TC tags: mapped by file, and marked as such in the report.
FILE_TAGS = {
    "test_availability.py": ["TC-Book-01"],
    "test_booking.py": ["TC-Book-02", "TC-Book-03"],
    "test_payment.py": ["TC-Pay-01", "TC-Pay-02"],
    "test_payment_repo.py": ["TC-Pay-02"],
    "test_payment_security.py": ["TC-Sec-06"],
    "test_performance.py": ["TC-Perf-01"],
    "test_admin.py": ["TC-Admin-02"],
    "test_admin_routes.py": ["TC-Admin-02", "TC-Sec-04"],
    "test_audit_repo.py": ["TC-Ops-01"],
    "test_booking_repo.py": ["TC-Ops-01"],
    "test_train_admin_routes.py": ["TC-Admin-01", "TC-Sec-04"],
}
TAG_RE = re.compile(r"TC-[A-Za-z]+-\d+")


def path(*parts):
    return os.path.join(ROOT, *parts)


def today():
    return datetime.now().strftime("%d-%b-%Y")


# ---- running the tests -------------------------------------------------------------------
def run_pipeline():
    os.makedirs(path("docs", "reports"), exist_ok=True)
    xml, js, html = (path("docs", "reports", n) for n in ("unit_tests.xml", "coverage.json", "coverage_html"))
    try:
        import coverage  # noqa: F401
    except ImportError:
        sys.exit("The 'coverage' package is missing. Run: pip install coverage")
    run = [sys.executable, "-m", "coverage", "run", "--rcfile", path(".coveragerc"),
           "-m", "pytest", "-q", f"--junitxml={xml}"]
    code = subprocess.call(run, cwd=ROOT)
    print(f"pytest finished with exit code {code} (non-zero means some tests failed; reports are still built)")
    for args in (["json", "-o", js], ["html", "-d", html]):
        subprocess.check_call([sys.executable, "-m", "coverage", *args, "--rcfile", path(".coveragerc")], cwd=ROOT,
                              stdout=subprocess.DEVNULL)
    return xml, js


# ---- reading results -----------------------------------------------------------------------
def parse_junit(xml_path):
    cases = []
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        outcome, message = "passed", ""
        for tag, label in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
            node = case.find(tag)
            if node is not None:
                outcome, message = label, (node.get("message") or "").strip().splitlines()[0:1]
                message = message[0] if message else ""
                break
        module = (case.get("classname") or "").split(".")[-1]
        cases.append({"module": module, "name": case.get("name") or "", "outcome": outcome,
                      "time": float(case.get("time") or 0), "message": message})
    return cases


def parse_coverage(json_path):
    with open(json_path, encoding="utf-8") as handle:
        data = json.load(handle)
    files = []
    for name, info in sorted(data["files"].items()):
        s = info["summary"]
        statements, covered = s.get("num_statements", 0), s.get("covered_lines", 0)
        branches, covered_branches = s.get("num_branches", 0), s.get("covered_branches", 0)
        files.append({
            "file": name.replace("\\", "/"), "statements": statements, "covered": covered,
            "missing": s.get("missing_lines", statements - covered),
            "line_pct": 100.0 if not statements else covered / statements * 100,
            "branches": branches, "covered_branches": covered_branches,
            "partial": s.get("num_partial_branches", 0),
            "branch_pct": 100.0 if not branches else covered_branches / branches * 100,
            "missing_lines": info.get("missing_lines", []),
            "missing_branches": info.get("missing_branches", []),
        })
    totals = data.get("totals", {})
    return files, totals


def sum_files(files):
    statements, covered = sum(f["statements"] for f in files), sum(f["covered"] for f in files)
    branches, cb = sum(f["branches"] for f in files), sum(f["covered_branches"] for f in files)
    return {
        "statements": statements, "covered": covered,
        "line_pct": 100.0 if not statements else covered / statements * 100,
        "branches": branches, "covered_branches": cb,
        "branch_pct": 100.0 if not branches else cb / branches * 100,
    }


# ---- test case traceability ------------------------------------------------------------------
def scan_tags(tests_dir):
    """Returns {tc_id: [(module, function, how)]}; how is 'tag' or 'file'."""
    found = defaultdict(list)
    for fname in sorted(os.listdir(tests_dir)):
        if not (fname.startswith("test_") and fname.endswith(".py")):
            continue
        source = open(os.path.join(tests_dir, fname), encoding="utf-8-sig").read()  # some files start with a BOM
        tree = ast.parse(source)
        module_tags = set(TAG_RE.findall(ast.get_docstring(tree) or ""))
        lines = source.splitlines()
        module = fname[:-3]
        functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        any_tagged = bool(module_tags)
        per_function = {}
        for fn in functions:
            text = "\n".join(lines[fn.lineno - 1: fn.end_lineno])
            tags = set(TAG_RE.findall(text)) or set(module_tags)
            # a comment on the line above the def also counts
            if fn.lineno >= 2:
                tags |= set(TAG_RE.findall(lines[fn.lineno - 2]))
            per_function[fn.name] = tags
            any_tagged = any_tagged or bool(tags)
        for fn in functions:
            for tag in per_function[fn.name]:
                found[tag].append((module, fn.name, "tag"))
        if not any_tagged and fname in FILE_TAGS:
            for fn in functions:
                for tag in FILE_TAGS[fname]:
                    found[tag].append((module, fn.name, "file"))
    return found


def base_name(name):
    return name.split("[")[0]


def case_results(found, junit):
    outcome = {(c["module"], base_name(c["name"])): [] for c in junit}
    for c in junit:
        outcome[(c["module"], base_name(c["name"]))].append(c["outcome"])
    rows = []
    for tc_id, req, text, level in STP_CASES:
        tests = found.get(tc_id, [])
        results = []
        for module, function, _ in tests:
            results.extend(outcome.get((module, function), ["missing"]))
        if tc_id == "TC-UX-01" and tests:
            status = "Pass (automated); manual walkthrough pending"
            if any(r in ("failed", "error") for r in results):
                status = "FAIL"
        elif not tests:
            status = "No automated test (manual)"
        elif any(r in ("failed", "error") for r in results):
            status = "FAIL"
        elif all(r == "passed" for r in results):
            status = "Pass"
        else:
            status = "Not run"
        how = "tag" if any(t[2] == "tag" for t in tests) else ("file" if tests else "-")
        rows.append({"id": tc_id, "req": req, "text": text, "level": level, "tests": len(tests),
                     "status": status, "how": how})
    return rows


# ---- writing reports -------------------------------------------------------------------------
def table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(out)


def header(title, extra=""):
    return (f"# {title}\n\n**Project:** {PROJECT}  \n**Generated:** {today()}  \n"
            f"**Environment:** Python {platform.python_version()}, {platform.system()}  \n{extra}\n")


def unit_report(junit):
    total = len(junit)
    counts = defaultdict(int)
    for c in junit:
        counts[c["outcome"]] += 1
    seconds = sum(c["time"] for c in junit)
    rate = 100.0 * counts["passed"] / total if total else 0.0
    by_module = OrderedDict()
    for c in sorted(junit, key=lambda c: c["module"]):
        by_module.setdefault(c["module"], []).append(c)
    out = [header("Unit Test Report", "**Tool:** pytest  \n")]
    out.append("## Summary\n")
    out.append(table(["Total", "Passed", "Failed", "Errors", "Skipped", "Pass rate", "Run time"],
                     [[total, counts["passed"], counts["failed"], counts["error"], counts["skipped"],
                       f"{rate:.1f}%", f"{seconds:.1f}s"]]))
    out.append("\n\n## Results by test file\n")
    out.append(table(["Test file", "Tests", "Passed", "Failed", "Skipped"],
                     [[m + ".py", len(cs), sum(c["outcome"] == "passed" for c in cs),
                       sum(c["outcome"] in ("failed", "error") for c in cs),
                       sum(c["outcome"] == "skipped" for c in cs)] for m, cs in by_module.items()]))
    bad = [c for c in junit if c["outcome"] in ("failed", "error")]
    out.append("\n\n## Failures\n")
    out.append("None. All executed tests passed." if not bad else
               table(["Test", "Result", "Message"], [[f"{c['module']}::{c['name']}", c["outcome"],
                                                     c["message"].replace("|", "/")] for c in bad]))
    out.append("\n\n## Every test\n")
    for module, cs in by_module.items():
        out.append(f"\n### {module}.py\n")
        out.append(table(["Test", "Result", "Time (s)"], [[c["name"], c["outcome"], f"{c['time']:.3f}"] for c in cs]))
        out.append("")
    return "\n".join(out) + "\n"


def coverage_report(files, kind):
    s = sum_files(files)
    branch = kind == "branch"
    title = "Branch Coverage Report" if branch else "Code Coverage Report"
    out = [header(title, "**Tool:** coverage.py (branch measurement on)  \n")]
    out.append("## Summary\n")
    if branch:
        out.append(table(["Branches", "Taken both ways", "Branch coverage"],
                         [[s["branches"], s["covered_branches"], f"{s['branch_pct']:.1f}%"]]))
        out.append("\nA branch is one outcome of a decision (for example the `if` taken and the `if` skipped). "
                   "Each decision has at least two.\n")
        rows = [[f["file"], f["branches"], f["covered_branches"], f["partial"], f"{f['branch_pct']:.1f}%"]
                for f in files if f["branches"]]
        out.append("\n## Branch coverage per file\n")
        out.append(table(["File", "Branches", "Covered", "Partial lines", "Branch %"], rows))
        weak = sorted((f for f in files if f["branches"] and f["missing_branches"]),
                      key=lambda f: f["branch_pct"])[:10]
        out.append("\n\n## Branches never taken (lowest files first)\n")
        if not weak:
            out.append("Every branch was taken.")
        for f in weak:
            pairs = ", ".join(f"{a}->{'exit' if b < 0 else b}" for a, b in f["missing_branches"][:25])
            more = "" if len(f["missing_branches"]) <= 25 else f" (+{len(f['missing_branches']) - 25} more)"
            out.append(f"- `{f['file']}` ({f['branch_pct']:.1f}%): line->target {pairs}{more}")
    else:
        out.append(table(["Statements", "Covered", "Missed", "Statement coverage"],
                         [[s["statements"], s["covered"], s["statements"] - s["covered"], f"{s['line_pct']:.1f}%"]]))
        out.append(f"\nTarget: {LINE_TARGET:.0f}% per file. Files below the target are listed after the table.\n")
        rows = [[f["file"], f["statements"], f["covered"], f["missing"], f"{f['line_pct']:.1f}%"] for f in files]
        out.append("\n## Statement coverage per file\n")
        out.append(table(["File", "Statements", "Covered", "Missed", "Coverage"], rows))
        low = [f for f in files if f["statements"] and f["line_pct"] < LINE_TARGET]
        out.append(f"\n\n## Files below {LINE_TARGET:.0f}%\n")
        if not low:
            out.append("None.")
        for f in sorted(low, key=lambda f: f["line_pct"]):
            lines = ", ".join(str(n) for n in f["missing_lines"][:30])
            more = "" if len(f["missing_lines"]) <= 30 else f" (+{len(f['missing_lines']) - 30} more)"
            out.append(f"- `{f['file']}` ({f['line_pct']:.1f}%): lines not run: {lines}{more}")
    out.append("\n\n## Explanation of gaps\n")
    out.append("Repository files contain SQL that needs a live Supabase database. Their logic is tested with "
               "a fake database cursor, so some SQL-only lines run only in manual system testing "
               "(see System_Validation_Report.md).\n")
    out.append("\nFull line-by-line view: `docs/reports/coverage_html/index.html` (open in a browser; "
               "red lines were never run, yellow lines had a branch not taken).\n")
    return "\n".join(out)


def test_case_document(rows, junit):
    done = sum(r["status"].startswith("Pass") for r in rows)
    out = [header("Test Case Document (updated after Sprints 1 and 2)",
                  "**Replaces:** the test case list in STP v1.0, section 13  \n")]
    out.append("## Result summary\n")
    out.append(table(["STP test cases", "Passing (automated)", "Manual only", "Failing"],
                     [[len(rows), done, sum(r["status"].startswith("No automated") for r in rows),
                       sum(r["status"] == "FAIL" for r in rows)]]))
    out.append("\n\n## Test cases\n")
    out.append(table(["TC", "Requirement", "What must be true", "Level", "Automated tests", "Result", "Linked by"],
                     [[r["id"], r["req"], r["text"], r["level"], r["tests"], r["status"], r["how"]] for r in rows]))
    out.append("\n\n`Linked by: tag` means the test names the TC id in its docstring or a comment. "
               "`file` means the whole test file was mapped to the TC; check it. "
               "Add the TC id to a test's docstring to link it exactly.\n")
    out.append("\n## Changes since the submitted Test Plan (STP v1.0)\n")
    for item in [
        "Database: the build uses Supabase PostgreSQL, not MySQL as written in the SRS, SAD and STP. "
        "Repository code is tested with a fake cursor; SQL is exercised in system validation.",
        "Mock payment: the outcome (Success, Failed, Timeout) is chosen on the booking page for demonstration, "
        "which is how the planned Success/Failure test scenarios are driven.",
        "Added in Sprint 2: lockout (TC-Auth-03), idle timeout (TC-Sec-05), admin-only checks (TC-Sec-04), "
        "audit trail (TC-Sec-07, TC-Ops-01), waitlist/RAC promotion (TC-Alloc-02), train and schedule admin "
        "(TC-Admin-01), TLS (TC-Sec-02), health and uptime (RRS-NF-002), usability checks (TC-UX-01).",
        "TC-Sec-02 runs a real TLS handshake and checks that TLS 1.1 is refused, instead of only reading config.",
        "TC-UX-01 is split into an automated part (labels, contrast, defaults) and a manual walkthrough "
        "(docs/TC-UX-01_usability_walkthrough.md).",
        "RRS-NF-002 (99% availability) is evidenced by the uptime probe log, not by a pytest test.",
    ]:
        out.append(f"- {item}")
    return "\n".join(out) + "\n"


VALIDATION_ROWS = [
    ("SV-01", "RRS-F-001", "Register a new account", "Register page, valid details", "Account created, can log in", ""),
    ("SV-02", "RRS-F-002", "Log in with the correct password", "Login page", "Dashboard opens", "PASS"),
    ("SV-03", "RRS-F-003", "Five wrong passwords, then the right one", "Login page", "Lockout message; right password refused until the lock ends", ""),
    ("SV-04", "RRS-F-010", "Search Bengaluru to Chennai", "Search page", "Trains with classes, fares and times", "PASS"),
    ("SV-05", "RRS-F-011", "Search a route with no trains", "Search page", "'No trains found' message", ""),
    ("SV-06", "RRS-F-020", "Open Seat Availability", "Availability page", "Counts match the booking state", ""),
    ("SV-07", "RRS-F-021", "Book a ticket", "Press Book, fill the form", "Provisional hold (10 minutes) and payment step", "PASS"),
    ("SV-08", "RRS-F-022", "Submit the booking form with missing fields", "Booking form", "Clear error, no booking created", ""),
    ("SV-09", "RRS-F-030", "Pay Now (SUCCESS)", "Payment step", "Booking Confirmed with a PNR", "PASS"),
    ("SV-10", "RRS-F-031", "Pay with FAILED, then TIMEOUT", "Payment step", "Booking cancelled, seat available again", ""),
    ("SV-11", "RRS-F-040", "Look up the PNR", "PNR Status page", "Details and a Confirmed badge", "PASS"),
    ("SV-12", "RRS-F-041/042", "Cancel the ticket", "PNR page, Cancel ticket", "Status Cancelled; refund shown and recorded", ""),
    ("SV-13", "RRS-F-050/051", "1-seat class: book 3 tickets, cancel the first", "Admin page to make the schedule; PNR page", "2nd becomes Confirmed with PNR, 3rd becomes RAC", ""),
    ("SV-14", "RRS-F-060", "Add a train and a schedule, then search for it", "/admin/trains, Search", "It appears in search at once", ""),
    ("SV-15", "RRS-F-061", "Open admin reports", "/admin/reports", "Figures match the bookings made", ""),
    ("SV-16", "PRJ-SR-003", "Passenger opens an admin page or API", "/admin/reports, /api/admin/audit-log", "Access refused (403)", ""),
    ("SV-17", "PRJ-SR-004", "Stay idle past the timeout, then click", "Any page", "Redirected to the login page", ""),
    ("SV-18", "PRJ-SR-006", "Cancel as admin, then read the audit log", "/api/admin/audit-log", "Entry with user and time", ""),
    ("SV-19", "PRJ-SR-001", "Open the site over http while REQUIRE_HTTPS=1", "run_https.py", "Redirected to https", ""),
    ("SV-20", "RRS-NF-002", "Run the uptime probe, then read availability", "/api/admin/availability", "Availability at or above 99%", ""),
    ("SV-21", "RRS-NF-005", "Usability walkthrough with a new user", "docs/TC-UX-01_usability_walkthrough.md", "All tasks done without help", ""),
]


def validation_report():
    out = [header("System Validation Report",
                  "**Environment:** local Flask app against the Supabase test database  \n"
                  "**Tester:** ______________   **Browser:** ______________  \n")]
    out.append("End-to-end checks run in the browser against the real database (the part of the STP "
               "system-test level that unit tests cannot cover). Fill in the Actual and Result columns, "
               "and attach a screenshot name for anything that failed.\n")
    out.append("Rows marked PASS were observed on 12-Nov-2026 during the first run of the merged build.\n")
    out.append(table(["ID", "Requirement", "Scenario", "Where", "Expected", "Actual", "Result"],
                     [[r[0], r[1], r[2], r[3], r[4], "" if not r[5] else "Behaved as expected", r[5] or "[ ]"]
                      for r in VALIDATION_ROWS]))
    out.append("\n\n## Defects found\n")
    out.append(table(["#", "Scenario", "What happened", "Severity", "Fixed in"], [["", "", "", "", ""]]))
    out.append("\n\n## Conclusion\n")
    out.append("All scenarios passed: **YES / NO**   Open defects: ____   Signed: ______________\n")
    return "\n".join(out)


def write(name, text):
    target = path("docs", name)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote docs/" + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--skip-run", action="store_true")
    parser.add_argument("--force-validation", action="store_true")
    parser.add_argument("--root", help=argparse.SUPPRESS)
    args = parser.parse_args()
    global ROOT
    if args.root:
        ROOT = os.path.abspath(args.root)

    if args.skip_run:
        xml, js = path("docs", "reports", "unit_tests.xml"), path("docs", "reports", "coverage.json")
    else:
        xml, js = run_pipeline()
    junit = parse_junit(xml)
    files, _ = parse_coverage(js)
    rows = case_results(scan_tags(path("tests")), junit)

    write("Unit_Test_Report.md", unit_report(junit))
    write("Code_Coverage_Report.md", coverage_report(files, "line"))
    write("Branch_Coverage_Report.md", coverage_report(files, "branch"))
    write("Test_Case_Document.md", test_case_document(rows, junit))
    if args.force_validation or not os.path.exists(path("docs", "System_Validation_Report.md")):
        write("System_Validation_Report.md", validation_report())
    else:
        print("kept docs/System_Validation_Report.md (your entries); use --force-validation to recreate")

    s = sum_files(files)
    passed = sum(c["outcome"] == "passed" for c in junit)
    print(f"\nTests: {passed}/{len(junit)} passed | statement coverage {s['line_pct']:.1f}% | "
          f"branch coverage {s['branch_pct']:.1f}%")


if __name__ == "__main__":
    main()
