# QA Onboarding FAQ

Answers to the questions new QA team members ask most often.

**What should I do in my first week?**
Request access to the bug tracker, CaseBook, the device lab booking sheet, the team password vault and the VPN. Access requests can take up to **2 working days**, so raise them on day one.

**Will someone help me get started?**
Yes. Every new joiner gets a **buddy for their first 30 days**. Your buddy is assigned by the QA Lead, Priya Nair.

**Is there any training I must complete?**
Complete the **"TaskTrail Product Basics"** training within your first **14 days**. It covers all modules and the user roles.

**Where are the test cases?**
All manual and automated test cases are in **CaseBook**, our test management tool. Test cases are grouped by module.

**What automation stack do we use?**
Java, **Appium** and **TestNG**, following the **Page Object Model**. The code lives in the `tasktrail-mobile-tests` repository. API tests use REST Assured.

**How do code reviews work?**
Every pull request needs at least **1 approval**. For framework changes, the approval must come from Arjun Mehta. Pull requests must pass the P0 test run before merging.

**Which environment should I test on?**
Use the QA environment for daily testing. Use STAGING only for release candidate testing (VPN required).

**Where do I get test accounts?**
See the Test Data Guide. Passwords are in the team password vault.

**How do I get a test device?**
Book one from the device lab on the 3rd floor (maximum 4 hours a day). To request a new device for the lab, ask the QA Lead.

**What are the working hours for the team?**
Core hours are **10 AM to 6 PM IST**. The stand-up starts at 10:15 AM.

**How do I report a bug correctly?**
Follow the Bug Severity Guide. Always include the build number, device, OS version, environment, steps, expected and actual results, and a screenshot or video.

**Who do I ask if I am blocked?**
Ask the module owner first. If you are still blocked after 4 hours, ask the QA Lead.
