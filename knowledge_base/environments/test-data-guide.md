# Test Data Guide

Good test data makes bugs easy to reproduce. This guide explains which accounts and data to use.

## Test accounts

- Test accounts follow the pattern **qa.user01@tasktrail.example.com** to **qa.user20@tasktrail.example.com**.
- Passwords are stored in the **team password vault**. Never write passwords in documents, bug reports or chat.

| Accounts | Role | What the role can do |
|---|---|---|
| qa.user01 to qa.user10 | **Field Worker** | See and update only tasks assigned to them |
| qa.user11 to qa.user15 | **Supervisor** | See all tasks in their team, assign and reopen tasks |
| qa.user16 to qa.user20 | **Admin** | Manage users, teams and organisation settings |

All test accounts belong to the organisation **"Demo Org"** on the QA environment.

## Nightly data reset

A seed script resets the QA test data every night at **2 AM IST**. After the reset, every Field Worker account has 25 tasks: 10 To Do, 10 In Progress and 5 Done. If you need data to survive the reset, create it under the "Persistent QA" team and tell the QA Lead.

## Real customer data

Using real customer data for testing is **not allowed**. STAGING data is anonymised before it is copied. If you find real personal data anywhere in a test environment, report it to the QA Lead immediately.

## Photo test assets

The shared test assets folder contains images for photo upload testing:

- 1 MB JPG
- 5 MB JPG
- 20 MB PNG
- 25 MB JPG (the exact upload limit)
- 30 MB JPG (above the limit, should be rejected)
- HEIC samples taken on iPhone

## Offline testing data

- Use airplane mode to test offline behaviour.
- The offline sync queue holds up to **200 items**. When the queue is full, the app asks the user to connect before creating more items.
- To test large sync queues, use qa.user05, which is pre-loaded with 150 offline changes by the seed script.

## Creating new test data

Create new tasks with a title that starts with **"QA-"** followed by your initials, for example "QA-RD Check due date". This makes it easy to find and clean up your data.
