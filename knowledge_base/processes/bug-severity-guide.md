# Bug Severity Guide

This guide explains how the TaskTrail QA team decides the severity of a bug. Severity describes the **impact on users**. It is set by the QA engineer who logs the bug. Priority (how soon we fix it) is set by the Product Owner, Daniel Okafor.

## Severity levels

| Severity | Meaning | Examples | Expected fix time |
|---|---|---|---|
| **S1 (Critical)** | The app is unusable or data is lost, and there is no workaround | Crash on launch, tasks deleted after sync, login blocked for all users | Response within **2 hours**, fixed before any release |
| **S2 (High)** | A major feature is broken and there is no workaround | Photos cannot be uploaded, supervisor cannot reassign tasks | Within **2 working days** |
| **S3 (Medium)** | A feature is broken but a workaround exists | Filter resets after closing the app, wrong sort order | Within the **current sprint** (sprints last 2 weeks) |
| **S4 (Low)** | Cosmetic or text problems | Typos, misaligned icons, wrong colour | Added to the backlog |

## Rules for Critical bugs

- Notify the QA Lead (Priya Nair) and the Release Manager (Lucas Fernandes) on the #tt-release channel immediately.
- A release cannot go ahead while any S1 bug is open.
- Only S1 bugs are allowed into a hotfix build.

## What every bug report must contain

1. Build number (for example 4.8.0 build 512)
2. Device model and OS version
3. Test environment (QA, STAGING or PROD)
4. Clear steps to reproduce
5. Expected result and actual result
6. Screenshot or screen recording
7. Device logs for crashes

## Where bugs are logged

All bugs go into the **TT** project in the bug tracker. Add the module label using the format `module-<name>`, for example `module-photo-upload`. Duplicate bugs should be linked to the original and closed as "Duplicate".

## Common mistakes

- Setting severity based on how annoying the bug is to the tester, not the impact on the user.
- Marking every crash as Critical. A crash in a rarely used settings screen with an easy workaround can be S2.
- Forgetting to re-check severity after the root cause is found.

Bug triage meetings happen every **Tuesday and Friday at 3 PM IST**. Severity can be changed during triage if the team agrees.
