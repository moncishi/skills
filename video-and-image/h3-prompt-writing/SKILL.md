---
name: h3-prompt-writing
description: Write MiniMax H3 video generation prompts for T2VA, I2VA, FL2VA, L2VA, and Ref2VA. Use when rewriting multimodal requests into H3 prompt structures, composing integrated_multimodal_description, overall_soundscape, and non_diegetic_music, aligning keyframes, or defining reference labels for images, videos, and audio.
---

# H3 Prompt Writing

Portable to any agent that can read local files: no external API calls, MiniMax Hub tools, or proprietary runtime required. The agents/openai.yaml file only adds optional ChatGPT/Codex UI metadata; it does not restrict the skill to OpenAI agents.

## Workflow

1. Identify the input mode: T2VA, I2VA, FL2VA, L2VA, or full-reference Ref2VA.
   Before rewriting speech, apply the Speech Timing Gate below. Carry any supplied dialogue ledger forward as the timing source; do not replace it with newly guessed timestamps.
2. For base text/keyframe modes, read `references/base-en.txt` and follow its final prompt structure.
3. For full-reference mode, read `references/ref-en.txt` and follow its six-section rewrite format.
4. Preserve the exact field names, section order, labels, and timing notation from the selected guide.

## Base Modes

- T2VA: build the full audiovisual timeline from text.
- I2VA: start from the first frame and develop forward from it.
- FL2VA: describe the continuous path between the first and last frames.
- L2VA: infer a plausible opening and converge to the supplied last frame.

Use `integrated_multimodal_description`, `overall_soundscape`, and `non_diegetic_music` in the order shown in `references/base-en.txt`.

## Full-Reference Mode

Ref2VA rewrites use `subject_definitions`, `summary`, `retention_analysis`, `detailed_description`, `overall_soundscape`, and `non_diegetic_music` in that order. Reference labels stay consistent across all sections.

Read `references/ref-en.txt` for label rules, retention analysis, and complete examples.

## Output Rules

- Write rewrite sections in English; preserve dialogue, lyrics, and visible scene text in their original language.
- Describe each shot by composition, subjects, environment, actions, camera, sound, and the exact point where referenced content appears.
- Avoid plot summaries, unresolved reference labels, and timing that does not match the requested duration.

## Speech Timing Gate

- For dialogue or narration, record exact text, speaker, intended delivery, required duration including internal pauses, available speaking window, and timing evidence outside the final prompt. Use supplied measurements or clearly labeled estimates; text timestamps alone are not audio evidence.
- When estimating, state the spoken-unit count and rate, expand numbers/abbreviations into the intended reading for counting, and budget pauses plus an explicit uncertainty allowance. Keep pronunciation notes separate from the unchanged spoken text. If source audio is measured, its internal pauses are already included; do not count them twice. No universal words-per-second or characters-per-second value applies to every language and delivery.
- Require the speaking window to fit the full utterance and allowance, with room on the timeline for any sequential anticipation, speaker handoff, and post-line reaction. Compatible speech and action may run concurrently. Check all speakers for unintended overlap. Speech-free clips skip this gate.
- Verify counts and duration arithmetic with an available calculator or local execution; show the formula and mark arithmetic unchecked if tools are unavailable. Preserve full precision for pass/fail and distinguish user-reported audio measurements from files actually inspected.
- If speech cannot fit, adjust timing/cuts within the user's constraints or report the duration deficit with concrete alternatives. Do not label the prompt render-ready by accelerating delivery, rewriting supplied text, removing pauses, or adding `<cutoff>` to hide overflow. Use `<cutoff>` only for a requested dramatic interruption.
- For Liaozhai projects with `liaozhai-2d-animation-short-generator` installed, read that skill's `references/dialogue-timing.md` and inherit its approved ledger. This is a conditional integration; other projects do not need that skill or its stylistic defaults.
- Serialize checked key beats into the selected H3 format, preserving exact dialogue, stable speaker IDs, delivery, meaningful pauses, voiceover mouth behavior, and sound/visual dependencies. Keep arithmetic, ledger IDs, QC stamps, and production notes out of the model-facing prompt. Do not paste the full per-second production table into it.
- A line crossing an editorial cut inside one generation uses the guide's `<scenetrans>` convention and an explicit continuous-audio description. Across separate generation calls, a tag or repeated speaker ID cannot establish audio continuity: split at a natural speech boundary or document assembly with a continuous voice track. Do not duplicate the full line into both clips.
- Mark estimated fit as provisional and generated-audio QC as pending. After rendering, listen for exact words, intended delivery, pauses, speaker assignment, and complete endings; measure actual timing before calling it verified. If only prompts were requested, deliver the checked prompt and its brief evidence status without implying a render occurred.

## Tips for Better Results
- Match the description to the requested video length and the selected tool's supported duration. Treat the guide's duration examples as examples, not universal API limits.
- Keep reference labels consistent (e.g. `<Picture 1>`, `<Video 1>`, `<Audio 1>`) across every section.
- Prefer concrete visual and audio details over abstract words like "cinematic" or "beautiful".
- When using keyframes (I2VA / FL2VA / L2VA), clearly state how the first and/or last frame connects to the timeline.
