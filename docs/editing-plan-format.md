# Editing Plan Format

The editing plan is the structured output of Phase 2 (take selection) and the input to Phase 3 (editorial review). It captures every decision needed to assemble the final video.

**Produced by**: `check-readiness` command (take selection step)
**Consumed by**: `review-editing-plan` command (editorial reviewer)
**Location**: `production/{slug}/editing-plan.md`

---

## Format Specification

### Header

```yaml
---
slug: "{slug}"
date: "{YYYY-MM-DD}"
script_ref: "input/{slug}/{YYYY-MM-DD}-{slug}.md"
sidecar_ref: "input/{slug}/{YYYY-MM-DD}-{slug}.json"
brand: "{davidk|dbexpertai}"
content_mode: "{demos|futures|human-edge|walkthroughs|reframes|insider}"
duration_target: "{N}min"
duration_estimate: "{M}min {S}s"
total_beats: {N}
hook_type: "{hook type}"
story_shape: "{rise|fall-rise|rise-fall|rags-to-riches|steady-climb}"
abt: "{ABT sentence}"
status: "draft"
---
```

### Beat Sequence Table

Each beat is a level-2 heading with a metadata table and notes.

```markdown
## Beat {N}: {Beat Name}

| Field | Value |
|---|---|
| **Take file** | `beats/beat-{NN}-{name}-take-{T}.mp4` |
| **Duration** | {duration}s |
| **Mood** | {drive\|tension\|steady} |
| **VAD target** | V{v} A{a} D{d} |
| **VAD actual** | V{v} A{a} D{d} |
| **VAD match** | ✅ \| ⚠️ \| ❌ (per dimension ±0.15/±0.25) |
| **Segment type** | {visual-only\|narrated\|dense\|key-reveal} |
| **Delivery energy** | {1-10} |
| **Music mood** | {drive\|tension\|steady} |
| **Music presence** | {full\|moderate\|low\|very-low\|silent\|silence-to-reentry} |
| **Music volume** | {-6\|-15\|-18\|-22\|mute} dB |
| **Source type** | {talking-head-desk\|talking-head-mobile\|screen-recording} |
| **Transition out** | {fade\|cut-on-action\|bridge-vo\|music-fade\|visual-break} to Beat {N+1} |

**Notes**: {any beat-specific notes — alternate takes available, splice points, delivery concerns}
```

### Music Plan

```markdown
## Music Plan

### Track Assignments

| Time Range | Beat(s) | Mood Track | Presence | Volume | BPM | Notes |
|---|---|---|---|---|---|---|
| 0:00–0:45 | 1 Hook | drive | very-low | -22 dB | 120 | High delivery energy, music pulled back |
| 0:45–2:00 | 2 Setup | steady | low | -18 dB | 80 | Calm narration |
| ... | ... | ... | ... | ... | ... | ... |

### Fade Points

- **{timecode}**: Fade {mood} to silence over {N}s — entering key-reveal
- **{timecode}**: Cross-fade {mood1} → {mood2} over {N}s — mood transition

### Silence Points (Key-Reveal Pattern)

- **{timecode}–{timecode}**: Silence for key reveal in Beat {N} ("{reveal text}")
- **{timecode}**: Music re-entry on payoff line

### BPM Reference

- drive: 120 BPM
- tension: 120 BPM
- steady: 80 BPM (3:2 ratio with drive/tension — rhythmically congruent downshift)
```

### Voiceover Requests

```markdown
## Voiceover Requests

| # | Text | Emotion Profile | VAD Target | Placement | Beat | Timecode |
|---|---|---|---|---|---|---|
| 1 | "{voiceover text}" | {profile name} | V{v} A{a} D{d} | {bridge\|intro\|transition\|outro} | Between {N}→{N+1} | ~{timecode} |
```

**Available emotion profiles** (from `voice-profiles/samples/`):

| Profile | Mood | VAD Approximate | Best For |
|---|---|---|---|
| `drive` | drive | V0.70 A0.75 D0.75 | Confident narration, CTAs, positive energy |
| `drive-wonder` | drive+wonder | V0.80 A0.80 D0.50 | Awe moments, fascinating reveals |
| `high-intensity-drive` | drive (high) | V0.75 A0.85 D0.80 | Climax narration, peak energy |
| `steady` | steady | V0.65 A0.45 D0.50 | Tutorial narration, calm explanation |
| `steady-empathy` | steady+empathy | V0.75 A0.45 D0.25 | Empathetic moments, audience validation |
| `tension` | tension | V0.25 A0.75 D0.70 | Urgent problem statements, stakes |
| `tension-vulnerability` | tension+vulnerability | V0.25 A0.60 D0.30 | Honest admissions, real concern |
| `reflective-calm` | — | V0.60 A0.30 D0.40 | Thoughtful bridges, contemplative moments |

### Graphics / B-Roll Requests

```markdown
## Graphics & B-Roll Requests

| # | Type | Description | Beat | Timecode | Duration | Notes |
|---|---|---|---|---|---|---|
| 1 | stat-overlay | "95% of DBAs spend 6+ hours on routine tasks" | 3 | ~2:15 | 5s | Speaker says feeling, graphic shows number |
| 2 | list | 3 skills that can't be automated | 5 | ~5:30 | 8s | Animate items sequentially |
| 3 | b-roll | Beach walk footage | 4→5 transition | ~4:45 | 3s | Visual break, bridge narration over |
| 4 | diagram | Before/after workflow | 6 | ~7:00 | 10s | Split screen: manual vs AI-assisted |
```

### Subtitle / Translation Notes

```markdown
## Subtitle & Translation Notes

- **Primary language**: {language}
- **Subtitle style**: {burned-in\|sidecar-srt\|both}
- **Translation targets**: {list of languages, or "none"}
- **Special notes**: {e.g., "Technical terms need glossary subs", "Hebrew subtitles for IL audience"}
```

### Pacing Summary

```markdown
## Pacing Summary

- **Total beats**: {N}
- **Total estimated duration**: {M}min {S}s (target: {T}min)
- **Average beat duration**: {X}s
- **Longest beat**: Beat {N} ({name}) at {X}s
- **Shortest beat**: Beat {N} ({name}) at {X}s

### Energy Arc

```
Beat:    1    2    3    4    5    6    7    8
Energy: [████ ][██  ][███ ][████ ][██  ][█████][█████][███ ]
Mood:    ten   sted  drv   drv    sted  drv    drv    sted
         Hook  Setup Body1 Body2  Bridg Body3  Climax Close
```

### Drift Zone Check (25-40% of duration)

- Beats in drift zone: {list}
- Assessment: {tight/needs-tightening/flagged}
```

### Open Questions

```markdown
## Open Questions

- [ ] {Question for David — e.g., "Beat 4 take-1 has a stumble at 3:22 but better energy than take-2. Splice or use take-2?"}
- [ ] {Question — e.g., "Hook opens with context instead of tension. Re-record or rewrite VO?"}
```

---

## Complete Example

```markdown
---
slug: "ai-wont-take-your-job"
date: "2026-03-24"
script_ref: "input/ai-wont-take-your-job/2026-03-24-ai-wont-take-your-job.md"
sidecar_ref: "input/ai-wont-take-your-job/2026-03-24-ai-wont-take-your-job.json"
brand: "davidk"
content_mode: "reframes"
duration_target: "8min"
duration_estimate: "7min 52s"
total_beats: 6
hook_type: "Myth Hook"
story_shape: "fall-rise"
abt: "Everyone thinks AI will replace them AND they're scrambling to learn prompting, BUT the real risk isn't AI — it's other humans using AI better, THEREFORE the winning move is doubling down on skills AI can't touch."
status: "draft"
---

## Beat 1: Hook

| Field | Value |
|---|---|
| **Take file** | `beats/beat-01-hook-take-2.mp4` |
| **Duration** | 38s |
| **Mood** | tension |
| **VAD target** | V0.25 A0.75 D0.70 |
| **VAD actual** | V0.30 A0.80 D0.65 |
| **VAD match** | ✅V ✅A ✅D |
| **Segment type** | narrated |
| **Delivery energy** | 8 |
| **Music mood** | drive |
| **Music presence** | very-low |
| **Music volume** | -22 dB |
| **Source type** | talking-head-mobile |
| **Transition out** | cut-on-action to Beat 2 |

**Notes**: Take-2 selected over take-1 (take-1 had flat arousal A0.55). Beach walk footage, morning light. First sentence: 11 words.

---

## Beat 2: Setup

| Field | Value |
|---|---|
| **Take file** | `beats/beat-02-setup-take-1.mp4` |
| **Duration** | 72s |
| **Mood** | steady |
| **VAD target** | V0.65 A0.45 D0.50 |
| **VAD actual** | V0.60 A0.50 D0.55 |
| **VAD match** | ✅V ✅A ✅D |
| **Segment type** | narrated |
| **Delivery energy** | 5 |
| **Music mood** | steady |
| **Music presence** | low |
| **Music volume** | -18 dB |
| **Source type** | talking-head-desk |
| **Transition out** | music-fade to Beat 3 |

**Notes**: Clean single take. Credential line delivered naturally at 0:55 — "I run a company where AI agents manage databases — no human DBA watching the screen."

---

## Beat 3: Body 1 — The Real Threat

| Field | Value |
|---|---|
| **Take file** | `beats/beat-03-body1-take-1.mp4` |
| **Duration** | 85s |
| **Mood** | tension |
| **VAD target** | V0.25 A0.75 D0.70 |
| **VAD actual** | V0.28 A0.70 D0.68 |
| **VAD match** | ✅V ✅A ✅D |
| **Segment type** | key-reveal |
| **Delivery energy** | 7 |
| **Music mood** | drive |
| **Music presence** | silence-to-reentry |
| **Music volume** | fade→mute→-22 dB |
| **Source type** | talking-head-desk |
| **Transition out** | bridge-vo to Beat 4 |

**Notes**: Key stat reveal at ~2:55 — "3 out of 4 companies already using AI in hiring." Stat goes to graphic, David says "Almost every company you'd apply to is already using this." Silence starts at 2:50, re-entry at 3:02.

---

## Beat 4: Body 2 — Skills That Can't Be Automated

| Field | Value |
|---|---|
| **Take file** | `beats/beat-04-body2-take-2.mp4` |
| **Duration** | 90s |
| **Mood** | drive |
| **VAD target** | V0.70 A0.75 D0.75 |
| **VAD actual** | V0.65 A0.70 D0.72 |
| **VAD match** | ✅V ✅A ✅D |
| **Segment type** | narrated |
| **Delivery energy** | 7 |
| **Music mood** | drive |
| **Music presence** | very-low |
| **Music volume** | -22 dB |
| **Source type** | talking-head-desk |
| **Transition out** | visual-break to Beat 5 |

**Notes**: Take-2 selected — better energy arc. Take-1 available as backup (slightly lower arousal). List of 3 skills enumerated — needs graphic overlay.

---

## Beat 5: Climax — The Reframe

| Field | Value |
|---|---|
| **Take file** | `beats/beat-05-climax-take-1.mp4` |
| **Duration** | 75s |
| **Mood** | drive |
| **VAD target** | V0.80 A0.80 D0.50 |
| **VAD actual** | V0.75 A0.78 D0.55 |
| **VAD match** | ✅V ✅A ✅D |
| **Segment type** | narrated |
| **Delivery energy** | 9 |
| **Music mood** | drive |
| **Music presence** | very-low |
| **Music volume** | -22 dB |
| **Source type** | talking-head-desk |
| **Transition out** | music-fade to Beat 6 |

**Notes**: Peak energy. VAD target includes wonder modifier (V+0.10, A+0.05, D-0.25 applied to drive base). Strong delivery — jaw-drop moment lands at ~6:10.

---

## Beat 6: Close

| Field | Value |
|---|---|
| **Take file** | `beats/beat-06-close-take-1.mp4` |
| **Duration** | 52s |
| **Mood** | steady |
| **VAD target** | V0.75 A0.45 D0.25 |
| **VAD actual** | V0.70 A0.50 D0.30 |
| **VAD match** | ✅V ✅A ✅D |
| **Segment type** | narrated |
| **Delivery energy** | 5 |
| **Music mood** | steady |
| **Music presence** | low |
| **Music volume** | -18 dB |
| **Source type** | talking-head-mobile |
| **Transition out** | fade to outro |

**Notes**: Empathy modifier applied (V+0.10, D-0.25 from steady base). Ends with agency: "Pick one skill AI can't do. Get better at it this week." Beach walk closer — warm, human.

---

## Music Plan

### Track Assignments

| Time Range | Beat(s) | Mood Track | Presence | Volume | BPM | Notes |
|---|---|---|---|---|---|---|
| 0:00–0:38 | 1 Hook | drive | very-low | -22 dB | 120 | High delivery energy (8), music pulled back |
| 0:38–1:50 | 2 Setup | steady | low | -18 dB | 80 | Calm narration, moderate delivery |
| 1:50–2:50 | 3 Body 1 (pre-reveal) | drive | very-low | -22 dB | 120 | Building to key reveal |
| 2:50–3:02 | 3 Body 1 (reveal) | — | silent | mute | — | Key-reveal silence pattern |
| 3:02–3:15 | 3 Body 1 (payoff) | drive | very-low | -22 dB | 120 | Re-entry on payoff |
| 3:15–4:45 | 4 Body 2 | drive | very-low | -22 dB | 120 | High delivery, music stays back |
| 4:45–4:48 | Transition | — | — | — | — | Visual break (B-roll, 3s) |
| 4:48–6:03 | 5 Climax | drive | very-low | -22 dB | 120 | Peak energy (9), music minimal |
| 6:03–6:55 | 6 Close | steady | low | -18 dB | 80 | Wind down, warm close |
| 6:55–7:05 | Outro | drive | full | -6 dB | 120 | No narration, music carries |

### Fade Points

- **1:50**: Cross-fade steady → drive over 3s — entering Body 1
- **2:50**: Fade drive to silence over 4s — entering key-reveal
- **6:03**: Cross-fade drive → steady over 3s — entering close
- **6:55**: Fade steady → drive over 2s — entering outro

### Silence Points (Key-Reveal Pattern)

- **2:50–3:02**: Silence for key reveal in Beat 3 ("Almost every company you'd apply to is already using this")
- **3:02**: Music re-entry on "But here's what they're NOT looking for..."

### BPM Reference

- drive: 120 BPM
- tension: 120 BPM (same BPM, minor key — no tempo disruption on transitions)
- steady: 80 BPM (3:2 ratio — rhythmically congruent downshift)

---

## Voiceover Requests

| # | Text | Emotion Profile | VAD Target | Placement | Beat | Timecode |
|---|---|---|---|---|---|---|
| 1 | "And this is where most people get it backwards." | drive | V0.70 A0.75 D0.75 | bridge | 3→4 | ~3:15 |
| 2 | "Let's talk about what actually matters." | steady-empathy | V0.75 A0.45 D0.25 | transition | 4→5 | ~4:45 |

---

## Graphics & B-Roll Requests

| # | Type | Description | Beat | Timecode | Duration | Notes |
|---|---|---|---|---|---|---|
| 1 | stat-overlay | "75% of companies now use AI in hiring decisions" | 3 | ~2:55 | 4s | Speaker expresses feeling, graphic shows stat |
| 2 | list | "Negotiation / Judgment / Relationships" — 3 un-automatable skills | 4 | ~4:00 | 6s | Animate sequentially as David names each |
| 3 | b-roll | Beach/street walk footage | 4→5 | ~4:45 | 3s | Visual break between body and climax |
| 4 | text-overlay | "The skill that compounds: judgment under uncertainty" | 5 | ~5:45 | 5s | Reinforce the reframe |
| 5 | lower-third | "David K — Founder, dbexpertAI" | 2 | ~0:55 | 4s | On credential line, subtle |

---

## Subtitle & Translation Notes

- **Primary language**: English
- **Subtitle style**: sidecar-srt
- **Translation targets**: Hebrew (IL audience)
- **Special notes**: Key stat in Beat 3 should have burned-in subtitle for emphasis

---

## Pacing Summary

- **Total beats**: 6
- **Total estimated duration**: 7min 52s (target: 8min) ✅ within ±10%
- **Average beat duration**: 69s
- **Longest beat**: Beat 4 (Body 2) at 90s
- **Shortest beat**: Beat 1 (Hook) at 38s

### Energy Arc

```
Beat:    1    2    3    4    5    6
Energy: [████ ][██▌  ][███▌ ][███▌ ][█████][██▌  ]
Mood:    ten   sted   ten    drv    drv    sted
         Hook  Setup  Body1  Body2  Climax Close
```

### Drift Zone Check (25-40% of duration ≈ 1:58–3:09)

- Beats in drift zone: Beat 3 (Body 1 — The Real Threat)
- Assessment: **tight** — key-reveal pattern creates peak attention moment in the drift zone. No concerns.

---

## Open Questions

- [ ] Beat 4 take-2 has slightly lower valence than target (0.65 vs 0.70). Accept or check take-1?
- [ ] Hebrew subtitle scope — full video or key sections only?
- [ ] Outro card — use standard DK template or custom for this topic?
```

---

## Notes on Agent Parsing

The editing plan is designed to be both human-readable and agent-parseable:

- **YAML frontmatter** provides structured metadata for programmatic access
- **Beat tables** use consistent `| Field | Value |` format — parse by splitting on `|`
- **Music plan table** is a standard markdown table
- **Status values** use emoji indicators: ✅ ⚠️ ❌
- **Timecodes** use `M:SS` or `~M:SS` (approximate) format
- **File paths** are relative to `production/{slug}/`

The editorial reviewer reads this format, modifies it in place, and writes the reviewed version to `production/{slug}/editing-plan-reviewed.md`.
