---
description: Push finished video output to Synology NAS for team review
allowed-tools: Bash, Read, Glob
---

Push finished output for a slug to the Synology NAS so the team can review in Synology Photos.

**Slug**: `$ARGUMENTS`

## Step 1: Validate

If `$ARGUMENTS` is empty, report "Usage: /push-output {slug}" and stop.

Check that the local output directory exists and has files:

```bash
ls video-content/output/{slug}/
```

If the directory doesn't exist or is empty, report "No output found for slug: {slug}" and stop.

## Step 2: Inventory local output

List all files with sizes:

```bash
find video-content/output/{slug}/ -type f -exec ls -lh {} \;
```

Print a table:

```
| # | File | Size |
|---|------|------|
| 1 | final.mp4 | 48MB |
```

And compute total size:

```bash
du -sh video-content/output/{slug}/
```

## Step 3: Create destination on NAS

```bash
ssh nas "mkdir -p /volume1/photo/ContentOutput/{slug}"
```

## Step 4: Push files via scp

The NAS does not have rsync. Use scp to push files.

```bash
scp -r video-content/output/{slug}/* "nas:/volume1/photo/ContentOutput/{slug}/"
```

If scp fails, report the error and stop.

## Step 5: Verify remote files

List what landed on the NAS to confirm:

```bash
ssh nas "ls -lh /volume1/photo/ContentOutput/{slug}/"
```

## Step 6: Summary

```
## Push Output Summary

Slug: {slug}
Destination: nas:/volume1/photo/ContentOutput/{slug}/
Files pushed: {count}
Total size: {size}

Local copy retained at: video-content/output/{slug}/
```

$ARGUMENTS
