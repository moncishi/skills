# Dialogue-First Timing

Read before the shot table, and whenever a line, delivery, duration, or generation boundary changes. The dialogue ledger is the timing source for the table, storyboard, model prompt, and audio review.

## Establish Evidence

For every spoken line, record:

`line_id | speaker | exact_text | delivery | timing_basis | spoken_units/rate (if estimated) | articulation_s | internal_pauses_s | reserve_s | required_s | start_s | end_s | shot_ids | clip_ids | audio_source | status`

- Keep original words and punctuation. Line IDs remain stable across cuts; split timing spans by phrase without duplicating the spoken text. Proposed wording changes require the user's approval unless rewriting is already in scope.
- Prefer an actual rehearsal or approved voice track in the intended delivery. Measure the retained utterance from first audible speech to last, including internal breaths and pauses; record the file and in/out points. A rehearsal measures that take only, not future H3 speech. Do not claim measurement without audio evidence.
- Without audio, mark `timing_basis: estimated`. For Mandarin, expand numbers, dates, abbreviations, and symbols into their intended pronunciation for counting; exclude punctuation from spoken units and budget pauses separately. Keep this counting form separate from the exact dialogue. Mixed languages and unusual readings need explicit pronunciation assumptions or a rehearsal.
- For restrained Liaozhai Mandarin dialogue, 2.5-3.5 spoken syllables per second is an initial planning range, not an empirical standard or H3 limit. Select a rate matching this character and delivery. Do not assume whispers are always slower or distressed speech always faster. When uncertain, budget using the slower end; verify by listening later.
- Specify meaningful pauses and breaths as durations. An ellipsis alone is not a timing instruction. Treat sustained cries, laughter, and nonverbal vocalizations as timed audio events too.

## Fit the Timeline

For estimated speech:

`required_s = spoken_units / rate + internal_pauses_s + reserve_s`

For measured speech:

`required_s = measured_utterance_s + reserve_s`

The measured duration already includes its internal pauses; never add them again. For estimates, `utterance_s = spoken_units / rate + internal_pauses_s`. For estimated speech or a rehearsal that H3 will reperform, start with `reserve_s = max(0.5, 0.1 * utterance_s)` as a tunable planning allowance, not a model guarantee. Compute this allowance from the full utterance including pauses, not articulation alone. If changing the default, state why. For a locked audio track reused unchanged, reserve may be zero; preserve any editorial handles separately.

Use an available calculator or local executable arithmetic to check spoken-unit counts, required time, and margins. Keep full precision until final display; do not round a deficit into a pass. When calculation tools are unavailable, show the arithmetic and mark it unchecked. Derive available time from the user's actual constraints, not an invented earlier deadline. Treat user-reported audio measurements as supplied evidence, not measurements you performed; file-level validation remains pending until the source is available.

- Require `end_s - start_s >= required_s` for each line's continuous speaking window. Check arithmetic, not just the presence of timestamps. For a line crossing cuts, record contiguous phrase spans on the film timeline and count the line once.
- Allocate pre-speech anticipation, post-speech reaction, and supernatural reveal holds on the same timeline. Mark dependencies: a reaction that happens after a line cannot occupy its speech window. Actions that can occur during speech share time and are not added again. Clip/shot duration must cover the latest scheduled event end.
- Other speakers must not overlap unless an intentional interruption or chorus is specified. Allocate turn-taking pauses explicitly. Off-screen speech can continue while another character reacts silently.
- Keep film time, shot-local time, and clip-local time distinguishable. Sum edited shot durations for the requested film length; do not sum overlapping sound bridges or generation handles as extra screen time.
- Distinguish an editorial shot from a generation clip. A continuous line may cross editorial cuts within one clip. For separate generation calls, choose a natural speech boundary or an explicit continuous-audio editing plan; a repeated speaker ID does not ensure matching takes.
- Silent shots need an audio/silence timeline but no fabricated speech entries. Maintain deliberately held poses without inventing an action for every second.

## Gate and Repair

Before storyboards or video prompts, publish a compact timing result per line: `required`, `available`, `margin`, `evidence`, and `pass/fail`. An arithmetic pass based on estimates is `provisional`, not audio-verified. Audio review is still required after generation.

If a line fails, revise in this order as constraints allow:

1. Extend or redistribute shot time while respecting the approved total duration and clip limits; preserve intentional story beats.
2. Let continuous speech bridge an editorial cut, or split at a natural phrase boundary with an explicit audio plan. Recompute the timeline and ledger.
3. When fixed runtime and unchanged text cannot both fit the intended delivery, report the concrete deficit and offer revised text or runtime choices. Do not emit a render-ready prompt labeled as passed.

Do not silently accelerate delivery, remove pauses, cut words, truncate a sentence, or hide overflow with a cutoff marker. A changed line, voice delivery, or clip boundary invalidates its old fit result. Native-audio prompts carry timing targets; they do not enforce exact speech duration.

## Worked Planning Cases

- Slow line: 12 spoken units at 3 units/s + 1s internal pause + 0.5s reserve needs 5.5s. With 1s anticipation and a sequential 2s reaction, allocate at least 8.5s. These are estimates until heard.
- Overload: 36 units at 3 units/s + 1s pause gives a 13s utterance; 1.3s reserve makes 14.3s required. A 5s speaking window fails by 9.3s even if the prompt labels every second. Return to timing, not faster delivery.
- Cross-cut speech: one unchanged measured 8s voice track can run from film 1s to 9s across a picture cut at 5s. Count 8s once, use phrase/audio offsets, and retain the same audio source. If visuals are generated separately, assemble against that track; do not generate two overlapping copies of the line.

## Uncanny Rhythm

Stage an understandable normal state, one specific violation, and time to perceive it. These may span several shots; no fixed reveal-per-three-shots quota applies. Assign each scene a repeatable rule such as a motionless person whose shadow keeps moving. Hold framing when it helps comparison. Opera-influenced posture, sleeve gestures, flat painted layers, and selective movement support the style; camera movement and effects must not obscure the abnormal event.

## Listen After Generation

Compare actual speech against exact text and intended delivery: omissions, substitutions, repetitions, speaker swaps, accidental overlap, rushed syllables, missing pauses, cutoff endings, and lip movement on a silent listener or narrator. Check that the reveal and reaction still occur in their intended relation to the words. Record actual times and clip identity; automated transcription can assist but does not prove delivery or pause quality. If listening is unavailable, mark audio QC pending. Repair affected timing/prompts or use an authorized continuous voice track; do not mark an unheard render verified.
