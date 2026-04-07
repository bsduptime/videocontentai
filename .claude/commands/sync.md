---
description: Sync git — update memory, docs, then stash/pull/push to main
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Agent
---

Sync the repo to main. Follow these steps in order, stopping to discuss with the user if anything is non-trivial.

## Step 1: Review uncommitted changes

Run `git status` and `git diff --stat`. Summarize what's changed.

## Step 2: Update memory and docs

Before syncing, check if any changes warrant updates to:

1. **Memory** (`~/.claude/projects/-home-dbexpertai-code-videocontentai/memory/`) — update or add memory files if the changes reveal new project context, architecture decisions, or user preferences worth remembering. Check MEMORY.md index too.
2. **CLAUDE.md** — if one exists at repo root, update it to reflect any new conventions, commands, or project structure changes.
3. **README.md** — if the changes add/remove features, commands, config, or dependencies that are documented in README.md, update it to stay accurate.

Only touch docs that genuinely need updating. Don't force changes.

## Step 3: Commit uncommitted work

If there are uncommitted changes (including any doc/memory updates from Step 2), create a well-described commit grouping related changes logically.

## Step 4: Sync with remote

Try this sequence:

1. `git stash` any remaining uncommitted changes (if any)
2. `git pull --rebase origin main`
3. If rebase succeeds cleanly → `git stash pop` (if stashed) → `git push origin main`
4. If there are conflicts or the merge is non-trivial → **stop and show the user**:
   - What conflicts exist
   - What the remote changes look like (`git log --oneline origin/main..HEAD` and vice versa)
   - Ask how they want to resolve it

## Important

- If push fails (e.g., protected branch, auth issue), report the error clearly.
- Never force-push unless the user explicitly says to.
- If the pull reveals significant remote changes, summarize them before pushing.
- Always show the final state: `git log --oneline -5` and `git status`.
