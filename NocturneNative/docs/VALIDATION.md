# v4 validation

Godot 4.5.2 Standard / Compatibility / Linux desktop.

98/98 engine integration checks passed. The previous 90 campaign/combat checks
are retained. Eight additional checks cover render presets, adaptive resolution
minimum/maximum bounds, rigid weapon batching, and weapon-relative hand targets.
See TEST_RESULTS.txt for the complete engine output.

All five stage environments and boss captures were rendered at 1280x720 using
Mesa llvmpipe. Quality preset, adaptive scaling disabled for the captures.
These are actual engine screenshots, with staged boss positions and player
invulnerability. They are not generated illustrations or a human-playthrough record.
The final capture run completed without script/shader errors. A virtual-display
V-Sync warning remains; desktop software rendering is not an iPhone benchmark.

See PERFORMANCE.md for the sampled render counters. Draw calls decreased in all
five sampled scenes, while the new textures cost more texture memory. Foliage
was partitioned spatially and its cylinder meshes simplified after the first pass.

Not verified: iOS v4 export, installation, hardware touch, frame rate on iPhone,
sustained heat/battery usage, low-end-device compatibility or 60 fps. No hardware
ray tracing, new mocap library or AAA character replacement is included.

Still needed: better bespoke character/prop models, broader combat animation,
more varied environmental composition, device profiling and human playtesting.
The shared soldier and procedural geometry remain visible limitations.
