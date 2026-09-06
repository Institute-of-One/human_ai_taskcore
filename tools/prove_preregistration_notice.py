"""Prove the pre-registration reminder fires when it should and stops when it should.

Three states, all of which have to behave, or the reminder is decoration:

  1. no DOI recorded, ordinary run   -> the notice appears, but nothing fails
  2. no DOI recorded, --revision     -> it becomes a failure, because that is the
                                        moment a resubmission can cite a new record
  3. a DOI recorded                  -> silent, in both modes, for ever

State 3 is the one worth testing hardest. A reminder that never clears gets ignored,
and an ignored reminder is the same as no reminder.

Run from the repository root. results/release.json is restored afterwards.
"""

import json
import pathlib
import shutil
import subprocess
import sys

RELEASE = pathlib.Path("results/release.json")
CHECK = ["tools/presubmission_check.py"]


def run(*extra: str) -> str:
    result = subprocess.run(
        [sys.executable, *CHECK, *extra],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return f"[exit {result.returncode}]\n" + (result.stdout or "") + (result.stderr or "")


def set_doi(value: str | None) -> None:
    payload = json.loads(RELEASE.read_text(encoding="utf-8"))
    if value is None:
        payload.pop("preregistration_doi", None)
    else:
        payload["preregistration_doi"] = value
    RELEASE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )


def main() -> int:
    shutil.copy2(RELEASE, RELEASE.with_suffix(".json.bak"))
    failures = []
    try:
        set_doi(None)
        out = run()
        shown = "not archived under its own DOI" in out
        # the tree is dirty during this test, so a non-zero exit is expected; what
        # matters is that the notice itself did not create a *new* failure line
        blamed = "this is a revision" in out
        ok = shown and not blamed
        print(f"  {'PASS' if ok else 'FAIL'}  no DOI, ordinary run -> notice shown, "
              f"not blamed as a failure")
        failures += [] if ok else ["state 1"]

        out = run("--revision")
        ok = "this is a revision" in out and "[exit 1]" in out
        print(f"  {'PASS' if ok else 'FAIL'}  no DOI, --revision   -> hard failure")
        failures += [] if ok else ["state 2"]

        set_doi("10.5281/zenodo.99999999")
        quiet_plain = "not archived under its own DOI" not in run()
        quiet_rev = "this is a revision" not in run("--revision")
        ok = quiet_plain and quiet_rev
        print(f"  {'PASS' if ok else 'FAIL'}  DOI recorded         -> silent in both modes")
        failures += [] if ok else ["state 3"]
    finally:
        shutil.move(str(RELEASE.with_suffix(".json.bak")), str(RELEASE))

    print(f"\n{3 - len(failures)}/3 states behave")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
