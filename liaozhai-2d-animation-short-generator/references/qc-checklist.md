# Assembly, Final Review, and Asset Discipline

## STEP 8: Full Film Assembly, BGM Match, and Final Output

After clips pass visual and audio review, assemble them according to the shot/clip mapping and approved timeline. A multi-shot generation clip appears once, not once per table row. Apply continuous voice tracks and sound bridges with their recorded offsets. Add the approved continuous BGM only when requested; intentional absence of score is valid for uncanny held beats.

Assembly and BGM rules:

- Preserve the exact shot order from the approved table.
- Match BGM to the assembled video’s actual pacing, emotional arc, comedy beats, chase rhythm, and ending tone.
- Duck BGM under dialogue, non-language reactions, and important SFX.
- Preserve clip audio/SFX unless the approved audio plan replaces them. When a continuous voice track is the final dialogue source, prevent generated dialogue from playing underneath it; confirm the needed separation or remix is available. Do not infer audio-track separation support.
- Do not generate BGM per shot.
- Do not add subtitles or text unless the user explicitly asks.
- Output the final video with clean animation visuals and no storyboard traces, including no `[char:…] [scene:…] [shot:…]` labels.

Then show a user choice card:

- Approve final film (recommended)
- Regenerate BGM
- Adjust BGM mix
- Re-render selected clip

## STEP 9: Final Review

Create a short final review text node if the user asks for diagnosis or if there are visible risks.

Check:

- Character consistency
- Scene continuity (verify against the `Reference Anchors` column — did every landmark land where the table said it would?)
- Emotional anchor payoff
- Shot purpose clarity
- Dialogue completeness and delivery: listen against the exact ledger text for omissions, substitutions, repetitions, rushed syllables, lost pauses, wrong speakers, accidental overlaps, and truncated endings. Apply `dialogue-timing.md`; without listening, report audio QC pending.
- Actual speech start/end and silence/reaction windows match the intended causal order. Record actual timing and asset version; estimated-fit approval is not rendered-audio verification.
- Cross-cut dialogue uses one coherent audio source or checked phrase-boundary edits, without duplicated words or abrupt voice changes. Check visible lip articulation and silent narrator/listener mouths.
- Foley/SFX sync (against the `Audio & Dialogue Track` column)
- BGM balance
- No storyboard artifacts in final video: no panel borders, sketch lines, arrows, labels, handwritten notes, timing marks, pose ghosts, storyboard text, AND no double-binding labels (`[char:…]`, `[scene:…]`, `[shot:…]`, `[dur:…]`, `[hook:…]`)
- Missing or weak clips
- Any asset that may need regeneration

## Canvas Ordering and Grouping Discipline

Whenever a durable artifact is created, write it to the canvas immediately in the sequence defined in STEP 0. If a generation tool automatically adds outputs to canvas, do not duplicate them.

Group every production section on canvas:

- Group project brief and story outline as `<title> story planning` when both exist.
- Group character cards as `<title> character cards`.
- Group scene cards as `<title> scene cards`.
- Group the standardized shot table as `<title> shot table`.
- Group the text storyboards document as `<title> text storyboards` (default mode, one document). Extracted standalone text storyboard nodes and pencil storyboards (visualization mode) are separate groups: `<title> extracted text storyboards` and `<title> multi-panel pencil storyboards`. Keep all storyboard groups separate from rendered clips because storyboards contain double-binding labels, shot numbers, camera icons, arrows, and sketch lines.
- Keep storyboard groups separate from rendered clips because storyboards contain double-binding labels, shot numbers, camera icons, arrows, and sketch lines.
- Group single-shot video clips as `<title> shot clips` (the label no longer hard-codes a specific model name, since projects can mix H3 and Seedance 2.0).
- Group assembled main video, matched BGM, and final composited video as `<title> final delivery` when they exist.

If a generation round produces two or more outputs, group recent outputs immediately with a clear title. If the renderer has not flushed positions and grouping fails, tell the user to click/drag any canvas node once, then retry grouping before continuing to the next costly stage when possible.

## User Choice Card Discipline

Use choice cards when supported; otherwise use the available input mechanism. The execution scope in `SKILL.md` governs these full-production defaults: reuse existing choices and authorization, and skip stages outside the requested deliverable. Gates for missing creative decisions:

- Immediately after intake, before any next step, to choose screen size / aspect ratio
- Immediately after intake, before any next step, to choose total duration
- After project brief
- After story outline
- After character cards
- After scene cards
- After standardized shot table (gate 1: approve table before self-check)
- After shot-table self-check passes (gate 2: approve self-check, then immediately choose storyboard mode: text only / text + pencil image)
- After single-shot storyboards (text storyboards document by default with optional extracted standalone nodes; pencil images if the user opted in)
- Before single-shot video-clip rendering, to choose the video model (H3 default, Seedance 2.0 fallback, per-shot mixed)
- Before single-shot video-clip rendering, to choose video resolution
- After single-shot video clips
- After full-film assembly, BGM match, and final composite

Default recommended option should be first. Always allow custom user input. If the user says “continue,” treat it as choosing the recommended option.

## Regeneration and Latest-Asset Discipline

When the user regenerates or revises any artifact, all downstream steps must use the newest approved artifact, not the older one.

Rules:

- If a character card is regenerated, future shot tables, the text storyboards document (plus any extracted standalone text storyboard nodes), pencil storyboards (if visualization mode is on), single-shot video clips, assembled videos, and final composites must reference the regenerated labeled character card by exact character name.
- If a scene card is regenerated, future shot tables, the text storyboards document (plus any extracted standalone text storyboard nodes), pencil storyboards (if visualization mode is on), single-shot video clips, assembled videos, and final composites must reference the regenerated scene card by exact scene name.
- If the shot table is revised, future text storyboards document (or extracted nodes), single-shot video clips, and assembly must use the revised table. The self-check in Step 5.5 must be re-run before storyboarding resumes.
- If dialogue text, delivery, audio source, pauses, or shot/clip durations change, invalidate affected ledger fit results and downstream prompts. Recompute timing before generation; new clips need fresh listening checks. Preserve stable line IDs and mark superseded audio versions.
- If a section in the text storyboards document is revised, the matching single-shot video clip must use the revised section. If that section has been extracted to a standalone node, that node is the source of truth; otherwise the document section is.
- If a standalone extracted text storyboard is revised, after the user is satisfied, re-integrate it back into the text storyboards document (replace the placeholder with the latest content) and archive the standalone node.
- In visualization mode, if a pencil storyboard is redrawn, the matching video clip is still bound to the text storyboards document (or extracted node); the pencil image is human-review-only and may be redrawn without forcing a video re-render.
- If a single-shot video clip is re-rendered, assembly, BGM matching, and final composite must use the new clip. If the clip was rendered with H3 and the user wants to re-render with Seedance 2.0 (or vice versa), treat that as a model switch — record the new model in the Project Brief and re-check per-shot rules.
- If BGM is regenerated, the final composite must use the regenerated BGM.

After any regeneration:

1. Mark the regenerated artifact as the current approved version in the next text output or reply.
2. Prefer the regenerated file path / node over previous versions in all subsequent prompts.
3. If there are multiple versions on canvas, identify the chosen current version by filename or node name before continuing.
4. Do not silently mix old and new assets in final assembly.
