# Video Model Selection and Prompt Shaping

## STEP 7: Video-Model Choice Card + Single-Shot Video Clips

### Video-model choice card (mandatory before any clip render)

Reuse the user's selected model; show the video-model choice card only when the decision is missing. Store the choice in the Project Brief. Check supported durations, resolutions, and audio inputs using the actual tool before rendering; this skill does not establish provider capabilities or prices.

Video model card:

- **H3 (workflow default)** - use checked dialogue timing, readable flat 2D staging, restrained gestures, held unease, and a clear supernatural rule. Model choice does not guarantee speech timing.
- **Seedance 2.0 (optional fallback)** - use only when selected by the user or an authorized fallback plan; preserve the same timing ledger and 2D style.
- **Per-shot mixed (advanced)** - record `video_model: H3` or `video_model: Seedance2` in each affected row. Unmarked rows use the brief's selected default. Check audio continuity when models change.

### Resolution choice card (after video model)

Reuse the approved resolution if supported. Otherwise offer the actual tool's available draft and final resolutions, with verified cost information only when available. Resolve a missing choice before rendering; text-only planning may label it pending.

### Single-shot clip rendering

Normally generate one clip per approved table row. When continuous speech bridges editorial cuts within one generation, explicitly group those rows under one `clip_id` and use all their approved storyboard sections, character cards, and scene cards. Keep shot-local and clip-local timing mapped; render the group once. For separately generated visuals with continuous external audio, record the exact track and offsets for assembly. Do not repeat or regenerate the same line in each shot.

Per-shot rules common to all video models:

- Use the text storyboards document as the authoritative per-shot reference for narrative, composition, camera movement, action staging, per-second timing, and shot number. For shots that have been extracted to a standalone node, read the extracted node instead. If a pencil image storyboard also exists, use it only for human-side pose / silhouette pre-check; do not let it override the text storyboard.
- Use character cards as the authoritative identity source.
- Use scene cards as the authoritative environment source.
- **Strip all storyboard double-binding labels** (`[char:…]`, `[scene:…]`, `[shot:…]`, `[dur:…]`, `[hook:…]`) before video render — these labels are storyboard-only reference markers and must NOT appear in the final clip. Pencil image storyboards additionally have their own shot numbers, camera icons, arrows, and notes that must be removed at render time.
- The rendered clip must contain only clean full-color Liaozhai-inspired 2D ink-and-color animation content: flat color planes, controlled gongbi contour lines, layered painted staging, and restrained paper texture.
- No storyboard line art, no storyboard labels, no subtitles unless requested, no watermarks, no 3D volume, no glossy CGI materials, and no photorealistic lighting.
- Maintain the approved screen size / aspect ratio and the approved video resolution from the resolution choice card.
- Require a passing dialogue-ledger fit before serializing prompts. Estimated fits remain provisional. Text-only prompt work stops after prompt delivery; it does not call a renderer.

### Model-specific prompt shaping

Extract key performance beats from the checked storyboard and ledger. Keep production tables, arithmetic, and QC notes outside the model-facing prompt. A held state may span several seconds without a new camera move or action. The style prefix differs by model:

- **H3 prompt prefix** (default): emphasize flat color planes, crisp painted shadow shapes, contour clarity, limited animation, restrained theatrical gestures, and the scene's specific supernatural signature. Add: `classic Chinese 2D ink-and-color animation, Shanghai Animation Film Studio-inspired visual language, crisp cel-shaded flat colors, hard-edged shadow shapes, gongbi contour linework, mineral-pigment color planes, restrained paper texture, layered painted staging, held poses, readable silhouettes, no 3D render`. Describe the actual abnormal event and its timing rather than stacking abstract horror adjectives.
- **Seedance 2.0 prompt prefix** (performance fallback): emphasize layered 2D staging, crisp cel-shaded planes, opera-inspired gestures, anticipation and recovery, selective smear frames, ink-splash spell impacts, cinematic composition, and camera choice. Add: `cinematic Chinese 2D ink-and-color animation, The Legend of Sealed Book-inspired theatrical fantasy, classic Chinese cel-animation coloring, gongbi contour lines, flat color planes, hard-edged shadow shapes, layered painted staging, opera-inspired gestures, limited animation with selective smear frames, dramatic ink-cloud effects, no 3D`.

When the user picked `per-shot mixed`, apply the prefix that matches the row’s `video_model` field.

### H3 serialization and audio handoff

- When installed, read `h3-prompt-writing/SKILL.md` and its applicable base or full-reference guide from the skill roots. Preserve that mode's field order, reference labels, speaker IDs, and dialogue syntax. Do not pass a base-mode prompt to a full-reference mode without adapting it.
- For base modes, the core fields are `integrated_multimodal_description`, `overall_soundscape`, and `non_diegetic_music`. Write descriptions in English; preserve original Chinese dialogue inside `<d>[Chinese] ...</d>`. Put delivery and pause instructions outside the dialogue tags. Add the appropriate image-alignment instruction only when actual keyframe inputs exist. Missing advanced mode syntax is a prompt-adaptation gap, not permission to invent API fields.
- Carry the ledger's phrase windows, natural delivery, pauses, and visual dependencies into the audiovisual description. Mark active speech with stable speaker IDs. Silent listeners remain silent; a visible narrator's lips stay closed during off-screen voiceover.
- Within one generated clip, use the H3 guide's `<scenetrans>` convention for continuous speech across cuts. Across separate generation calls, use natural phrase boundaries or one authorized continuous track in editing; reference-audio conditioning is not proof that the source waveform is reused unchanged.
- If external dialogue is the final source, specify whether generated speech is disabled, muted, or replaced, and preserve intended SFX/ambience where the available audio tracks permit. Do not assume a renderer can accept or isolate audio it does not support. Plan visible lip synchronization when required; off-screen speech can bridge reaction shots.
- Timing targets in a prompt do not prove H3 followed them. Run dialogue listening checks from `dialogue-timing.md` on each generated clip before assembly. Flag omitted/repeated words, rushed delivery, lost pauses, speaker errors, and cutoff endings; update actual timing evidence rather than stamping an estimate as verified.
