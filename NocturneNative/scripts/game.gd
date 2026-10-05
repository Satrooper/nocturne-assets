extends Node3D

var graphics: Node
var world: NRWorld
var player: NRPlayer
var hud: NRHud
var sound: NRAudio
var actors: Node3D
var effects: Node3D
var mode: String = "menu"
var stage: int = 0
var wave: int = 0
var kills: int = 0
var unlocked: int = 0
var best_kills: int = 0
var enemies: Array[NREnemy] = []
var projectiles: Array[Dictionary] = []
var pickups: Array[Node3D] = []
var stage_names = ["NEON UNDERWORLD","THE GLASS PALACE","HOLLOW BAMBOO","ASHWORKS","BLACK CATHEDRAL"]
var boss_names = ["THE ENFORCER","THE DIRECTOR","THE BELLKEEPER","THE FURNACE","THE WARDEN"]
var objective_actions = ["DISABLE THE RELAY","OVERRIDE SECURITY","RING THE SHRINE BELL","SHUT DOWN THE VALVE","BREAK THE SEAL"]
var objective_pending: bool = false
var objective_done: bool = false
var hazards: Array[Dictionary] = []
var objectives = ["Clear the checkpoint and disable its relay.","Breach the lobby and override security.","Follow the shrine path and ring the bell.","Reach the furnace and close its fuel valve.","Break the seal. End the Warden's reign."]
var wave_counts = [3,3,3,3,4]
var clear_timer: float = -1
const ARSENAL = preload("res://scripts/arsenal.gd")
var loadout: Array = ["pistol","rifle","launcher"]
var cleared: Array = [false,false,false,false,false]
var player_shots: Array[Dictionary] = []
var spark_pool: Array[CPUParticles3D] = []
var spark_cursor: int = 0
var tracer_pool: Array[MeshInstance3D] = []
var tracer_life: PackedFloat32Array = PackedFloat32Array()
var tracer_cursor: int = 0
var hitstop_until: int = 0
static var shared: Dictionary = {}
var stage_clock: float = 0
var damage_taken: float = 0

func _ready() -> void:
	randomize()
	process_mode = Node.PROCESS_MODE_ALWAYS  # menus run while the world is frozen
	graphics=load("res://scripts/graphics.gd").new();graphics.game=self;add_child(graphics)
	configure_input()
	load_progress()
	sound = NRAudio.new()
	add_child(sound)
	var canvas = CanvasLayer.new()
	add_child(canvas)
	hud = NRHud.new()
	hud.game = self
	canvas.add_child(hud)
	build_stage(0)
	show_menu()
	sound.play_music("menu")
	for arg in OS.get_cmdline_user_args():
		if arg == "--preview":
			start_stage(0)
		if arg.begins_with("--capture="):
			capture_frame.call_deferred(arg.trim_prefix("--capture="))

func configure_input() -> void:
	var bindings = {"forward":KEY_W,"back":KEY_S,"left":KEY_A,"right":KEY_D,"dodge":KEY_SHIFT,"jump":KEY_SPACE,"wheel":KEY_TAB,"reload":KEY_R,"blade":KEY_Q,"swap":KEY_E,"pause":KEY_ESCAPE,"fire":KEY_J,"interact":KEY_F,"heal":KEY_H}
	for action in bindings:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		var key = InputEventKey.new()
		key.physical_keycode = bindings[action]
		InputMap.action_add_event(action,key)
	# Left-click fires on desktop only. On a touchscreen, every touch is turned into an
	# emulated left-click (so menu buttons work), which would otherwise fire the gun
	# whenever a finger touches the move stick or any HUD button.
	if not DisplayServer.is_touchscreen_available():
		var mouse = InputEventMouseButton.new()
		mouse.button_index = MOUSE_BUTTON_LEFT
		InputMap.action_add_event("fire",mouse)

func build_stage(index: int) -> void:
	if is_instance_valid(world):
		world.free()
	if is_instance_valid(actors):
		actors.free()
	if is_instance_valid(effects):
		effects.free()
	enemies.clear()
	projectiles.clear()
	hazards.clear()
	pickups.clear()
	world = NRWorld.new()
	world.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(world)
	world.build(index)
	actors = Node3D.new()
	actors.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(actors)
	effects = Node3D.new()
	effects.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	effects.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(effects)
	player_shots.clear()
	build_pools()
	player = NRPlayer.new()
	player.game = self
	player.position = world.player_start
	actors.add_child(player)
	player.defeated.connect(on_player_defeated)
	graphics.apply()

func start_stage(index: int) -> void:
	get_tree().paused = false
	mode = "loading"
	hud.close_panel()
	hud.reset_controls()
	stage = index
	wave = 0
	clear_timer = -1
	stage_clock = 0
	objective_pending = false
	objective_done = false
	build_stage(index)
	mode = "playing"
	Engine.time_scale = 1.0
	spawn_wave()
	announce("CONTRACT 0%d / %s" % [stage+1,stage_names[stage]])
	sound.play_music("stage%d" % (stage+1))
	sound.set_stage_acoustics(stage)

func spawn_wave() -> void:
	wave += 1
	clear_timer = -1
	var count = 6 if wave==1 or wave==wave_counts[stage] else 8
	var types = ["runner","guard","heavy","marksman","shield"]
	var anchors: Array = world.wave_anchors
	if not anchors.is_empty() and wave-1 < world.wave_hints.size() and world.wave_hints[wave-1] != "":
		announce(world.wave_hints[wave-1])
	for i in range(count):
		var preferred = Vector3(-8 if i%2==0 else 8,.05,-17+(i/2)*5)
		if not anchors.is_empty():
			preferred = anchors[mini(wave-1, anchors.size()-1)] + Vector3(-5 if i%2==0 else 5, .05, -3+(i/2)*2.5)
		var kind = types[(i+stage+wave-1)%types.size()]
		spawn_enemy(kind,world.safe_spawn(preferred))
	if wave == wave_counts[stage]:
		spawn_enemy("boss",world.safe_spawn(world.boss_spawn))
		if anchors.is_empty() or wave-1 >= world.wave_hints.size(): announce(boss_names[stage]+" / FINAL ENCOUNTER")
		sound.play_music("boss",.8)
	else:announce("SECTOR %d / %d" % [wave,wave_counts[stage]])

func spawn_enemy(kind: String, location: Vector3) -> NREnemy:
	var enemy = NREnemy.new()
	enemy.game = self
	enemy.kind = kind
	enemy.position = location
	actors.add_child(enemy)
	enemy.defeated.connect(on_enemy_defeated)
	enemies.append(enemy)
	return enemy

func _physics_process(delta: float) -> void:
	if mode != "playing":
		return
	stage_clock += delta
	update_hazards(delta)
	update_player_shots(delta)
	if Input.is_action_just_pressed("interact"): interact_objective()
	for i in range(projectiles.size()-1,-1,-1):
		var bullet = projectiles[i]
		var origin: Vector3 = bullet.node.global_position
		var destination: Vector3 = origin + bullet.velocity*delta
		var query = PhysicsRayQueryParameters3D.create(origin,destination,1|2)
		var hit = get_world_3d().direct_space_state.intersect_ray(query)
		bullet.life -= delta
		if not hit.is_empty():
			if hit.collider == player:
				player.take_damage(bullet.damage)
			impact(hit.position)
			bullet.life = 0
		bullet.node.global_position = destination
		if bullet.life <= 0:
			bullet.node.queue_free()
			projectiles.remove_at(i)
	for i in range(pickups.size()-1,-1,-1):
		var pickup = pickups[i]
		pickup.rotation.y += delta*1.5
		if pickup.global_position.distance_to(player.global_position+Vector3.UP*.4) < 1.4:
			player.health = minf(player.max_health,player.health+28)
			pickup.queue_free()
			pickups.remove_at(i)
			announce("+28 VITALS")
			sound.play_effect("success",1.3)
	if clear_timer >= 0:
		clear_timer -= delta
		if clear_timer <= 0:
			clear_timer = -1
			if wave == wave_counts[stage]-1 and not objective_done:
				objective_pending = true
				world.set_objective_active(true)
				announce(objective_actions[stage]+" / REACH THE MARKER")
			elif wave < wave_counts[stage]:
				spawn_wave()
			else:
				mission_complete()
	if Input.is_action_just_pressed("pause"):
		pause_game()

func _unhandled_input(event: InputEvent) -> void:
	if mode == "paused" and event.is_action_pressed("pause"):
		resume_game()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT and mode == "playing":
		pause_game()

func on_enemy_defeated(enemy: NRActor) -> void:
	enemies.erase(enemy)
	kills += 1
	impact(enemy.global_position+Vector3.UP)
	if kills%3 == 0:
		var pickup = Node3D.new()
		effects.add_child(pickup)
		pickup.global_position = enemy.global_position+Vector3.UP*.45
		NRWorld.part(pickup,Vector3.ZERO,Vector3(.55,.15,.2),Color("a9f68a"),true)
		NRWorld.part(pickup,Vector3.ZERO,Vector3(.15,.55,.2),Color("a9f68a"),true)
		pickups.append(pickup)
	if enemies.is_empty():
		clear_timer = 2

func on_player_defeated(_actor: NRActor) -> void:
	mode = "dead"
	hud.reset_controls()
	hud.show_panel("SIGNAL LOST","Not your last night.","Use cover to break line of sight. Dodge incoming rounds. The blade is strongest at close range.",[["RETRY CONTRACT",func(): start_stage(stage)],["MAIN MENU",show_menu]])

func mission_complete() -> void:
	mode = "complete"
	unlocked = maxi(unlocked,mini(stage+1,4))
	cleared[stage] = true
	sound.play_music("menu",2.0)
	best_kills = maxi(best_kills,kills)
	save_progress()
	sound.play_effect("success")
	var final_stage = stage == 4
	var buttons = [["PLAY AGAIN" if final_stage else "NEXT CONTRACT",func():
		if final_stage: kills = 0
		start_stage(0 if final_stage else stage+1)
	],["MAIN MENU",show_menu]]
	hud.show_panel("CONTRACT FULFILLED" if final_stage else "DISTRICT SECURED","You own the night." if final_stage else "Clean work.","%s cleared in %d seconds.\n%d hostiles eliminated across this run." % [stage_names[stage],int(stage_clock),kills],buttons)

func show_menu() -> void:
	get_tree().paused = false
	mode = "menu"
	Engine.time_scale = 1.0
	sound.play_music("menu")
	var buttons = [["SELECT CONTRACT",show_contracts],["ARSENAL  /  LOADOUT",show_arsenal],["RADIO",show_radio],["AUDIO",show_audio],["CONTROLS",show_controls],["GRAPHICS  /  FPS",show_graphics]]
	hud.show_panel("N / INDEPENDENT OPERATIONS","NOCTURNE","BLACK RAIN / V6\nFive contracts. Five adversaries. All open.",buttons,2)

func back_target() -> Callable:
	return show_menu if mode == "menu" else pause_settings_back

func show_radio() -> void:
	var buttons = [[("▶ " if sound.radio_track == "" else "")+"AUTO  (stage + boss)",func(): sound.set_radio(""); show_radio()]]
	for t in sound.TRACKS:
		var id = t[0]
		buttons.append([("▶ " if sound.radio_track == id else "")+t[1],func(): sound.set_radio(id); show_radio()])
	buttons.append(["BACK",back_target()])
	hud.show_panel("NOCTURNE RADIO","Now playing: "+sound.track_title(sound.music_name),"AUTO follows each contract and switches to the boss theme. Pick a station to keep it on. In battle, tap ♫ to skip.",buttons,2)

func show_audio() -> void:
	var rows = []
	for bus in ["Master","Music","Weapons","Effects","Movement","UI"]:
		var name = bus
		var label = {"Master":"MASTER","Music":"MUSIC","Weapons":"GUNS & SWORD","Effects":"EXPLOSIONS & HITS","Movement":"FOOTSTEPS & JETS","UI":"MENU CLICKS"}[bus]
		rows.append(["%s  %d%%" % [label, roundi(sound.volumes[bus]*100)],func(): sound.set_volume(name, 0.0 if sound.volumes[name] > 0 else .8); show_audio()])
		rows.append(["−",func(): sound.set_volume(name, snappedf(sound.volumes[name]-.1,.1)); show_audio()])
		rows.append(["+",func(): sound.set_volume(name, snappedf(sound.volumes[name]+.1,.1)); show_audio()])
	rows.append(["BACK",back_target()])
	hud.show_panel("AUDIO MIX","Volume","Tap a name to mute/unmute it. Gunfire echoes change with each stage's surroundings.",rows,3)

func show_contracts() -> void:
	var buttons = []
	for i in range(5):
		var index = i
		buttons.append(["0%d  %s%s" % [i+1,stage_names[i],"  ✓" if cleared[i] else ""],func():
			kills = 0
			start_stage(index)
		])
	buttons.append(["BACK",show_menu])
	hud.show_panel("CONTRACTS","Choose your night.","Every contract is unlocked. Boss: "+", ".join(boss_names)+".",buttons,2)

func show_arsenal() -> void:
	var buttons = []
	var lines = []
	for w in ARSENAL.WEAPONS:
		var id = w.id
		var on = loadout.has(id)
		buttons.append([("■ " if on else "□ ")+w.name,func():
			if loadout.has(id):
				if loadout.size() > 1: loadout.erase(id)
			elif loadout.size() < ARSENAL.MAX_LOADOUT:
				loadout.append(id)
			else:
				loadout.pop_front(); loadout.append(id)
			save_progress()
			if mode == "paused" and is_instance_valid(player): player.apply_loadout(loadout)
			show_arsenal()
		])
	for id in loadout: lines.append(ARSENAL.find(id).name.split(" / ")[1])
	buttons.append(["DONE",back_target()])
	hud.show_panel("ARSENAL / CARRY UP TO 3","Loadout","Equipped: "+"  ·  ".join(lines)+"\nSWAP cycles them in battle. SWORD is always on your back.",buttons,2)

func show_controls() -> void:
	hud.show_panel("FIELD MANUAL","Own the night.","TOUCH: Left stick moves. Swipe right side to look. Hold and drag FIRE to shoot and aim. SWORD: tap up to 3 times (third hit is a slam). ROLL dodges (invulnerable); standing still it is a quick backstep. In the air it becomes a jet air-dash. FLASK drinks a healing flask (3 per life). Tap ⇄ to cycle guns, HOLD ⇄ for the weapon wheel. ♫ changes the radio.\n\nDESKTOP: WASD • Drag mouse to aim • Click/J fire • Q sword • Space jump • Shift roll • H flask • Tab wheel • 1-7 weapons • R reload • E swap • F interact • Esc pause.",[["BACK",back_target()]])

func pause_game() -> void:
	if mode != "playing": return
	mode = "paused"
	Engine.time_scale = 1.0
	get_tree().paused = true  # freezes animation, particles, enemies, tweens — everything
	if is_instance_valid(player) and player.beam_on: player.set_beam(false)
	hud.reset_controls()
	hud.show_panel("CONTRACT ON HOLD","Take a breath.","Everything is frozen until you resume.",[["RESUME",resume_game],["ARSENAL",show_arsenal],["RADIO",show_radio],["AUDIO",show_audio],["GRAPHICS",show_graphics],["CONTROLS",show_controls],["RESTART",func(): start_stage(stage)],["MAIN MENU",show_menu]],2)

func resume_game() -> void:
	get_tree().paused = false
	hud.close_panel()
	hud.reset_controls()
	mode = "playing"

func announce(text: String) -> void:
	hud.message = text
	hud.message_time = 2.5

func line_of_sight(from: Vector3, to: Vector3) -> bool:
	return get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from,to,1)).is_empty()

func tracer(from: Vector3, to: Vector3, color: Color, lifetime: float) -> void:
	if tracer_pool.is_empty(): return
	var line = tracer_pool[tracer_cursor]
	tracer_life[tracer_cursor] = lifetime
	tracer_cursor = (tracer_cursor+1) % tracer_pool.size()
	line.material_override = NRWorld.material(color,true)
	var direction = (to-from)
	var length = direction.length()
	if length < .01: return
	line.global_basis = Basis(Quaternion(Vector3.UP,direction/length)).scaled_local(Vector3(1,length,1))
	line.global_position = (from+to)*.5
	line.visible = true

func _process(delta: float) -> void:
	for i in range(tracer_life.size()):
		if tracer_life[i] > 0:
			tracer_life[i] -= delta
			if tracer_life[i] <= 0 and is_instance_valid(tracer_pool[i]): tracer_pool[i].visible = false
	if Engine.time_scale < 1.0 and Time.get_ticks_msec() >= hitstop_until and not hud.wheel_open:
		Engine.time_scale = 1.0

func shared_mesh(key: String) -> Mesh:
	if shared.has(key): return shared[key]
	var mesh: Mesh
	match key:
		"tracer":
			var c = CylinderMesh.new(); c.top_radius=.018; c.bottom_radius=.018; c.height=1; c.radial_segments=6; c.rings=1; mesh=c
		"enemy_bullet":
			var b = SphereMesh.new(); b.radius=.095; b.height=.19; b.radial_segments=8; b.rings=4; mesh=b
		"bolt":
			var b = CapsuleMesh.new(); b.radius=.07; b.height=.75; b.radial_segments=8; b.rings=2; mesh=b
		"rocket":
			var r = CapsuleMesh.new(); r.radius=.07; r.height=.5; r.radial_segments=8; r.rings=2; mesh=r
		"spark":
			var q = BoxMesh.new(); q.size=Vector3(.03,.03,.14); mesh=q
		"casing":
			var c = CylinderMesh.new(); c.top_radius=.018; c.bottom_radius=.018; c.height=.07; c.radial_segments=6; c.rings=1
			c.material=NRWorld.material(Color("b49c59")); mesh=c
		"fireball":
			var f = SphereMesh.new(); f.radius=.5; f.height=1; f.radial_segments=16; f.rings=8; mesh=f
	shared[key] = mesh
	return mesh

func casing_mesh() -> Mesh:
	return shared_mesh("casing")

func build_pools() -> void:
	spark_pool.clear(); tracer_pool.clear(); tracer_life.resize(0)
	var spark_mat = StandardMaterial3D.new()
	spark_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	spark_mat.vertex_color_use_as_albedo = true
	spark_mat.albedo_color = Color(1,1,1)
	var spark: BoxMesh = shared_mesh("spark").duplicate()
	spark.material = spark_mat
	for i in range(14):
		var p = CPUParticles3D.new()
		p.one_shot = true; p.emitting = false; p.explosiveness = 1.0
		p.amount = 10; p.lifetime = .32; p.local_coords = false
		p.mesh = spark
		p.direction = Vector3.UP; p.spread = 80
		p.initial_velocity_min = 3; p.initial_velocity_max = 7.5
		p.gravity = Vector3(0,-12,0)
		p.particle_flag_align_y = true
		p.scale_amount_min = .6; p.scale_amount_max = 1.3
		effects.add_child(p)
		spark_pool.append(p)
	for i in range(28):
		var line = MeshInstance3D.new()
		line.mesh = shared_mesh("tracer")
		line.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		line.visible = false
		effects.add_child(line)
		tracer_pool.append(line)
		tracer_life.append(0.0)

func enemy_projectile(origin: Vector3, direction: Vector3, damage: float) -> void:
	var bullet = MeshInstance3D.new()
	bullet.mesh = shared_mesh("enemy_bullet")
	bullet.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	bullet.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_ON
	bullet.material_override = NRWorld.material(Color("ff8867"),true)
	effects.add_child(bullet)
	bullet.global_position = origin
	bullet.reset_physics_interpolation()
	projectiles.append({"node":bullet,"velocity":direction*16,"damage":damage,"life":4.0})

func impact(at: Vector3, color: Color = Color("ffc788"), _count: int = 6) -> void:
	if spark_pool.is_empty(): return
	var p = spark_pool[spark_cursor]
	spark_cursor = (spark_cursor+1) % spark_pool.size()
	p.global_position = at
	p.color = color
	p.restart()

func hitstop(seconds: float) -> void:
	if mode != "playing": return
	Engine.time_scale = .06
	hitstop_until = Time.get_ticks_msec() + int(seconds*1000.0)

# ------------------------------------------------------------ player projectiles
func player_projectile(kind: String, origin: Vector3, direction: Vector3, w: Dictionary, target: Node3D = null) -> void:
	var node = MeshInstance3D.new()
	node.mesh = shared_mesh(kind)
	node.material_override = NRWorld.material(w.color, true)
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_ON
	effects.add_child(node)
	node.global_position = origin
	node.global_basis = Basis(Quaternion(Vector3.UP, direction))
	node.reset_physics_interpolation()
	if kind == "rocket":
		var trail = CPUParticles3D.new()
		trail.amount = 24; trail.lifetime = .4; trail.local_coords = false
		trail.mesh = spark_pool[0].mesh
		trail.direction = Vector3(0,-1,0); trail.spread = 15
		trail.initial_velocity_min = .5; trail.initial_velocity_max = 1.5
		trail.gravity = Vector3(0,.6,0)
		trail.color = Color("ffb36b")
		trail.position = Vector3(0,-.3,0)
		node.add_child(trail)
		var glow = OmniLight3D.new(); glow.light_color = Color("ff8a3a"); glow.light_energy = 2.0; glow.omni_range = 3.0
		node.add_child(glow)
	player_shots.append({"node":node,"velocity":direction*w.get("speed",40.0),"weapon":w,"life":3.0,"kind":kind,"target":target})

func update_player_shots(delta: float) -> void:
	var space = get_world_3d().direct_space_state
	for i in range(player_shots.size()-1,-1,-1):
		var shot = player_shots[i]
		var node: Node3D = shot.node
		if not is_instance_valid(node):
			player_shots.remove_at(i); continue
		var w: Dictionary = shot.weapon
		if shot.kind == "bolt" and is_instance_valid(shot.target) and not shot.target.dead:
			var want = (shot.target.global_position + Vector3.UP*1.2*shot.target.model_size - node.global_position).normalized()
			var speed = shot.velocity.length()
			shot.velocity = shot.velocity.normalized().slerp(want, clampf(w.get("homing",0.0)*delta,0,1)) * speed
		var origin = node.global_position
		var destination = origin + shot.velocity*delta
		var query = PhysicsRayQueryParameters3D.create(origin,destination,1|4,[player.get_rid()])
		var hit = space.intersect_ray(query)
		shot.life -= delta
		node.global_position = destination
		if shot.velocity.length() > .01:
			node.global_basis = Basis(Quaternion(Vector3.UP, shot.velocity.normalized()))
		if not hit.is_empty():
			if shot.kind == "rocket":
				explode(hit.position - shot.velocity.normalized()*.2, w.radius, w.damage)
			else:
				if hit.collider is NREnemy:
					hit.collider.take_damage(w.damage)
					hit.collider.hit_push += shot.velocity.normalized()*w.push
					hud.hit_time = .15
				impact(hit.position, w.color)
			shot.life = 0
		if shot.life <= 0:
			if shot.kind == "rocket" and hit.is_empty(): explode(node.global_position, w.radius, w.damage)
			node.queue_free()
			player_shots.remove_at(i)

func explode(at: Vector3, radius: float, damage: float) -> void:
	for enemy in enemies.duplicate():
		if not is_instance_valid(enemy) or enemy.dead: continue
		var centre = enemy.global_position + Vector3.UP
		var d = centre.distance_to(at)
		if d > radius + .4*enemy.model_size: continue
		if not line_of_sight(at + Vector3.UP*.3, centre): continue
		var falloff = clampf(1.0 - d/(radius+.5), .35, 1.0)
		enemy.take_damage(damage*falloff)
		var push = (enemy.global_position - at); push.y = 0
		enemy.hit_push += push.normalized()*8.0*falloff
		enemy.stagger = .5
		hud.hit_time = .2
	fireball(at, radius, Color("ff9a4a"))
	sound.play_effect("explosion", randf_range(.92,1.05))
	if is_instance_valid(player):
		var dist = player.global_position.distance_to(at)
		player.shake = maxf(player.shake, clampf(1.4 - dist/14.0, .2, 1.2))

func fireball(at: Vector3, radius: float, color: Color) -> void:
	var ball = MeshInstance3D.new()
	ball.mesh = shared_mesh("fireball")
	var m = StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_color = Color(color.r, color.g*.85, color.b*.6, 1.0)
	ball.material_override = m
	ball.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.add_child(ball)
	ball.global_position = at
	ball.scale = Vector3.ONE*.3
	var flash = OmniLight3D.new(); flash.light_color = color; flash.light_energy = 9.0; flash.omni_range = radius*2.5
	effects.add_child(flash); flash.global_position = at + Vector3.UP*.5
	var ring = make_ring(Vector3(at.x,.08,at.z), .6, color)
	var t = ball.create_tween().set_parallel(true)
	t.tween_property(ball,"scale",Vector3.ONE*radius*1.5,.38).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_EXPO)
	t.tween_property(m,"albedo_color:a",0.0,.42)
	t.tween_property(flash,"light_energy",0.0,.35)
	t.tween_property(ring,"scale",Vector3(radius*1.6,1,radius*1.6),.35)
	t.chain().tween_callback(func():
		ball.queue_free(); flash.queue_free(); ring.queue_free())
	for k in range(3): impact(at + Vector3(randf_range(-.5,.5),.3,randf_range(-.5,.5)), Color("ffb070"))

func shockwave(at: Vector3, radius: float, damage: float) -> void:
	for enemy in enemies.duplicate():
		if not is_instance_valid(enemy) or enemy.dead: continue
		var offset = enemy.global_position - at; offset.y = 0
		if offset.length() > radius: continue
		enemy.take_damage(damage)
		enemy.hit_push += offset.normalized()*7.0
		enemy.stagger = .6
	var ring = make_ring(Vector3(at.x,.06,at.z), .5, Color("9fc4ff"))
	var t = ring.create_tween()
	t.tween_property(ring,"scale",Vector3(radius*2.2,1,radius*2.2),.3).set_ease(Tween.EASE_OUT)
	t.tween_callback(ring.queue_free)
	for k in range(3): impact(at + Vector3(randf_range(-1,1),.1,randf_range(-1,1)), Color("bcd4ff"))

func sword_trail(actor: NRPlayer, step: int, points: Array = []) -> void:
	# v7: trail follows the blade's real recorded path (actor-local space).
	if points.size() < 2: return
	var st = SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var n = points.size() - 1
	for i in range(n):
		var a = points[i]; var b = points[i+1]
		var ka = float(i)/n; var kb = float(i+1)/n
		for v in [[a[0],ka,0.0],[a[1],ka,1.0],[b[1],kb,1.0],[a[0],ka,0.0],[b[1],kb,1.0],[b[0],kb,0.0]]:
			st.set_uv(Vector2(v[1],v[2]))
			st.add_vertex(v[0])
	var trail_mesh = st.commit()
	var trail = MeshInstance3D.new()
	trail.mesh = trail_mesh
	var m = ShaderMaterial.new()
	m.shader = load("res://assets/shaders/slash_trail.gdshader")
	m.set_shader_parameter("tint", Color("a9c8ff") if step < 3 else Color("c7b3ff"))
	trail.material_override = m
	trail.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	effects.add_child(trail)
	trail.global_transform = actor.visual.global_transform
	var t = trail.create_tween()
	t.tween_method(func(v): m.set_shader_parameter("fade", v), 1.0, 0.0, .26)
	t.tween_callback(trail.queue_free)

func make_ring(at: Vector3, radius: float, color: Color) -> MeshInstance3D:
	var ring = MeshInstance3D.new()
	var mesh = TorusMesh.new()
	mesh.inner_radius = radius-.07
	mesh.outer_radius = radius+.07
	mesh.rings = 40
	mesh.ring_segments = 8
	ring.mesh = mesh
	ring.material_override = NRWorld.material(color,true)
	effects.add_child(ring)
	ring.global_position = at
	return ring

func slash(at: Vector3, _angle: float, radius: float = 2.6) -> void:
	var ring = make_ring(at,radius,Color("caff99"))
	var tween = ring.create_tween()
	tween.tween_property(ring,"scale",Vector3(1.2,.1,1.2),.22)
	tween.tween_callback(ring.queue_free)

func load_progress() -> void:
	var config = ConfigFile.new()
	if config.load("user://progress_v3.cfg") == OK:
		unlocked = clampi(config.get_value("progress","unlocked",0),0,4)
		cleared = config.get_value("progress","cleared",cleared)
		var saved = config.get_value("progress","loadout",loadout)
		if saved is Array and not saved.is_empty(): loadout = saved
		best_kills = maxi(0,config.get_value("progress","best_kills",0))

func save_progress() -> void:
	var config = ConfigFile.new()
	config.set_value("progress","unlocked",unlocked)
	config.set_value("progress","best_kills",best_kills)
	config.set_value("progress","cleared",cleared)
	config.set_value("progress","loadout",loadout)
	config.save("user://progress_v3.cfg")

func capture_frame(path: String) -> void:
	await get_tree().create_timer(2.5).timeout
	await RenderingServer.frame_post_draw
	var image = get_viewport().get_texture().get_image()
	var result = image.save_png(path)
	print("CAPTURE_RESULT=",result)
	get_tree().quit()

func interact_objective() -> void:
	if mode != "playing" or not objective_pending: return
	if player.global_position.distance_to(world.objective_position)>2.8:
		announce("GET CLOSER TO THE OBJECTIVE")
		return
	objective_pending=false
	objective_done=true
	world.set_objective_active(false)
	player.health=minf(player.max_health,player.health+35)
	sound.play_effect("success")
	spawn_wave()

func hazard(at: Vector3,radius: float,delay: float,duration: float,damage: float,color: Color) -> void:
	var ring=make_ring(Vector3(at.x,.07,at.z),radius,color)
	hazards.append({"node":ring,"at":Vector3(at.x,0,at.z),"radius":radius,"wait":delay,"life":duration,"damage":damage,"tick":0.0})

func update_hazards(delta: float) -> void:
	for i in range(hazards.size()-1,-1,-1):
		var h=hazards[i]
		h.wait-=delta
		if h.wait>0:
			h.node.scale=Vector3.ONE*(.95+.05*sin(h.wait*15))
		else:
			h.life-=delta;h.tick-=delta
			h.node.position.y=.10
			h.node.scale=Vector3(1,1.5,1)
			if h.tick<=0:
				h.tick=.5
				impact(h.at+Vector3.UP*.2)
				if player.global_position.distance_to(h.at)<h.radius and line_of_sight(h.at+Vector3.UP,player.global_position+Vector3.UP): player.take_damage(h.damage)
			if h.life<=0:
				h.node.queue_free();hazards.remove_at(i)

func show_graphics() -> void:
	var back=back_target()
	var g=graphics
	var note="3D renders at %d%% and is upscaled with MetalFX; HUD stays native. " % int(g.MAX_SCALE[g.profile]*100)
	if g.fps_mode==120 and not g.high_refresh_active():
		note+="120 FPS applies after you fully close and reopen the app. "
	note+="60 FPS runs cooler and saves battery."
	hud.show_panel("DISPLAY / %d FPS TARGET" % g.fps_mode,g.NAMES[g.profile],note,[
		["QUALITY: "+g.NAMES[g.profile],func():g.choose((g.profile+1)%3);show_graphics()],
		["FRAME RATE: %d FPS" % g.fps_mode,func():g.set_fps_mode(120 if g.fps_mode==60 else 60);show_graphics()],
		["ADAPTIVE RES: "+("ON" if g.adaptive else "OFF"),func():g.adaptive=not g.adaptive;g.save();show_graphics()],
		["FPS COUNTER: "+("ON" if g.diagnostics else "OFF"),func():g.diagnostics=not g.diagnostics;g.save();show_graphics()],
		["BACK",back]],2)
func pause_settings_back() -> void:
	mode="playing";pause_game()
