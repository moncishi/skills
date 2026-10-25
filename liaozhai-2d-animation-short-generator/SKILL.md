---
name: liaozhai-2d-animation-short-generator
description: |
  Plan and produce Liaozhai-inspired Chinese 2D animated shorts with dialogue-first timing, uncanny held beats, character and scene continuity, and H3-ready video prompts. Use for Shanghai Animation Film Studio-inspired supernatural folklore storyboards and complete shorts, including dialogue that must fit natural delivery. Supports text-only planning without canvas tools. Not for photorealistic live action, 3D rendering, or unrelated standalone images.
---

# Liaozhai 2D Animation Short Generator

Use this Skill for Liaozhai short-film planning or production. Read `references/dialogue-timing.md` before allocating shot durations, including for storyboard-only requests. Dialogue performance and intentional silence determine the timeline; the video prompt inherits that checked timeline.

## Execution Scope

The scope and timing rules in this section take precedence over the full-production defaults below.

- Deliver only the requested stages. For storyboard or prompt work with an existing script, reuse supplied designs and enter dialogue timing and Step 5 directly; mark missing visual references as descriptive anchors, not generated assets.
- Use canvas and choice cards when available. Without them, use ordered Markdown artifacts and the available input mechanism. Do not block text planning on unavailable canvas or generation tools.
- Reuse format, model, language, and creative decisions already supplied or authorized in this conversation. The confirmation gates below collect missing choices; they do not require repeating settled decisions. Generate media only within the user's requested production scope.
- Preserve supplied dialogue in its original language. When writing new dialogue and the language is unclear, resolve it before finalizing speech timing.
- For this workflow H3 is the default, not a capability or pricing guarantee. Use the actual generation tool's supported durations and resolutions. Keep approved clip limits in the brief; unverified limits remain planning assumptions.

Full-production order: brief and story -> character/scene designs -> dialogue ledger -> checked six-column shot table -> text storyboards (pencil images opt-in) -> model-specific prompts -> authorized clip generation -> audio/visual review -> assembly and optional BGM. Read `references/liaozhai-style-guide.md` before visual prompts. Reuse settled choices, collect missing format decisions, and stop at the requested deliverable. Final renders contain no storyboard artifacts.

## Global Visual Style Lock

Unless the user explicitly requests another visual style, all character cards, scene cards, shot tables, text storyboards, optional pencil storyboards, single-shot video clips (regardless of which video model is selected), assembled videos, and final composites must use this visual style:

- Rendering style: Shanghai Animation Film Studio-inspired Chinese 2D animation language, with classic ink-and-color fantasy qualities and `The Legend of Sealed Book`-era theatrical whimsy, expressed through high-level attributes rather than copying any existing shot, character, or asset.
- Image construction: flat 2D color planes with classic Chinese cel-animation coloring, crisp hard-edged cel shadows, limited two-tone shading, clear contour hierarchy, gongbi-like controlled linework, mineral-pigment reds/blues/greens, restrained paper or silk texture, and selective ink wash for atmosphere. Keep color shapes readable at a small size.
- Character design: graphic silhouettes, elegant costume shapes, and restrained exaggeration. Use an opera-influenced facial construction: role-specific phoenix-shaped or tapered eyes, deliberate eyebrow silhouettes, and controlled cheek-rouge planes as part of the painted face design. Preserve identity through face shape, eye shape, brow shape, hair contour, costume pattern, cheek color, and signature prop instead of 3D material detail. Do not apply identical eyes, brows, or blush to every character.
- Motion language: limited-animation economy mixed with decisive pose changes, theatrical gesture, opera-inspired hand and sleeve movement, held poses, cutout-like layer separation, and occasional elastic smear only at key impact beats.
- Staging and camera: planar compositions with deliberate foreground/midground/background layers, symmetrical reveals, scroll-like lateral moves, measured pans and pushes, ink-cloud transitions, and Dutch angles only for supernatural imbalance or comic shock.
- Atmosphere: mysterious, humane, ironic, and poetic. Use moonlit courtyards, old halls, bridges, forests, paper doors, lanterns, mist, and symbolic props when story-appropriate; make the supernatural rule visually legible.
- Emotional range: favor quiet unease, wry humor, tenderness, moral ambiguity, and sudden uncanny reversals over constant action or horror spectacle.

Negative style constraints: no photorealistic live action, no 3D render, no glossy plastic materials, no generic modern anime, no neon cyberpunk palette, no Western medieval fantasy defaults, no random floating ornaments, no excessive painterly blur, no uncontrolled sketch lines, no horror gore, no copied existing characters or shot compositions.

## STEP 0: Intake and Canvas Plan

Capture:

- One-line idea or rough premise
- Desired output: blueprint only, assets only, standardized shot table with per-second directives, single text storyboards document (default) + extracted single-shot text storyboard nodes for heavy-iteration shots + multi-panel pencil storyboards (opt-in), single-shot video clips (with video model chosen in Step 7), assembled main video, or final BGM-composited film
- Approximate length, if the user already stated it
- Screen size / aspect ratio, if the user already stated it
- Visual tone: default Liaozhai-inspired Chinese 2D ink-and-color animation; read `references/liaozhai-style-guide.md` before generating any visual prompt
- Dialogue requirement: whether the film has dialogue, voiceover, or no speech
- Dialogue language from supplied lines or the user's stated choice; do not translate supplied dialogue or default new dialogue to English

Immediately after capturing the user's input, before Project Brief or any other next step, show choice cards to confirm production format:

Screen size / aspect ratio card:

- 16:9 landscape (recommended for cinematic short)
- 9:16 vertical short
- 1:1 square
- 4:5 social portrait
- Custom size / aspect ratio

Total duration card:

- 30–60 seconds (recommended)
- 15–30 seconds
- 60–90 seconds
- 90–180 seconds
- Custom duration

Only proceed after the user chooses both screen size/aspect ratio and total duration, or explicitly supplies custom values. Store the approved screen size/aspect ratio and duration in the Project Brief and reuse them in shot timing, transition continuity, the standardized shot table with per-second directives, single-shot storyboards (text by default, pencil image when user opts in), single-shot video clips, assembly, BGM matching, and final composite settings.

Create or later update canvas artifacts in this order:

1. Project Brief text node
2. Story Outline text node
3. Labeled Character Card image nodes
4. Environment-only Scene Card image nodes
5. Standardized Shot Information Table node with six columns; each row must include per-second directives inside `Shot Description`
6. **Single text storyboards document** — one canvas text node named `<title> text storyboards` containing one section per shot (mirrors the half-narrated-drama storyboard structure). When the user flags a shot for heavy iteration, that section is extracted to a standalone text node and a `(extracted)` marker is left in the document. Pencil image storyboards, if opted in, are separate image nodes.
7. Single-Shot Video Clip nodes (rendered by the video model selected in Step 7 — H3 default, Seedance 2.0 fallback)
8. Assembled Main Video node
9. Matched BGM audio node and Final BGM-Composited Video node

Do not dump long production content only in chat. Put durable outputs on canvas as text, image, video, or audio nodes.

## STEP 1: Project Brief

Produce a concise project brief and write it to a canvas text node named with the project title or `项目简报`.

Include:

- Working title
- One-line What-if
- Emotional premise
- Target audience feeling
- Main deliverables planned
- Approved screen size / aspect ratio
- Approved total duration
- Dialogue mode and language from supplied text or an explicit choice; mark newly requested speech language pending only when unclear
- Initial risks
- Dialogue intent when present
- Speech production mode: native generated speech or an existing continuous voice track; timing evidence: estimated, measured rehearsal, or measured final audio
- Available clip duration/resolution constraints and any assumptions that still need verification before rendering

Then show a user choice card:

- Continue with this direction (recommended)
- Regenerate premise options
- Revise emotional premise
- Refine dialogue direction

Only proceed after the user chooses or explicitly says to continue.

## STEP 2: Story Outline and Gates

Create a story outline and write it to a canvas text node named `故事大纲` or `story-outline`.

Include:

- Protagonist Want / Need / flaw
- Core world rule
- 8-beat causal story spine
- Emotional anchor and payoff
- Dialogue beats if the user requested dialogue
- Red-line checks

Gate checks:

- Protagonist is active
- Crisis is intensified by protagonist flaw
- Coincidence never solves the problem
- Ending reuses an earlier emotional anchor
- Antagonistic pressure is not a flat villain
- Dialogue reveals relationship change instead of explaining the theme

Then show a user choice card:

- Approve story and continue (recommended)
- Revise beats
- Revise emotion curve
- Revise dialogue beats
- Return to premise

## STEP 3: Character Cards

Generate character reference cards and place each image on canvas. Recommended order:

1. Protagonist card
2. Contrast / pressure character card
3. Optional supporting character card

Each character card should be a 16:9 production reference sheet when possible. Unlike final rendered video, character cards should include clear readable labels so downstream generation can bind the correct person and props:

- Character name label in English and/or the project language
- Role label, such as protagonist, grandma, thief, sidekick, pressure character
- Main 3/4 view
- Front / side / back views
- Expressions
- Material / costume / prop details
- Important prop labels, such as handbag, wallet, skateboard, apple basket, scarf, shoes, glasses
- Identity lock repeated in the prompt
- A short visual-ID note listing age range, body type, hairstyle, outfit colors, signature props, and do-not-change traits

For this 2D animation style, keep contour weight, face construction, costume pattern, palette role, and signature props consistent across later images and videos. Do not introduce 3D volume, glossy materials, or realistic lighting in later assets.

After the main character cards are generated, show a user choice card:

- Lock character designs and continue (recommended)
- Regenerate protagonist card
- Adjust specific visual details
- Add another character card

Warn the user that changing locked character designs later may require regenerating the shot table, single-shot storyboards, single-shot video clips, assembled main video, and final composite.

## STEP 4: Scene Cards

Generate scene reference cards and place them on canvas after character cards. Scene cards must show environments only: do not include characters, people, crowd figures, silhouettes, hands, faces, or character cameos. Character action belongs in the shot table, single-shot multi-panel pencil storyboards, and single-shot video clips, not scene cards.

Include:

- Main environment overview
- Key light states, such as day / night
- Emotional sub-spaces
- Continuity landmarks (fixed objects whose screen position must persist across shots in the same scene, e.g. kitchen island, sofa, door frame, tree, mailbox)
- Important props in the environment

Then show a user choice card:

- Lock scene design and continue (recommended)
- Regenerate scene card
- Add another scene angle
- Adjust lighting or layout

## STEP 5: Standardized Shot Table Video Prompts (Six Columns)

After character/scene designs are available (or supplied descriptions are recorded for text-only planning), build the dialogue ledger from `references/dialogue-timing.md`. Then allocate shot durations and output the six-column shot table. Do not choose uniform shot lengths first and squeeze speech into them. Keep the production table separate from the compact model-facing prompt.

Required references: read and follow `references/shot-table-spec.md` for the exact six-column schema and self-check gate, and `references/liaozhai-style-guide.md` for 2D staging, linework, palette, supernatural visual grammar, and prompt negatives.

Minimum runtime contract:

- Create a canvas table node named `标准镜头信息表` or `standard-shot-table`.
- Use exactly six columns: `Shot ID & Duration`, `Continuity Handoff`, `Reference Anchors (Spatial + Identity)`, `Hook Type`, `Shot Description (Per-Second Directives)`, `Audio & Dialogue Track`.
- Every row must include complete per-second directives, continuity handoff, reference anchors, hook type, and audio/dialogue timing.
- Every speech-bearing row must reference checked dialogue-ledger entries. Preserve evidence status and silence/response windows in the table and downstream storyboards.
- Run the Step 5.5 self-check from `references/shot-table-spec.md` before storyboarding. Do not enter Step 6 until the self-check passes.

Then show the table approval/self-check choice cards defined in `references/shot-table-spec.md`.

## STEP 6: Text Storyboards Document (Default) + Pencil Image Storyboards (Opt-in)

After the Step 5.5 self-check passes, show a storyboard-mode choice card before producing any storyboard artifact.

Required reference: read and follow `references/storyboard-guidelines.md` for the default single text storyboards document, optional multi-panel pencil storyboards, shot-level extraction/re-integration, storyboard approval cards, and visualization fallback rules.

Minimum runtime contract:

- Default mode is one authoritative text storyboards document containing one section per shot.
- Pencil storyboard images are opt-in visualization artifacts only; they never override the text storyboard.
- Extract a shot into a standalone text node only when the user flags that shot for heavy iteration.
- Step 7 must read the matching text storyboard section or extracted standalone node, not the pencil image.

After all storyboards are approved, proceed to the video-model choice card.

## STEP 7: Video-Model Choice Card + Single-Shot Video Clips

Before any clip is rendered, show the video-model choice card and resolution choice card.

Required references:

- Read `references/model-selection.md` for the H3 default, Seedance 2.0 fallback, per-shot mixed mode, resolution choices, and model-specific prompt shaping. Preserve the Liaozhai 2D style prefix for either model.
- Read `references/fallback-policy.md` for per-model retry ladders, drift handling, and escalation choices.
- Read `references/dialogue-timing.md` again when dialogue, delivery, clip boundaries, or durations change; invalidate affected timing checks before rendering.

Minimum runtime contract:

- H3 is the recommended default model.
- Seedance 2.0 is an optional fallback under the user's selected model/retry plan.
- Per-shot mixed mode is allowed only when the shot table marks the model per row; unmarked rows use the brief's default (H3 unless changed).
- Strip all storyboard-only labels before video render.
- Bind each clip to its approved storyboard section(s), exact character cards, and exact scene card. Use the shot/clip mapping when one generation contains several editorial shots.
- If a clip drifts from the approved `Reference Anchors`, follow `references/fallback-policy.md`; do not silently assemble incorrect clips.

After all clips render and their dialogue/visual checks pass, place them in shot order, group them as `<title> shot clips`, and use the clip approval options in `references/fallback-policy.md` when approval remains needed.

## STEP 8: Full Film Assembly, BGM Match, and Final Output

After all clips are approved, assemble the main video using the shot/clip and audio mapping. Match or generate a continuous BGM track only when requested; intentional absence of score is valid.

Required reference: read `references/qc-checklist.md` for assembly rules, BGM rules, final review checks, canvas ordering/grouping discipline, user choice-card discipline, and regeneration/latest-asset discipline.

Minimum runtime contract:

- Preserve the exact shot order from the approved table.
- Use only approved latest assets.
- Duck BGM under dialogue, reactions, and important SFX.
- Do not add subtitles or text unless explicitly requested.
- Final video must contain no storyboard traces, labels, arrows, timing marks, panel borders, or double-binding labels.

Then run the final review checks from `references/qc-checklist.md` and deliver the final approved asset.

## Boundaries

For Liaozhai storyboard or prompt-only work, run the timing and staging parts and stop at the requested text deliverable; use `h3-prompt-writing` for H3 serialization when installed. For unrelated standalone prompts or character cards, use the corresponding prompt or character workflow instead.
