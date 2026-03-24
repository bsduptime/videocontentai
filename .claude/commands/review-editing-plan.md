---
description: Editorial review of an editing plan — quality check, improvements, verdict
allowed-tools: Bash, Read, Write, Glob, Grep
---

Review the editing plan for `$ARGUMENTS` and produce a reviewed plan + review summary.

## Overview

You are the **editorial reviewer** — a fresh pair of eyes on the editing plan. You have NO context from take selection. You load everything from scratch, review against the quality checklist, improve what you can, and produce a verdict.

**Slug**: `$ARGUMENTS` (e.g., `/review-editing-plan ai-wont-take-your-job`)

## Steps

### Step 1: Load Context (Fresh — No Carry-Over)

Read ALL of these files. You need complete context before reviewing anything.

**Editing plan (the thing you're reviewing):**
- `video-content/production/{slug}/editing-plan.md`

**Editorial reviewer skill:**
- `.claude/skills/editorial-reviewer/SKILL.md`

**Original script + coaching sidecar (from input):**
- Find the script `.md` and sidecar `.json` in `video-content/input/{slug}/`
- These contain the original intent: beat structure, VAD targets, mood assignments, segment types, delivery energy, coaching notes, extraction points

**Beat analysis data:**
- `video-content/production/{slug}/beats/beat_analysis.json` — actual VAD scores, emotion2vec labels, take metadata per beat

**Brand guide:**
- Determine brand from editing plan frontmatter
- If `davidk`: read the brand skill from `~/code/content/.claude/skills/davidk-brand/SKILL.md`

**Music system:**
- `~/code/content/strategy/cuts/moods.json` — 3 moods, VAD values, BPM, modifiers
- `~/code/content/strategy/cuts/music-placement-guide.md` — segment types, lookup tables, placement rules

**Voice profiles (for voiceover requests):**
- Check `voice-profiles/samples/` for available emotion profiles

If any required file is missing, stop and report what's missing.

### Step 2: Parse the Editing Plan

Extract from the plan:
- All beats with their metadata (take file, duration, mood, VAD target/actual, segment type, delivery energy, music mood/presence/volume, source type, transition)
- Music plan (track assignments, fade points, silence points)
- Voiceover requests
- Graphics/B-roll requests
- Pacing summary
- Open questions

### Step 3: Run the 7-Point Quality Checklist

Work through each check systematically. Reference specific values — not vibes.

#### Check 1: Beat Flow & Pacing

- **Total duration**: Compare `duration_estimate` against `duration_target`. Flag if outside ±10%.
- **Individual beat timing**: Flag any beat exceeding 120s of continuous talking head without a visual break.
- **The Drift zone (25-40% mark)**: Calculate which beats fall in this range. Are they the tightest beats? If not, flag with specific recommendation (trim, add visual break, increase energy).
- **Hook**: Must be ≤45s. First sentence must be ≤15 words. Must NOT open with credentials or context — must open with stakes or curiosity. Check against the script's hook.
- **Closer**: Must end with agency ("here's what to do") not summary ("so in conclusion"). Check the script's closing beat.
- **90-second wall**: Something must land (micro-payoff or open loop) before 1:30 cumulative. Check beat durations.

#### Check 2: VAD Delivery Match

For each beat, compare actual VAD against target VAD using these thresholds:

| Dimension | ✅ Match | ⚠️ Watch | ❌ Miss |
|-----------|---------|---------|--------|
| Each of V, A, D | ±0.15 | ±0.25 | >0.25 |

Cross-reference with `beat_analysis.json` to verify the editing plan's VAD actual values are correct. If there are alternative takes available in beat_analysis.json, check if any missed take would be a better VAD match.

For any ❌ miss:
- Check if an alternative take exists with better VAD
- If no better take, consider voiceover replacement (allowed for bridges/transitions/intros — NEVER for hook or climax)
- Flag for re-recording as last resort

#### Check 3: Music Placement Verification

For each beat, verify the music assignment against the lookup table:

| segment_type | delivery_energy | Expected music_presence | Expected volume |
|---|---|---|---|
| visual-only | any | full | -6 dB |
| narrated | 1-3 | moderate | -15 dB |
| narrated | 4-6 | low | -18 dB |
| narrated | 7-10 | very-low | -22 dB |
| dense | any | silent | mute |
| key-reveal | any | silence-to-reentry | fade→silence→re-enter |

Verify mood selection:
- Default: `drive` (best memory quadrant, d'≈2.75)
- Dense segments: `steady`
- Narrated + delivery_energy ≤4: `steady`
- Problem statements/stakes: **silence** (no music)

**Congruence check**: Flag any beat where music mood contradicts content emotion. Mismatch is worse than silence.

**Key-reveal pattern**: Every `key-reveal` beat MUST have: fade to silence over 3-5s before reveal → hold silence → re-enter on payoff. If missing, add it.

**Music during stakes**: Any music playing during problem statements or negative-valence beats → flag and recommend silence.

#### Check 4: Source Type & Visual Variety

- Flag >3 consecutive minutes of desk talking head with no visual break
- Flag mobile footage during dense technical explanation
- Flag screen recording without narration AND without music (dead air)
- For 10+ minute videos, note if mobile footage is entirely absent (opportunity, not requirement)

#### Check 5: Graphics, B-Roll & Voiceover Opportunities

**Add graphics requests when:**
- A stat/number is spoken aloud → should be text overlay (speaker expresses feeling, graphic shows number)
- A list of 3+ items → visual list overlay
- A before/after comparison → split screen
- A process/flow → simple diagram

**Add B-roll requests when:**
- Abstract concept needs visual metaphor
- Beat transition needs visual relief
- Drift zone needs pattern interrupt

**Add voiceover requests when:**
- Take has VAD ❌ miss but words are right → VO replacement with correct energy
- Transition needs narration over B-roll
- Intro/outro needs polish
- **NEVER** for hook or climax — must be authentic recorded delivery

Use the 8 emotion profiles from `voice-profiles/samples/`:
- `drive` (V0.70 A0.75 D0.75)
- `drive-wonder` (V0.80 A0.80 D0.50)
- `high-intensity-drive` (V0.75 A0.85 D0.80)
- `steady` (V0.65 A0.45 D0.50)
- `steady-empathy` (V0.75 A0.45 D0.25)
- `reflective-calm` (V0.60 A0.30 D0.40)

#### Check 6: Transition Quality

Between every pair of beats:
- **Energy continuity**: No jarring jumps without a breath/bridge. Flag high→low or low→high without transition.
- **Music transitions**: Must be fades, not cuts. Abrupt endings wipe short-term buffer.
- **Visual transitions**: Source type changes need a visual beat (no hard-cut desk→beach mid-sentence).
- **Narrative bridges**: Does the viewer understand why we moved to the next topic?

#### Check 7: Brand Compliance

- **Credential**: Full credential line appears exactly ONCE (hook or setup). Flag duplicates.
- **Terminology**: Check against the translation table from the brand skill. No raw jargon (AI agent, LLM, autonomous, RAG, etc.) without plain-language introduction first.
- **Tone**: Practitioner not pundit. Warm not lecturing. Flag anything that sounds like TED talk or LinkedIn post.
- **dbexpertAI mentions**: Credential only. Never a CTA. Never "check out dbexpertAI."
- **Visual identity**: Warm neutrals (#1A1816, #F5F0EB, #D9A96D). DK watermark. No tech/cyber aesthetic.

### Step 4: Common Mistakes Scan

Check for all 10 common editing mistakes from the SKILL.md:

1. Opening with context instead of stakes/curiosity
2. Stats spoken as numbers (should be graphics)
3. Credential dumping (repeated in hook AND setup)
4. 90-second wall — no payoff before 1:30
5. Monotone middle — arousal below 0.40 for 2+ consecutive beats
6. Missing pattern interrupts — 2+ minutes with no visual change
7. Music during stakes/problems — should be silence
8. Music during dense content
9. No key-reveal silence for the jaw-drop moment
10. Abrupt endings (music or video cuts instead of fades)

### Step 5: Make Improvements

You have authority to modify the editing plan directly. For each change:

**You CAN do (without approval):**
- Rearrange beat order for better narrative flow
- Flag weak takes and recommend alternatives from available takes
- Adjust music mood assignments (within the 3-mood system + lookup table)
- Add graphics/subtitle/B-roll requests
- Add voiceover requests (text + emotion profile + placement)
- Add translation/subtitle requests
- Flag pacing issues and suggest trims
- Fix any lookup table mismatches (wrong music presence/volume for segment type + delivery energy)

**You CANNOT do (needs David's approval — add to Open Questions):**
- Delete entire beats
- Change the core narrative arc (ABT, story shape)
- Override take selections where VAD scores match targets (all ✅)
- Add new content not in the script
- Change hook type or grand payoff
- Modify YouTube packaging

### Step 6: Write the Reviewed Editing Plan

Copy the editing plan structure, applying all your modifications inline. Write to:

```
video-content/production/{slug}/editing-plan-reviewed.md
```

Update the frontmatter `status` from `"draft"` to `"reviewed"`.

The reviewed plan follows the exact same format as the original (see `docs/editing-plan-format.md`), with your changes applied. Add `> REVIEW:` blockquotes inline where you made changes, explaining what changed and why:

```markdown
> REVIEW: Changed music mood from drive to silence — beat contains problem statement/stakes, silence is correct for negative-valence content.
```

### Step 7: Write the Review Summary

Write to:

```
video-content/production/{slug}/review-summary.md
```

Format:

```markdown
# Editorial Review: {slug}

**Reviewer**: Editorial Review Agent
**Date**: {YYYY-MM-DD}
**Editing plan**: `production/{slug}/editing-plan.md`
**Reviewed plan**: `production/{slug}/editing-plan-reviewed.md`

---

## Verdict: {✅ Approved | ⚠️ Approved with Notes | ❌ Needs Revision | 🚫 Blocked}

{One-sentence summary of the verdict.}

---

## Issues Found

### ❌ Must Fix (blocks assembly)
- **{issue name}**: {what's wrong} → {fix applied or recommended action}

### ⚠️ Should Fix (improves quality)
- **{issue name}**: {what's wrong} → {fix applied or recommended action}

### 💡 Suggestions (optional improvements)
- **{opportunity}**: {what could be better} → {suggestion}

---

## Beat-by-Beat Review

| Beat | Name | VAD Match | Music OK | Visual OK | Transitions | Notes |
|------|------|-----------|----------|-----------|-------------|-------|
| 1 | Hook | ✅ | ✅ | ✅ | ✅ | — |
| 2 | Setup | ⚠️ A+0.20 | ✅ | ❌ | ✅ | Added graphic at 1:15 |
| ... | | | | | | |

---

## Changes Made to Plan

| # | Beat/Section | Change | Reason |
|---|---|---|---|
| 1 | Beat 3 | Added stat-overlay graphic request | Stat spoken as number — should be visual |
| 2 | Music Plan | Added key-reveal silence at 2:50 | Jaw-drop moment had music playing through |
| ... | | | |

---

## Voiceover Requests Added

| # | Text | Profile | VAD Target | Placement | Beat |
|---|---|---|---|---|---|
| 1 | "{text}" | {profile} | V{v} A{a} D{d} | {placement} | {beat} |

## Graphics Requests Added

| # | Type | Description | Beat | Timecode |
|---|---|---|---|---|
| 1 | {type} | {description} | {beat} | ~{timecode} |

---

## Questions for David

- [ ] {Question requiring human judgment}
- [ ] {Question about creative direction}

---

## Checklist Results

| Check | Result | Notes |
|---|---|---|
| 1. Beat Flow & Pacing | ✅ | Duration 7:52 vs 8:00 target (within ±10%) |
| 2. VAD Delivery Match | ⚠️ | Beat 4: valence 0.20 below target |
| 3. Music Placement | ✅ | All assignments match lookup table |
| 4. Source Type & Visual | ✅ | Good mix of desk + mobile |
| 5. Graphics & B-Roll | ⚠️ | Added 2 missing stat overlays |
| 6. Transition Quality | ✅ | All transitions have fades |
| 7. Brand Compliance | ✅ | Single credential, no jargon |

---

## Next Step

{If approved}: Ready for David's final review. After approval, proceed to assembly.
{If needs revision}: {What needs to happen before re-review.}
{If blocked}: {Specific questions that must be answered before proceeding.}
```

### Step 8: Summary

Print:

```
## Editorial Review Complete

**Slug**: {slug}
**Verdict**: {verdict}
**Issues**: {N} must-fix, {N} should-fix, {N} suggestions
**Changes made**: {N} modifications to the plan
**Voiceover requests**: {N} added
**Graphics requests**: {N} added
**Questions for David**: {N}

Reviewed plan: video-content/production/{slug}/editing-plan-reviewed.md
Review summary: video-content/production/{slug}/review-summary.md

{If approved}: Ready for David's final approval → assembly.
{If needs revision}: See review summary for required changes.
{If blocked}: Waiting on answers from David — see Questions section.
```

$ARGUMENTS
