class_name NRAnims
extends RefCounted
# Shared Mixamo motion library (v7). Every humanoid in the game is retargeted to
# Godot's humanoid skeleton ("%GeneralSkeleton"), so these clips play on all of them.
const LOOPS := ["idle","walk_f","walk_b","walk_l","walk_r","run_f","run_b","run_l","run_r","sprint",
	"jump_loop","kneel","fly","gs_idle","gs_run","gs_walk"]
const KEYS := ["idle","walk_f","walk_b","walk_l","walk_r","run_f","run_b","run_l","run_r","sprint",
	"jump_up","jump_loop","jump_down","death_front","death_back","reload","hit","roll","kneel","fly",
	"gs_idle","gs_run","gs_walk","gs_slash_1","gs_slash_2","gs_slam","gs_spin","drink"]
static var _lib: AnimationLibrary

static func library() -> AnimationLibrary:
	if _lib: return _lib
	_lib = AnimationLibrary.new()
	for key in KEYS:
		var a: Animation
		if ResourceLoader.exists("res://assets/anim/clips/%s.tres" % key):
			a = load("res://assets/anim/clips/%s.tres" % key).duplicate(true)   # baked in-house (tools/bake_*.gd)
		else:
			var src = load("res://assets/anim/clips/%s.fbx" % key)
			if not src or src.get_animation_list().is_empty(): continue
			a = src.get_animation(src.get_animation_list()[0]).duplicate(true)
		in_place(a)
		a.loop_mode = Animation.LOOP_LINEAR if key in LOOPS else Animation.LOOP_NONE
		_lib.add_animation(key, a)
	return _lib

# The game moves the body itself, so horizontal hip travel is removed from every clip
# (vertical bob is kept). Without this, runs would drift and snap back each loop.
static func in_place(a: Animation) -> void:
	for t in a.get_track_count():
		if a.track_get_type(t) != Animation.TYPE_POSITION_3D: continue
		if not String(a.track_get_path(t)).ends_with(":Hips"): continue
		if a.track_get_key_count(t) == 0: continue
		var first: Vector3 = a.track_get_key_value(t, 0)
		for k in a.track_get_key_count(t):
			var v: Vector3 = a.track_get_key_value(t, k)
			a.track_set_key_value(t, k, Vector3(first.x, v.y, first.z))

static func attach(player: AnimationPlayer) -> void:
	if player and not player.has_animation_library("mx"):
		player.add_animation_library("mx", library())
