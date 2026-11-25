# Liaozhai 2D Style Guide

Read this reference before writing any character, environment, storyboard, shot-table, image, or video prompt. It is the project-wide style lock for this skill.

## Creative target

Use a classic Chinese animation language associated with Shanghai Animation Film Studio folklore films and the theatrical wit of *The Legend of Sealed Book*. Translate the target into visual attributes rather than copying any existing character, frame, prop design, or shot composition.

- Flat 2D color planes with clear graphic silhouettes.
- Classic Chinese cel-animation coloring: crisp flat fills, hard-edged shadow shapes, limited two-tone shading, and no smooth 3D gradients.
- Gongbi-inspired controlled contour lines: deliberate, varied line weight; no uncontrolled sketching.
- Mineral-pigment reds, cinnabar, indigo, leaf green, ochre, ink black, and restrained paper-white accents.
- Subtle xuan-paper or silk grain; selective ink wash for mist, magic, night air, and transitions.
- Period Chinese costume silhouettes, readable sleeve and headdress shapes, patterned trims, and one or two identity props.
- Opera-influenced facial design without a full painted mask by default: tapered or phoenix-shaped eyes where the role supports it, deliberate eyebrow silhouettes, and controlled cheek-rouge planes integrated into the cel-colored face. Vary eye, brow, and cheek treatment by character.
- Layered foreground, midground, and background staging. Prefer painted depth and parallax over 3D volume.
- Theatrical gestures, opera-inspired sleeves and hand shapes, held poses, rhythmic limited animation, and selective smear or ink-splash frames at impacts.
- Tone: uncanny, humane, ironic, poetic, and morally ambiguous. Supernatural elements should expose character or social hypocrisy, not exist only as spectacle.

## Visual grammar for supernatural events

Give each supernatural rule a repeatable visual signature: a specific ink color, paper texture, contour behavior, shadow shape, sound motif, or prop transformation. Establish it before the first major reveal. Keep transformations readable in silhouette and stage them in layers so the audience can follow cause and effect.

Prefer doors, mirrors, lanterns, fans, scrolls, bridges, wells, old trees, masks, seals, and written charms as symbolic props when they serve the story. Avoid random ornament added only to signal "Chinese fantasy".

## Prompt construction

Put the style lock near the start of every visual prompt, then specify story action and continuity anchors. Use concrete 2D terms:

```text
classic Chinese 2D ink-and-color animation, Shanghai Animation Film Studio-inspired visual language, The Legend of Sealed Book-inspired theatrical fantasy, classic Chinese cel-animation coloring, crisp cel-shaded flat colors, hard-edged shadow shapes, limited two-tone shading, gongbi contour linework, flat mineral-pigment color planes, restrained xuan-paper texture, layered painted staging, theatrical folklore gestures, limited animation, readable silhouette, no 3D render
```

For character cards, append role-specific facial construction such as `opera-influenced facial design, tapered phoenix eyes, deliberate eyebrow silhouette, controlled cinnabar cheek-rouge planes, clean ink outlines`. Do not use this as a one-size-fits-all face: elderly, comic, villainous, and supernatural characters need different eye, brow, and cheek treatments.

Add the approved character card and scene card names exactly. Describe the key light as a painted color field, ink wash, rim contour, or paper cut shape instead of physically simulated volumetric lighting.

## Hard negatives

`photorealistic live action, 3D model, CGI volume, glossy plastic, physically based materials, generic modern anime, neon cyberpunk, Western medieval fantasy, random Chinese ornaments, excessive painterly blur, uncontrolled sketch lines, gore, body horror, copied existing characters, copied existing composition, text or watermark`

## Continuity checks

Across assets, verify: contour hierarchy, face construction, costume pattern, palette role, signature prop, layer order, fixed landmarks, shadow language, and the supernatural signature. If a model produces 3D volume, glossy surfaces, realistic lens blur, or inconsistent linework, regenerate with the hard negatives and exact reference-anchor block before changing the story.
