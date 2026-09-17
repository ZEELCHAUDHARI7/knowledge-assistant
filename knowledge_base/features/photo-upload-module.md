# Photo Upload Module

Field workers attach photos to tasks as proof of work. This page describes how photo upload works and what to test.

## Limits

- Up to **10 photos per task**.
- Maximum upload size is **25 MB per photo**. Larger files are rejected with the message: *"File too large (max 25 MB)"*.
- Supported formats: **JPG, PNG and HEIC**. HEIC photos are converted to JPG during upload.

## Compression

When the feature flag `photo_compression_v2` is **on**, photos larger than **5 MB** are compressed to about **2 MB** before upload. When the flag is off, photos are uploaded at their original size. Always note the flag state in bug reports about photo quality or upload time.

## Watermark

Every photo gets a watermark in the bottom-right corner with:

- the date and time the photo was taken
- the GPS location (if location permission is granted)

If location permission is denied, the watermark shows "Location unavailable".

## Offline uploads

- Photos taken offline are added to the upload queue.
- The app retries a failed upload every **15 minutes**, up to **5 attempts**.
- After 5 failed attempts, the photo is marked "Upload failed" and the user can retry manually.

## Mobile data warning

If the total size of photos waiting to upload is more than **50 MB** and the device is on mobile data, the app asks the user whether to continue or wait for Wi-Fi.

## Known issues

- **TT-2231:** HEIC photos can appear rotated by 90 degrees after upload on some Android 12 devices. Status: In Progress.
- **TT-2240:** The progress bar sometimes jumps from 60% to 100%. Status: Open, Low severity.

## Key test areas

- Upload at exactly 25 MB (should pass) and 30 MB (should fail)
- 10 photos and an 11th photo on one task
- HEIC conversion and rotation
- Compression on and off
- Offline queue retries and the "Upload failed" state
- Mobile data warning above 50 MB
- Watermark with and without location permission
