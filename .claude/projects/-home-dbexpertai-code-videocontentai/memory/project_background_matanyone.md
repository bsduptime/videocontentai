---
name: MatAnyone high-quality background matting
description: MatAnyone (CVPR 2025/2026) as future high-quality option for background replacement — better edges, hair detail, but slow
type: project
---

MatAnyone (v1 CVPR 2025, v2 CVPR 2026) is the planned high-quality upgrade path for background replacement, beyond the current RVM integration.

**Why:** RVM is fast and good enough for most content, but MatAnyone produces significantly better alpha mattes — fine hair strands, semi-transparent edges, excellent temporal consistency via its Consistent Memory Propagation module. For hero/flagship content where quality justifies overnight processing, MatAnyone is the right choice.

**How to apply:**
- Config field `model = "matanyone"` is reserved in BackgroundConfig for future use
- User tested RVM and decided it's good enough — MatAnyone is parked unless quality demands change
- MatAnyone is diffusion-based, ~2-10s per frame on Orin AGX 64GB — would need Docker container
- License is CC BY-NC 4.0 — check if commercialization is planned before using
- GitHub: pq-yang/MatAnyone, pq-yang/MatAnyone2
- Neither RVM nor MatAnyone correct lighting mismatches — a separate image harmonization step (iHarmony4, PCTNet) would be needed for compositing onto differently-lit backgrounds
