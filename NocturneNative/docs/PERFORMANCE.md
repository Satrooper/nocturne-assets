# Performance notes (v5)

Measured per-frame render load, stage start, before and after v5
(draw calls/objects from OpenGL v4 baseline; batch counts from scene census):

| Stage | v4 draw calls | v4 geometry batches | v5 geometry batches |
|---|---|---|---|
| 1 Neon Underworld | 1,753 | 275 | 51 |
| 2 Glass Palace    | 1,129 | —   | 18 |
| 3 Hollow Bamboo   | 1,011 | 200 | 20 |
| 4 Ashworks        |   910 | —   | 17 |
| 5 Black Cathedral | 1,288 | 168 | 18 |

Shadow casters, stage 1: 293 -> 49. Directional cascades: 4 -> 2.
Visible actor surfaces: 11 (enemy) to 18 (player); only skinned bodies cast shadows.

Quality presets (3D scale range, upscaled with MetalFX on iPhone):
PERFORMANCE 50–67% no MSAA, no glow, orthogonal shadow ·
BALANCED (default) 58–77% MSAA 2x, glow ·
QUALITY 66–87% MSAA 2x, glow, blended cascades.

If the phone still runs warm: choose PERFORMANCE, keep 60 FPS, keep ADAPTIVE on.
Renderer can be reverted to OpenGL by setting
`rendering/renderer/rendering_method.mobile="gl_compatibility"` in project.godot.
