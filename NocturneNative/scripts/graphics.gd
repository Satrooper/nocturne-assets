extends Node
# Rendering budget manager.
# - 3D is rendered below native resolution and upscaled with Apple MetalFX on iPhone
#   (HUD/text stay at full native sharpness).
# - 60 fps (default, cool + smooth) or 120 fps ProMotion (applies after restart).
# - Adaptive resolution lowers 3D resolution briefly if the phone heats up / throttles.
var game: Node
var profile: int = 1
var adaptive: bool = true
var diagnostics: bool = false
var fps_mode: int = 60
var scale: float = 1.0
var measured_fps: float = 0
var elapsed: float = 0
var frames: int = 0
var warmup: float = 5
var stable: float = 0
const NAMES = ["PERFORMANCE","BALANCED","QUALITY"]
const MAX_SCALE = [.67,.77,.87]
const MIN_SCALE = [.50,.58,.66]
const OVERRIDE = "user://display_override.cfg"

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	var cfg = ConfigFile.new()
	if cfg.load("user://graphics_v5.cfg") == OK:
		profile = clampi(int(cfg.get_value("graphics","profile",1)),0,2)
		adaptive = bool(cfg.get_value("graphics","adaptive",true))
		diagnostics = bool(cfg.get_value("graphics","diagnostics",false))
		fps_mode = 120 if int(cfg.get_value("graphics","fps",60)) == 120 else 60
	scale = MAX_SCALE[profile]
	Engine.max_fps = fps_mode

func save() -> void:
	var cfg = ConfigFile.new()
	cfg.set_value("graphics","profile",profile)
	cfg.set_value("graphics","adaptive",adaptive)
	cfg.set_value("graphics","diagnostics",diagnostics)
	cfg.set_value("graphics","fps",fps_mode)
	cfg.save("user://graphics_v5.cfg")

func choose(index: int) -> void:
	profile = clampi(index,0,2)
	scale = MAX_SCALE[profile]
	apply()
	save()

func set_fps_mode(value: int) -> void:
	fps_mode = 120 if value == 120 else 60
	Engine.max_fps = fps_mode
	# iOS reads the ProMotion display-link setting at launch, so persist it as an override.
	var o = ConfigFile.new()
	o.set_value("display","window/ios/allow_high_refresh_rate",fps_mode == 120)
	o.save(OVERRIDE)
	warmup = 3; stable = 0
	save()

func high_refresh_active() -> bool:
	return bool(ProjectSettings.get_setting("display/window/ios/allow_high_refresh_rate",false))

func apply() -> void:
	var vp = get_viewport()
	vp.scaling_3d_scale = scale
	if OS.get_name() == "iOS" and RenderingServer.get_current_rendering_method() != "gl_compatibility":
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_METALFX_SPATIAL
	else:
		vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	vp.msaa_3d = Viewport.MSAA_DISABLED if profile == 0 else Viewport.MSAA_2X
	vp.positional_shadow_atlas_size = 1024 if profile == 0 else 2048
	RenderingServer.directional_shadow_atlas_set_size(1024 if profile == 0 else 2048, true)
	warmup = 4; elapsed = 0; frames = 0; stable = 0
	if game and is_instance_valid(game.world):
		configure_node(game.world)

func configure_node(node: Node) -> void:
	if node is Light3D:
		if not node.has_meta("authored_shadow"): node.set_meta("authored_shadow",node.shadow_enabled)
		node.shadow_enabled = bool(node.get_meta("authored_shadow")) and (profile > 0 or node is DirectionalLight3D)
		if node is DirectionalLight3D:
			node.directional_shadow_max_distance = [26,36,46][profile]
			# 2 cascades instead of 4: half the shadow draw calls, still crisp near the player.
			node.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL if profile == 0 else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
			node.directional_shadow_blend_splits = profile == 2
		elif node is OmniLight3D or node is SpotLight3D:
			node.distance_fade_enabled = true
			node.distance_fade_begin = [18.0,26.0,34.0][profile]
			node.distance_fade_length = 6.0
	if node is WorldEnvironment and node.environment:
		var env: Environment = node.environment
		env.glow_enabled = profile > 0
		env.glow_intensity = .55
		env.glow_strength = 1.0
		env.glow_bloom = .04
		env.glow_hdr_threshold = .95
		env.glow_blend_mode = Environment.GLOW_BLEND_MODE_SCREEN
		for level in range(7): env.set_glow_level(level, 1.0 if level in [1,2,4] else 0.0)
	if node is GPUParticles3D: node.amount_ratio = [.35,.65,1.0][profile]
	if node is ReflectionProbe:
		node.visible = profile > 0
		node.update_mode = ReflectionProbe.UPDATE_ONCE
	for child in node.get_children(): configure_node(child)

func adjust(observed: float, seconds: float) -> void:
	var target = float(fps_mode)
	if observed < target * .9:
		stable = 0
		scale = maxf(MIN_SCALE[profile], scale - .04)
	elif observed > target * .97:
		stable += seconds
		if stable >= 10:
			scale = minf(MAX_SCALE[profile], scale + .02)
			stable = 0
	else:
		stable = 0
	get_viewport().scaling_3d_scale = scale

func _process(delta: float) -> void:
	if not game or game.mode != "playing":
		elapsed = 0; frames = 0
		return
	if warmup > 0:
		warmup -= delta
		return
	elapsed += delta; frames += 1
	if elapsed >= 2:
		measured_fps = float(frames)/elapsed
		if adaptive: adjust(measured_fps, elapsed)
		elapsed = 0; frames = 0
