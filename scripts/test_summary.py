"""Turn a pytest JUnit XML file into a Markdown table for the GitHub Actions summary.

Usage: python scripts/test_summary.py <junit.xml> "<title>"
Appends to $GITHUB_STEP_SUMMARY when set, otherwise prints.
"""
import os
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict


def main(path, title):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root)
    per_file = OrderedDict()
    for suite in suites:
        for case in suite.iter("testcase"):
            name = case.get("classname", "").split(".")
            file = name[1] if len(name) > 1 and name[0] == "tests" else (name[0] or "?")
            row = per_file.setdefault(file, {"passed": 0, "failed": 0, "skipped": 0})
            if case.find("failure") is not None or case.find("error") is not None:
                row["failed"] += 1
            elif case.find("skipped") is not None:
                row["skipped"] += 1
            else:
                row["passed"] += 1

    passed = sum(r["passed"] for r in per_file.values())
    failed = sum(r["failed"] for r in per_file.values())
    skipped = sum(r["skipped"] for r in per_file.values())
    total = passed + failed + skipped
    rate = (100.0 * passed / total) if total else 0.0

    lines = [
        f"## {title}",
        "",
        "| Total | Passed | Failed | Skipped | Pass rate |",
        "|---|---|---|---|---|",
        f"| {total} | {passed} | {failed} | {skipped} | {rate:.1f}% |",
        "",
        "| Test file | Passed | Failed | Skipped |",
        "|---|---|---|---|",
    ]
    for file, r in per_file.items():
        lines.append(f"| {file} | {r['passed']} | {r['failed']} | {r['skipped']} |")
    lines.append("")

    text = "\n".join(lines)
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "Test results"))
