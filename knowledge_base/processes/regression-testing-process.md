# Regression Testing Process

Regression testing checks that new changes have not broken existing features. This page explains how the TaskTrail team runs regression.

## The regression suite

- The full regression suite has **620 test cases**.
- **410** are automated with Appium and TestNG.
- **210** are manual (mostly visual checks and complex offline scenarios).
- Test cases have three priorities:
  - **P0**: run on every build
  - **P1**: run on every release candidate
  - **P2**: run once per month

## Nightly automated run

- The automated suite runs every night at **1:00 AM IST** against the QA environment.
- It runs on **4 devices in parallel** in the device farm and takes about **3 hours**.
- Results are published to the Regression Dashboard before the 10:15 AM stand-up.
- The Senior SDET (Arjun Mehta) owns the nightly pipeline.

## Pass rate target

The target pass rate is **95%**. If the nightly pass rate falls below 90%, the on-duty SDET must post a summary of failures in #tt-qa before 11 AM IST.

## Flaky test policy

A test is marked **flaky** when it fails **3 times in 10 runs** without a product bug. Flaky tests are:

1. Moved to the *quarantine* group, so they no longer block the pipeline.
2. Assigned to the test owner.
3. Fixed within **5 working days**, or deleted if the scenario is covered elsewhere.

No more than 15 tests may be in quarantine at the same time.

## Manual regression

Manual regression cases are split between the QA engineers according to module ownership (see QA Team Roles). Each engineer records results in CaseBook, the test management tool. Any failure must have a linked bug in the TT project.

## Regression scope

| Build type | Scope |
|---|---|
| Daily QA build | P0 automated tests |
| Release candidate | Full suite (P0 + P1 automated, all manual P0/P1) |
| Hotfix | Smoke test + full suite for the affected module |

## Reporting

The regression report includes the total cases run, pass/fail/blocked counts, the pass rate, new bugs found and a list of flaky tests.
