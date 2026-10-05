> Historical v2 notes. For the current v3 release, read README.md and VALIDATION.md.

# Nocturne — Northline graphics pass 02

This milestone upgrades the first contract only. Glasshouse and The Crown retain their previous environments. This remains a prototype and does not match AAA reference quality.

## Changes
- Northline street replaces Dockside: elevated railway, masonry buildings, shop windows and projecting signs, awnings, fire escapes, cars, grates, street furniture and checkpoint cover.
- Procedural world-space masonry shading; wet asphalt uses the original licensed asphalt maps and a static environment reflection probe.
- Warm street lamps and cooler shop lighting. Spatially grouped MultiMeshes share geometry. Rain is prewarmed.
- Separate procedural pistol, rifle and shotgun geometry; actual muzzle positions update with the model.
- Smoother acceleration and braking, modest movement bob, reload tilt and weapon recoil.
- Limited physical shell casings (maximum ten per player; 2.5-second lifetime).
- Enemy bullet/melee knockback. Melee now checks direction and solid cover.

## Validation
31/31 headless Godot integration checks passed: movement, aim assistance, shooting, ammo/reloads, distinct weapon muzzles, casing creation, knockback, dodge invulnerability, cover navigation, melee obstruction, pause/resume, three-stage completion, boss phase, death and retry.
Desktop OpenGL screenshots were captured from Godot 4.5.2 using a software renderer. Graphical capture completed without script/resource errors; the virtual display reports VSync unavailable.
This version has NOT been compiled for iOS or tested on a physical iPhone. Frame rate, thermal behavior and touch feel still need device testing. Reflections are static environment captures, not screen-space or ray-traced reflections. The models, animation, props and level density still need more work.

## Build on the existing GitHub repository
Replace the repository's existing Nocturne-Native-Project.zip with this version, keeping exactly one matching project ZIP. Keep the root .github/workflows/nocturne-ios.yml workflow already installed. Run Build unsigned iPhone game again. The new unsigned IPA still needs signing with Sideloadly for installation; the old downloaded IPA will not update automatically.

## Desktop editing
Open project.godot with Godot 4.5.2 Standard and press F6/F5 as appropriate. W/A/S/D movement, hold right mouse button and drag to look, J or left click fire, R reload, E weapon swap, Q blade, Space dodge, Escape pause. Touch controls remain enabled for the iPhone build.
