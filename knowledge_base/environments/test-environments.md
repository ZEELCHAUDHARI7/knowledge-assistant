# Test Environments

TaskTrail has four environments. All URLs below are internal example addresses.

| Environment | URL | Deploys | Used for |
|---|---|---|---|
| **DEV** | dev.tasktrail.example.com | Many times a day | Developer testing only; often unstable |
| **QA** | qa.tasktrail.example.com | Every day at **11 AM IST** | Main environment for daily QA testing |
| **STAGING** | staging.tasktrail.example.com | Release candidates only | Release testing; mirrors production |
| **PROD** | app.tasktrail.example.com | Release day | Real customers |

## Rules for each environment

### QA
- This is where most testing happens.
- Test data is reset every night at 2 AM IST (see Test Data Guide).
- If QA is down, post in the **#tt-devops** channel and tag the DevOps on-call engineer.

### STAGING
- STAGING uses the same configuration as production.
- **VPN is required** to access STAGING.
- Data on STAGING is refreshed from an anonymised copy of production every **Sunday**.
- Release candidate testing and the Go/No-Go test summary are based on STAGING results.

### PROD
- Never create test data in production.
- The only allowed testing is the post-release smoke test using the dedicated production test account.

## Getting mobile builds

- **Android:** builds are shared through the internal "App Tester" distribution channel. Each build shows its build number in Settings → About.
- **iOS:** builds are shared through TestFlight. Ask the QA Lead to add your Apple ID.

## Feature flags

Feature flags are managed in the **Flag Console**. QA engineers can switch flags on the QA environment only. Important flags right now:

- `photo_compression_v2`: new photo compression (see Photo Upload Module)
- `offline_sync_banner`: shows a banner when there are unsynced changes

Always write the flag state in your bug report if the bug is related to a flagged feature.

## API testing

The API base URL for QA is `qa-api.tasktrail.example.com/v2`. API tests are owned by Sara Khan and run in the CI pipeline on every merge.
