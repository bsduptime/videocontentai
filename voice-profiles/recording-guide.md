# Voice Clone Emotion Recording Guide

**For**: David K
**Purpose**: Record source material for voice clone profiles used in the editorial pipeline (voiceover bridges, intros, transitions)
**Date created**: 2026-03-23

---

## How This Works

The content pipeline uses **VAD (Valence-Arousal-Dominance)** as the unified measurement system for delivery:
- **Valence (V)**: 0 = negative → 1 = positive
- **Arousal (A)**: 0 = calm → 1 = energized
- **Dominance (D)**: 0 = submissive → 1 = authoritative

Each voice profile below maps to a specific VAD range used in scripts and coaching. The editorial review agent picks the right profile based on the segment's VAD target.

**Your sweet spot is 60-70% intensity** — moderate-high arousal, positive valence, confident dominance. Most profiles orbit this range with intentional shifts.

---

## Technical Recording Requirements

| Parameter | Requirement |
|---|---|
| **Format** | WAV (uncompressed) or FLAC |
| **Sample rate** | 48 kHz (minimum 44.1 kHz) |
| **Bit depth** | 24-bit preferred, 16-bit acceptable |
| **Channels** | Mono |
| **Environment** | Quiet room, no echo, no background noise. Same room as video recordings. |
| **Microphone** | Same mic used for video content (consistency matters) |
| **Distance** | Consistent mic distance throughout — don't lean in/out |
| **Session** | Record ALL profiles in one session if possible (consistent room tone) |
| **Silence** | 1 second of silence before and after each take |
| **Multiple takes** | Record each profile 2-3 times. Best take gets selected. |

**File naming**: `{profile-name}_take{N}.wav` — e.g., `drive_take1.wav`, `steady-empathy_take2.wav`

**Output directory**: `~/code/videocontentai/voice-profiles/recordings/`

---

## Profiles

### 1. Drive (Default Energy)

**VAD**: V0.70 A0.75 D0.75
**Used for**: Hooks, climaxes, demos, hot takes, CTAs — the most common profile
**Mood**: Confident, upbeat, forward momentum. You know what you're talking about and you're genuinely excited to share it.

**Recording tips**:
- Stand up or sit forward. This is your natural presenting energy.
- Think: explaining something cool you just built to a friend who gets it.
- Pace should feel purposeful — not rushed, not lazy. You're going somewhere.
- Smile with your voice. Not forced — just the natural warmth of genuine enthusiasm.

**Read these sentences**:

1. I've been building AI systems for years, and what happened this week genuinely surprised me.
2. Here's the thing nobody talks about — the tooling got so good that the bottleneck isn't technology anymore, it's imagination.
3. So I gave the agent access to our production database. Not a sandbox. The real thing. And then I watched what it did.
4. This changes everything for teams running Oracle on legacy infrastructure — and I mean everything.
5. The model processed forty thousand rows in six minutes. Six minutes. That same analysis used to take our team a full day.
6. Let me show you exactly what I mean, because this is one of those things you need to see to believe.
7. If you're a DBA and you haven't tried this yet, you're working twice as hard as you need to. That's not an exaggeration.
8. What makes this powerful isn't the AI — it's what the AI lets you skip. All the grunt work, all the manual checks, gone.
9. I walked into the office on Monday with a problem. By Wednesday the agent had not only solved it, it found three other issues I didn't know existed.
10. This is the kind of breakthrough that makes me genuinely optimistic about where database management is heading.

---

### 2. Drive + Wonder

**VAD**: V0.80 A0.80 D0.50
**Used for**: Discovery moments, "wait, it can do that?" reveals, future possibilities
**Mood**: Fascinated, slightly awed. The confidence is still there but mixed with genuine surprise. You're a builder who just saw something that impressed even you.

**Recording tips**:
- Let your eyebrows go up. Physically express surprise — it comes through in the voice.
- Drop dominance slightly — you're not lecturing, you're marveling alongside the viewer.
- Pace can quicken naturally on the exciting parts. Let the energy pull you forward.
- Think: the moment you first saw GPT-4 do something you didn't expect.

**Read these sentences**:

1. Okay, I was not expecting that. I genuinely did not think it would figure out the join optimization on its own.
2. This is one of those moments where you realize the gap between what AI can do and what people think it can do is enormous.
3. I've been in this industry for over a decade and I still get that feeling — that rush when something works better than you imagined.
4. Picture this — you ask a question in plain English, and it rewrites your entire monitoring setup. No SQL. No config files. Just... done.
5. The wild part isn't that it works. The wild part is that it works on edge cases I specifically thought would break it.
6. When I first saw this running in production, I literally stopped what I was doing and called my co-founder. You have to see this.
7. Think about what this means for someone who's never written a database query in their life. They can now do what took specialists years to learn.
8. I keep finding new things it can do. Every week there's another moment where I think, wait — that shouldn't be possible yet.
9. We're at this incredible inflection point where the technology is outpacing our ability to even describe what it does.
10. Imagine telling a DBA five years ago that an AI agent would handle their on-call rotation better than they do. They'd laugh. But here we are.

---

### 3. Tension

**VAD**: V0.25 A0.75 D0.70
**Used for**: Problem statements, stakes, "here's what's at risk" moments (always brief — max 15 seconds per use)
**Mood**: Urgent, serious, direct. Not angry — concerned. Like warning a friend about something important they're not seeing.

**Recording tips**:
- Lower your pitch slightly. Not artificially — just settle into gravity.
- Lean forward. Slow down just a touch on the key words.
- Think: telling a client their production database has a critical vulnerability they don't know about.
- This should feel like controlled intensity, not panic. Authority plus urgency.

**Read these sentences**:

1. Here's the problem that nobody wants to talk about — most companies are running their databases blind.
2. Every hour you wait, the problem compounds. I've seen teams lose weeks of work because they ignored the early warning signs.
3. Your data is not as safe as you think it is. I know that's uncomfortable to hear, but I've seen it too many times.
4. The industry is shifting faster than most teams can adapt. And the ones who fall behind don't get a second chance.
5. Right now, somewhere, a database is failing silently. No alerts. No warnings. Just slow degradation until something breaks.
6. If you're still doing manual health checks once a quarter, you're already behind. The threats are real-time. Your monitoring should be too.
7. This is the part where I have to be honest with you — the old way of doing things is dying, and pretending otherwise helps no one.
8. I talk to teams every week who are one bad deploy away from a serious incident. They don't know it yet, but the signs are all there.
9. The cost of inaction isn't theoretical. I've watched companies lose customers, lose revenue, lose trust — all because they moved too slowly.
10. When a production database goes down at two in the morning, nobody cares about your roadmap. They care about whether you saw it coming.

---

### 4. Tension + Vulnerability

**VAD**: V0.25 A0.60 D0.30
**Used for**: Honest admissions, "I got this wrong" moments, connecting through shared uncertainty
**Mood**: Raw, honest, slightly exposed. The authority drops — you're a human being sharing something real. Not weakness — authenticity.

**Recording tips**:
- Soften your voice. Not whispery — just let the armor down.
- Slow your pace noticeably. These moments need space.
- Think: telling your team about a mistake you made that cost real time and money.
- Don't perform vulnerability — actually recall a moment of genuine uncertainty. It reads in the voice.

**Read these sentences**:

1. I'll be honest — I didn't see this coming. I thought our approach was solid, and I was wrong.
2. There's this pressure to always sound certain. But the truth is, I don't have all the answers. Nobody does right now.
3. I spent three months building something nobody needed. Three months. And I should have known sooner, but I didn't want to see it.
4. When I started this company, I had no idea what I was doing with half of it. I just figured if I kept building, I'd learn. Sometimes that worked. Sometimes it didn't.
5. The hardest part of leading a tech company isn't the technology. It's sitting across from someone and saying, I don't know yet, but I'm working on it.
6. I remember the night our production system went down for six hours. Sitting there at three AM, staring at logs, thinking — I should have caught this weeks ago.
7. People see the wins. They don't see the thirty ideas that didn't work. The features we killed. The bets we lost.
8. I used to think being a founder meant having conviction about everything. Now I think it means being honest about what you don't know — and figuring it out anyway.
9. There are days when imposter syndrome hits hard. When you wonder if you're the right person to build this. I think anyone who says they don't feel that is lying.
10. Asking for help was the hardest lesson. I burned out twice before I learned that doing everything yourself isn't strength — it's stubbornness.

---

### 5. Steady

**VAD**: V0.65 A0.45 D0.50
**Used for**: Tutorials, walkthroughs, deep dives, narrated explanations — the teaching voice
**Mood**: Warm, calm, patient. Like a knowledgeable friend walking you through something step by step. No rush.

**Recording tips**:
- Sit back slightly. Relax your shoulders.
- Think: explaining a concept to a smart friend who's new to databases. Patient but not condescending.
- Pace is slower and more even than drive. Let each sentence breathe.
- This is your "explainer" voice. Supportive background energy.

**Read these sentences**:

1. Let me walk you through this step by step, because once you see how it works, it's actually pretty straightforward.
2. The first thing you want to do is check your connection settings. Open the config file — it's usually in the root directory — and look for the host parameter.
3. Don't worry if this looks complicated at first. Everyone feels that way. By the end of this, you'll know exactly what each piece does.
4. So what's happening under the hood is the query planner is choosing between a sequential scan and an index scan. In plain English — it's deciding the fastest way to find your data.
5. This is one of those tools that saves you maybe ten minutes a day. Doesn't sound like much, but over a month, that's an entire workday back.
6. If you get an error at this step, it's almost always a permissions issue. Check that your user has read access to the schema, and try again.
7. The nice thing about this approach is it's reversible. If something doesn't look right, you can roll it back with one command. No stress.
8. I like to think of indexes like a book's table of contents. Without one, the database has to read every single page to find what you need. With one, it jumps straight there.
9. Take your time with this part. There's no rush. Get comfortable with the basics before we move on to the more advanced configuration.
10. What we just did in five minutes would have taken most teams an afternoon of manual work. That's the whole point — let the tooling handle the tedious stuff so you can focus on the interesting problems.

---

### 6. Steady + Empathy

**VAD**: V0.75 A0.45 D0.25
**Used for**: Validating viewer feelings, "I get it" moments, emotional connection in educational content
**Mood**: Warm, understanding, gentle. You're acknowledging that this is hard, that their feelings are valid, that they're not alone. Low dominance — you're beside them, not above them.

**Recording tips**:
- Let warmth into your voice. Think about someone you care about who's struggling with something new.
- Pace stays slow. These moments are about connection, not information.
- Drop any trace of authority or performance. Just be a human talking to another human.
- Nod while you speak — it subtly changes your vocal tone.

**Read these sentences**:

1. I know this feels overwhelming. There's so much changing so fast, and it's completely normal to feel like you can't keep up.
2. If you're sitting there thinking, am I too late to learn this — you're not. I promise you, you're not. People start from exactly where you are every single day.
3. The fear is real. When your industry starts changing and you're not sure where you fit, that's a heavy feeling. I've felt it too.
4. You don't need to become a programmer. You don't need to understand neural networks. You just need to understand what's possible and how to use it. That's it.
5. Look, nobody expects you to figure this out overnight. The people who seem like they have it all together — they're learning as they go, just like you.
6. I talk to people every week who feel exactly the way you do right now. Smart, experienced professionals who suddenly feel like beginners again. That takes courage to sit with.
7. The whole reason I make this content is because I remember what it felt like to not understand something everyone else seemed to get. That feeling is temporary.
8. Here's what I want you to hear — your experience matters more than you think. AI can process data, but it can't do what you do. That's not a platitude. I build this technology, and I'm telling you, your judgment is irreplaceable.
9. Take a breath. You're doing fine. The fact that you're here, trying to learn this, puts you ahead of most people who are just hoping it goes away.
10. There's no stupid question in this space. The technology moves so fast that even experts are confused half the time. Anyone who says otherwise is selling something.

---

### 7. High-Intensity Drive

**VAD**: V0.75 A0.90 D0.85
**Used for**: Peak climax moments, big reveals, powerful CTAs — the top of the energy arc
**Mood**: Maximum confidence and energy. This is the "mic drop" voice. You're landing the most important point of the video with full conviction and presence.

**Recording tips**:
- Stand up for this one. Seriously — it changes your energy.
- Project. Not yelling — just filling the room with your voice.
- Think: the closing argument. The moment everything clicks together.
- Pace is slightly faster than drive, with strategic pauses before the punchlines.

**Read these sentences**:

1. This is the moment everything changes. Right here. Not next year, not next quarter — right now.
2. We ran the benchmark against every major platform on the market, and it wasn't even close. Not. Even. Close.
3. In eighteen months, the database teams that adopt this will be running circles around the ones that don't. That's not a prediction — that's math.
4. I built this because I was tired of watching talented people waste their time on problems that machines should solve. And now it actually works.
5. Forget everything you thought you knew about database monitoring. Seriously — throw it out. Because what I'm about to show you makes all of it obsolete.
6. This is why I get up in the morning. Not the technology — the fact that it actually helps people do better work. That's the whole point.
7. If you take one thing away from this video, let it be this — you have more power to shape your career right now than at any point in the last twenty years. Use it.
8. We went from concept to production in six weeks. Six weeks. And it's running right now, handling real workloads, catching real problems, twenty-four seven.
9. The people who move first always win. Always. Not because they're smarter — because they're willing to act while everyone else is still debating.
10. This is the future of how teams manage data. I'm not guessing. I'm not speculating. I built it, I tested it, and I'm watching it work every single day.

---

### 8. Reflective Calm

**VAD**: V0.55 A0.25 D0.40
**Used for**: Philosophical closers, "let that sink in" moments, transitions back from high energy
**Mood**: Quiet, thoughtful, measured. The energy has settled. You're giving the viewer space to process something meaningful. Almost intimate.

**Recording tips**:
- Lower your volume noticeably. Not a whisper — just quieter.
- Slow way down. Leave silence between sentences.
- Think: the last thing you say before someone goes to sleep. Calm, grounding, real.
- This is the opposite of performance. Just truth, delivered simply.

**Read these sentences**:

1. At the end of the day, none of this matters if it doesn't make your life better. That's the only metric that counts.
2. I think about this stuff a lot. Not just the technology — but what kind of world we're building with it. That question deserves more space than it gets.
3. Sometimes the best thing you can do is step away from the screen. Go for a walk. Let the ideas settle. The answers come when you stop forcing them.
4. We're living through one of the biggest shifts in how humans work. And most people haven't even noticed yet. That's strange, when you think about it.
5. The technology will keep getting better. That's inevitable. The question is whether we get better at using it wisely. That part is up to us.
6. I started this journey because I love building things. Years later, what keeps me going is the people who tell me it actually helped. That never gets old.
7. There's a version of the future where AI makes everything worse. And there's a version where it makes things genuinely better. We're choosing right now.
8. If you made it this far, thank you for your time. I mean that. Attention is the most valuable thing you can give someone, and I don't take it for granted.
9. The tools change. The platforms change. The one thing that stays constant is that people who keep learning keep winning. It's been true for centuries. It's still true now.
10. So that's what I've got for you today. Sit with it. Think about how it applies to your world. And if something clicks, let me know.

---

## Profile Summary Table

| # | Profile | VAD (V/A/D) | Primary Use | Delivery Energy |
|---|---------|-------------|-------------|-----------------|
| 1 | Drive | 0.70 / 0.75 / 0.75 | Hooks, demos, CTAs | 6-7 |
| 2 | Drive + Wonder | 0.80 / 0.80 / 0.50 | Discovery, reveals | 7-8 |
| 3 | Tension | 0.25 / 0.75 / 0.70 | Problem statements, stakes | 7-8 |
| 4 | Tension + Vulnerability | 0.25 / 0.60 / 0.30 | Honest admissions, uncertainty | 4-5 |
| 5 | Steady | 0.65 / 0.45 / 0.50 | Tutorials, explanations | 4-5 |
| 6 | Steady + Empathy | 0.75 / 0.45 / 0.25 | Validation, connection | 3-4 |
| 7 | High-Intensity Drive | 0.75 / 0.90 / 0.85 | Climaxes, mic drops | 9-10 |
| 8 | Reflective Calm | 0.55 / 0.25 / 0.40 | Closers, philosophy | 2-3 |

---

## Recording Checklist

Use this to track progress. Record each profile 2-3 takes.

- [ ] **Environment check**: Room is quiet, mic positioned, gain levels set
- [ ] **Test recording**: 10-second test, verify no clipping or background noise
- [ ] **Profile 1 — Drive**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Profile 2 — Drive + Wonder**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Profile 3 — Tension**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Profile 4 — Tension + Vulnerability**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Profile 5 — Steady**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Profile 6 — Steady + Empathy**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Profile 7 — High-Intensity Drive**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Profile 8 — Reflective Calm**: Take 1 ☐ Take 2 ☐ Take 3 ☐
- [ ] **Playback review**: Listen to all takes, mark best per profile
- [ ] **Files organized**: Named correctly in `voice-profiles/recordings/`

---

## Recording Order (Recommended)

Start with your natural energy and work outward:

1. **Drive** (your default — warm up here)
2. **Steady** (pull energy down to teaching mode)
3. **Steady + Empathy** (go warmer from steady)
4. **Reflective Calm** (continue the descent)
5. **Drive + Wonder** (bring energy back up with fascination)
6. **High-Intensity Drive** (peak energy while you're warmed up)
7. **Tension** (shift to urgency)
8. **Tension + Vulnerability** (drop the armor from tension)

Take a 2-minute break between profiles. Shake out the previous energy. The transitions between emotional states are harder than the states themselves.

---

## Notes for the Editorial Agent

Each profile's recordings will be used to create a voice clone matching that specific VAD range. When generating voiceover for a segment:

1. Read the segment's VAD target from the script/coaching sidecar
2. Select the voice profile with the nearest VAD match
3. For segments between profiles, prefer the profile with matching **valence** first (positive/negative split matters most), then arousal, then dominance
4. Never use a high-dominance profile (Drive, Tension) for low-dominance segments (Empathy, Vulnerability) or vice versa — the mismatch is immediately noticeable
