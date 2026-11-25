# Standardized Shot Table Specification

## STEP 5: Standardized Shot Table Video Prompts (Six Columns)

After designs are available, read `dialogue-timing.md` and build the dialogue ledger before allocating durations. For text-only planning, descriptive design anchors may stand in for cards that have not been generated. Create a canvas table node or Markdown table named `标准镜头信息表` or `standard-shot-table`. The table is the production plan; serialize a separate compact prompt for the chosen model after its checks pass.

The table must have exactly six columns in this order:

| Shot ID & Duration | Continuity Handoff | Reference Anchors (Spatial + Identity) | Hook Type | Shot Description (Per-Second Directives) | Audio & Dialogue Track |
|---|---|---|---|---|---|

Column rules:

- **Shot ID & Duration**: shot number plus planned duration, e.g. `S03 / 6s`.
- **Continuity Handoff**: how this shot naturally continues from the previous shot’s ending image, prop position, eyeline, character posture, sound bridge, or emotional state, AND how it sets up the next shot’s opening. This is the cross-shot continuity spine.
- **Reference Anchors (Spatial + Identity)**: four sub-fields, all mandatory.
  - `Fixed Landmarks` — exact named landmarks from the scene card, with their screen-relative positions (e.g. `door-frame: right third`, `kitchen-island: center bottom`).
  - `Character Positions (camera view)` — for every character in the shot, screen-relative position (left/center/right, top/mid/bottom, foreground/midground/background), facing direction, and initial pose.
  - `Exited Character Status` — for any character who was in the previous shot but is not in this shot, state their off-screen position and reason (e.g. `Mia — exited frame-left, last seen holding apple basket at door-frame`).
  - `Lighting Baseline` — inherited key/fill/rim direction from the scene card, plus any per-shot modifier (e.g. `key: warm overhead, fill: cool bounce right, modifier: window-backlit silhouette`).
  - Plus identity bindings: exact approved character card names and exact approved scene card name.
- **Hook Type**: one short purpose label, e.g. `setup`, `held-unease`, `suspense`, `reveal`, `reaction`, `reversal`, `callback`, `tender`, `chase`, `expression-beat`, or `visual-joke`. A held beat may serve anticipation or perception without a new reversal.
- **Shot Description**: shot size, motivated camera movement or a locked frame, performance style, negative style constraints, and model generation notes. For H3, prioritize readable 2D staging, speech delivery, timed silence, and audio/visual dependencies. Include `clip_id` and shot-to-clip mapping when editorial shots share a generation clip. A required `Per-Second Directives` subsection covers every second; consecutive seconds with the same held state may share an explicit range such as `2-5s`. Sub-second critical beats may use `2.0-2.5s`. Each timed interval covers five elements:
  1. Action / pose / expression (theatrical gesture, sleeve or prop path, anticipation, held pose, recovery, and selective smear where applicable)
  2. Camera movement (push / pull / pan / tilt / handheld-shake / locked / orbit)
  3. Spatial position (where the character is, what they hold, what landmark is in frame)
  4. Audio cue (narration / dialogue / SFX / breath / silence — or `silent` if intentional)
  5. Handoff to the next second or next shot (what state this second locks in for the next one)
- **Audio & Dialogue Track**: full audio script for the shot in time order, separate from per-second cues. Fields:
  - `Narration` — voiceover text with time range (omit if no narration).
  - `Dialogue` — line, speaker, tone, time range.
  - `Timing Ledger` — line IDs from `dialogue-timing.md`, required/available seconds, margin, evidence basis, and provisional or measured fit result. Preserve the full spoken text once in the ledger; per-second cues reference line IDs and phrases without repeating the whole line each second.
  - `Silence & Reactions` — explicit anticipation, internal pause, and post-line reaction/reveal windows, with sequential or concurrent dependencies. Internal pauses already counted in a line are not added twice.
  - `Audio Source & Continuity` — native speech or exact continuous-track reference, clip ID, and any cross-cut phrase/audio offsets. Separate renders require a natural speech boundary or an explicit audio assembly plan.
  - `SFX` — keyed sound effects, time-anchored.
  - `Performance Note` — when the protagonist is narrating off-screen, mark `narrator-mouth-closed: true`; describe expression path during narration; describe concrete eye-line and body-action changes for each dialogue line.

Table-wide rules:

- Each shot must naturally inherit the previous shot’s image state through the `Continuity Handoff` column and set up the next shot in the same column.
- Each shot row must include per-second directives that cover the entire shot duration from first frame to last frame, including action, pose, expression, camera movement, spatial position, sound cue, and continuity handoff.
- Timed directives must define the held or changing state precisely enough for storyboards. A sustained pose is valid: specify its duration, eyeline, prop position, camera, and sound. Do not invent a new action each second.
- Performance must be readable in 2D: use clear silhouettes, line-of-action, theatrical gesture, opera-inspired hands and sleeves, held poses, rhythmic limited animation, anticipation, recovery, and selective smear or ink-splash frames at key impacts. Do not add motion merely to simulate 3D realism.
- Choose framing changes for new information, a point of view, or a readable performance. Repeated framing and long holds are valid when they let the audience compare normal and abnormal states.
- Use Dutch angles only when motivated by the scene; surprise or imbalance does not require a tilted camera.
- Preserve the language of supplied dialogue. Resolve the language of newly requested speech only if unclear.
- Record who articulates during speech, who listens silently, and where mouths rest during pauses. On-screen speech uses natural articulation, not a continuously open mouth. The corresponding visible character stays closed-mouth during off-screen narration.
- A character who left the frame must still be tracked in `Exited Character Status` for at least one shot, then dropped after they are explicitly off-stage for two consecutive shots.

Then show a user choice card:

- Approve table and run self-check (recommended)
- Adjust shot continuity
- Make animation more exaggerated
- Adjust close-up / extreme-close-up rhythm
- Adjust Dutch-angle design

## STEP 5.5: Shot Table Self-Check Gate (Mandatory)

Before moving to pencil storyboards, run a hard self-check on the approved shot table. If any check fails, revise the table and re-run before asking the user to approve storyboarding.

Eight required checks (apply speech checks to narration as well as dialogue):

1. **Dramatic purpose and perception time**: every shot has a purpose; supernatural scenes establish a normal state, a specific violation, and a readable perception or reaction beat. Held unease can span several shots. Do not enforce reveal quotas or mandatory shot-size alternation.
2. **Runtime and generation boundaries**: edited shot durations fit the approved film length; each generation clip fits the selected tool's confirmed limits (or clearly labeled assumptions during planning). Distinguish editorial shots from clips. Do not shorten a speech window to satisfy a model limit; replan cuts and audio continuity first.
3. **Character count per shot**: no shot contains more than three important characters (defined as characters with on-screen action or dialogue).
4. **Spatial anchor inheritance**: for every interior scene with two or more shots, the `Fixed Landmarks` and `Lighting Baseline` of the next shot must either match the previous shot or include an explicit continuity note (e.g. `door-frame moves from right third to center as camera orbits left`).
5. **Timeline coverage**: timed intervals cover the shot without gaps or conflicting states, including held ranges, with all five required elements (action/pose/expression, camera, spatial, audio cue, handoff). Parallel action/audio events are allowed when compatible; a sequential reaction cannot silently overlap the line that triggers it.
6. **Cross-shot continuity**: reading the `Continuity Handoff` column row by row produces a continuous chain — no shot starts from a state that contradicts the previous shot’s ending. Any shot that flips eyeline, character position, prop state, or lighting must mark the flip explicitly (e.g. `HARD CUT — time skip: 2h`).

7. **Speech fit**: every line has a ledger entry and a nonnegative required-versus-available margin under `dialogue-timing.md`. Normalize spoken units, include internal pauses and reserve, prevent accidental speaker overlap, and preserve exact words. Fail undersized windows even if every second is labeled. No-speech shots are explicitly not applicable.
8. **Audio continuity and evidence**: line IDs, shot/clip mappings, voice source, and cross-cut offsets agree. Independent renders do not claim continuous speech without an editing plan. Mark estimated fit as provisional, measured rehearsal as rehearsal-only, and rendered-audio listening as pending until performed.

If all eight pass, place `shot-table self-check: passed; timing basis: <estimated/measured/mixed/no speech>; rendered-audio QC: pending` at the top of the table. Estimated or mixed timing also carries `speech fit: provisional`. Then show the user choice card when approval is still needed:

- Approve self-check and draw shot storyboards (recommended)
- Show self-check details
- Revise failed checks
- Re-run self-check

If any check fails, do not enter Step 6. Return to Step 5, list the failed rows, and only re-show the storyboard approval card after the table is fixed and the self-check passes.
