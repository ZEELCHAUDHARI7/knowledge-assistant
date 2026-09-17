# Release Checklist

TaskTrail ships a new mobile release **every second Thursday**. This checklist must be completed before any release is approved.

## Release week timeline

| When | What happens |
|---|---|
| Monday, 6 PM IST | **Code freeze.** No new features after this point. |
| Tuesday, 12 PM IST | Release candidate (RC) build shared with QA |
| Tuesday and Wednesday | Smoke test and regression on STAGING |
| Wednesday, 4 PM IST | **Go/No-Go meeting** |
| Thursday | Release to the stores |

## Quality gates (all must pass)

- [ ] Smoke test completed: **45 test cases**, takes about 2 hours
- [ ] Regression pass rate is **95% or higher**
- [ ] **Zero** open Critical (S1) bugs
- [ ] At most **3** open High (S2) bugs, each with written sign-off from the Product Owner
- [ ] Crash-free sessions in the beta group are **99.5% or higher**
- [ ] Release notes reviewed by the QA Lead
- [ ] Tier 1 devices tested (see the Device Matrix)

## Go/No-Go meeting

Attendees: QA Lead (Priya Nair), Release Manager (Lucas Fernandes), Product Owner (Daniel Okafor) and one developer lead. The QA Lead presents the test summary. If any quality gate fails, the release is postponed to the following Thursday unless the Product Owner and QA Lead both agree to an exception.

## Rollout plan

- **Android:** staged rollout 10% → 50% → 100% over 3 days. The rollout is paused if crash-free sessions drop below 99%.
- **iOS:** phased release over 7 days.
- After release, the QA team runs a production smoke test with the dedicated production test account within 1 hour.

## Hotfix releases

A hotfix is only allowed for Critical (S1) bugs. Hotfix builds use a branch named `hotfix/x.y.z`. The regression scope for a hotfix is the smoke test plus the full test suite of the affected module. A hotfix still needs sign-off from the QA Lead.

## After the release

- Update the release notes page.
- Move any unfinished bugs to the next sprint.
- Hold a 30-minute release retrospective on the Friday after release.
