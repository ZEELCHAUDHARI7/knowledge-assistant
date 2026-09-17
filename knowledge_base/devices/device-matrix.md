# Device Matrix

This page lists the devices and operating system versions the TaskTrail app supports and which devices the QA team must test on.

## Minimum supported versions

- **Android 10 (API level 29)** or newer
- **iOS 16** or newer

Devices below these versions cannot install the app from the stores.

## Tier 1: test on every release

| Device | OS version |
|---|---|
| Samsung Galaxy S23 | Android 14 |
| Google Pixel 7 | Android 14 |
| iPhone 14 | iOS 17 |
| iPhone 12 | iOS 16 |

Tier 1 devices run the full smoke test and the manual regression cases for every release candidate.

## Tier 2: test on every second release

| Device | OS version |
|---|---|
| Samsung Galaxy A52 | Android 13 |
| Xiaomi Redmi Note 11 | Android 12 |
| iPad (9th generation) | iOS 17 |

## Tier 3: performance checks only

| Device | OS version |
|---|---|
| Samsung Galaxy A12 | Android 11 |

The Galaxy A12 is our low-end reference device. The app must open in **under 4 seconds** on it (cold start), and the task list must scroll smoothly with 500 tasks.

## Tablets

Tablets are supported in both portrait and landscape. Layout bugs that only appear on tablets are usually S3 (Medium).

## Device lab

- The device lab is on the **3rd floor**.
- Book devices using the device booking sheet.
- The maximum booking time is **4 hours** per person per day.
- Return devices charged to at least 50%.
- To request a new test device, raise a request with the QA Lead, Priya Nair, and include the reason and the user share of that device.

## Device farm

Automated tests run on the device farm, which has 4 Android and 4 iOS devices available for parallel runs. Arjun Mehta manages the device farm configuration.
