class_name NRPlayer
extends NRActor

const ARSENAL = preload("res://scripts/arsenal.gd")
const WV = preload("res://scripts/weapon_visual.gd")
# Greatsword combo (v7): real Mixamo greatsword motion. Each swing plays part of a clip
# ("from", sped up by "speed") so the clip's fastest moment lands in the "active" window.
const SWINGS = [
	{"dur":.38,"active":[.12,.20],"damage":72.0,"range":3.3,"arc":.75,"lunge":8.5,"sound":"sword_1",
		"clip":"gs_slash_1","from":.142,"speed":1.8},
	{"dur":.40,"active":[.13,.21],"damage":82.0,"range":3.3,"arc":.75,"lunge":8.5,"sound":"sword_2",
		"clip":"gs_slash_2","from":.66,"speed":2.0},
	{"dur":.62,"active":[.32,.41],"damage":175.0,"range":3.9,"arc":1.1,"lunge":7.0,"sound":"sword_heavy","slam":true,
		"clip":"gs_slam","from":.464,"speed":1.8},
]

var yaw: float = 0
var pitch: float = -.08
var pivot: Node3D
var arm: SpringArm3D
var camera: Camera3D
var move_input: Vector2 = Vector2.ZERO
var fire_input: bool = false
var dodge_time: float = 0
var dodge_cooldown: float = 0
var blade_cooldown: float = 0
var shot_cooldown: float = 0
var reload_time: float = 0
var weapon_index: int = 0
var ammo: int = 12
var dash_direction: Vector3 = Vector3.FORWARD
var aim_assist: bool = true
var recoil: float = 0
var step_phase: float = 0
var casing_count: int = 0
var reload_duration: float = 1.25
var melee_pose: float = 0.0
var weapons: Array[Dictionary] = []
var mag: Dictionary = {}           # remaining rounds per weapon id
var shake: float = 0.0
var aim_target: NRActor            # cached aim-assist target (refreshed ~12x/sec)
var aim_refresh: float = 0.0
var barrel_side: int = 1
# Sword
var sword: Node3D
var melee_step: int = 0
var melee_t: float = 0.0
var melee_queued: bool = false
var melee_hits: Dictionary = {}
var sword_out: float = 0.0
var melee_twist: float = 0.0
var slam_done: bool = false
# Beam laser
var beam_on: bool = false
var beam_node: MeshInstance3D
var beam_light: OmniLight3D
var beam_glow: MeshInstance3D
var beam_hit: MeshInstance3D
var beam_flare: MeshInstance3D
var beam_end: Vector3 = Vector3.ZERO
var beam_tick: float = 0.0
var heat_acc: float = 0.0
# Boost dodge
var thrusters: Array[Node3D] = []
var air_dash: bool = true
var coyote: float = 0.0
var airborne_time: float = 0.0
var jump_count: int = 0
var boost_light: OmniLight3D
var exhaust: CPUParticles3D
const DODGE_TIME := .34
const ROLL_TIME := .55
var rolling: bool = false
# v7 healing flask (souls-style): drink takes time, you move slowly, a hit before the sip wastes it.
const FLASK_MAX := 3
const DRINK_TIME := 1.25
const SIP_AT := .62
var flasks: int = FLASK_MAX
var drinking: float = 0.0
var sipped: bool = false
var flask_prop: Node3D
var backstepping: bool = false

func _ready() -> void:
	collision_layer = 2
	collision_mask = 1 | 4
	weapons = ARSENAL.loadout(game.loadout if game and "loadout" in game else [])
	for w in weapons: mag[w.id] = w.capacity
	super._ready()
	equip_model(weapon_index)
	ammo = weapons[weapon_index].capacity
	floor_snap_length = .28
	pivot = Node3D.new()
	pivot.position = Vector3(.6, 1.5, 0)
	add_child(pivot)
	arm = SpringArm3D.new()
	arm.spring_length = 3.5
	arm.margin = .2
	arm.collision_mask = 1
	var sweep = SphereShape3D.new()
	sweep.radius = .16
	arm.shape = sweep
	arm.add_excluded_object(get_rid())
	pivot.add_child(arm)
	camera = Camera3D.new()
	camera.fov = 66
	camera.near = .08
	camera.far = 160
	arm.add_child(camera)
	camera.current = true
	sword = Node3D.new()
	sword.top_level = true   # v7: held in both hands, placed from the hand bones
	weapon_mount.add_child(sword)
	WV.build_sword(sword)
	load("res://scripts/mesh_batch.gd").merge(sword)
	sword.visible = false
	build_boost_rig()

func equip_model(index: int) -> void:
	if weapons.is_empty():
		super.equip_model(index)
		return
	var w = weapons[clampi(index, 0, weapons.size()-1)]
	muzzle.position.z = WV.build(weapon_geometry, w.model)
	load("res://scripts/mesh_batch.gd").merge(weapon_geometry)
	if hand_targets.has("Right"):
		hand_targets.Right.position = Vector3(-.01,-.04,-.09) * model_size

func current() -> Dictionary:
	return weapons[weapon_index]

func look(delta: Vector2) -> void:
	yaw -= delta.x * .004
	pitch = clampf(pitch - delta.y * .003, -.65, .45)

func _physics_process(delta: float) -> void:
	if not game or game.mode != "playing" or dead:
		if beam_on: set_beam(false)
		return
	update_actor(delta)
	if is_on_floor() and velocity.y <= 0.0:
		if airborne_time > .35:
			game.sound.play_effect("land", randf_range(.92, 1.05))
			shake = maxf(shake, .18)
			if action_time <= 0 and melee_step == 0: play_action("jump_down", .25, 1.5, .05, .22)
		coyote = .12
		airborne_time = 0
		air_dash = true
		jump_count = 0
	else:
		coyote = maxf(0, coyote - delta)
		airborne_time += delta
		# Jets hold you up during an air boost.
		if dodge_time > 0: velocity.y = maxf(velocity.y, 1.2)
	dodge_cooldown = maxf(0, dodge_cooldown - delta)
	blade_cooldown = maxf(0, blade_cooldown - delta)
	shot_cooldown = shot_cooldown - delta if shot_cooldown > 0 else 0.0
	dodge_time = maxf(0, dodge_time - delta)
	if dodge_time == 0: rolling = false; backstepping = false
	sword_out = maxf(0, sword_out - delta)
	shake = move_toward(shake, 0, delta * 3.5)
	aim_refresh -= delta
	if aim_refresh <= 0:
		aim_refresh = .08
		aim_target = closest_aim_target() if aim_assist else null
	var w = current()
	if reload_time > 0:
		reload_time = maxf(0, reload_time - delta)
		if reload_time == 0:
			ammo = w.capacity
			mag[w.id] = ammo
	var axis = move_input + Vector2(Input.get_action_strength("right") - Input.get_action_strength("left"), Input.get_action_strength("back") - Input.get_action_strength("forward"))
	axis = axis.limit_length()
	var direction = Basis(Vector3.UP, yaw) * Vector3(axis.x, 0, axis.y)
	var shooting = (fire_input or Input.is_action_pressed("fire")) and melee_step == 0
	var speed: float = 6.3
	if shooting: speed = 4.1 * w.move
	if drinking > 0: speed *= .3
	if dodge_time > 0:
		direction = dash_direction
		if backstepping: speed = lerpf(2.0, 9.0, dodge_time / .34)
		else: speed = lerpf(5.5, 11.0, dodge_time / ROLL_TIME) if rolling else lerpf(9.0, 18.5, dodge_time / DODGE_TIME)
	if melee_step > 0:
		direction = melee_forward()
		var s = SWINGS[melee_step-1]
		var p = melee_t / s.dur
		speed = s.lunge * (1.0 - smoothstep(.1, .5, p)) if p < .5 else 0.0
	var accel = 26.0 if axis.length() > .1 else 34.0
	if dodge_time > 0: accel = 120.0
	elif melee_step > 0: accel = 70.0
	velocity.x = move_toward(velocity.x, direction.x * speed, delta * accel)
	velocity.z = move_toward(velocity.z, direction.z * speed, delta * accel)
	move_and_slide()
	var previous_step = step_phase
	step_phase += delta * Vector2(velocity.x,velocity.z).length() * 1.7
	if is_on_floor() and dodge_time <= 0 and floor(step_phase / PI) != floor(previous_step / PI):
		game.sound.footstep(game.stage, clampf(Vector2(velocity.x,velocity.z).length() / 6.3, .3, 1.0))
	var bob = sin(step_phase*2.0)*.018*axis.length()
	pivot.position = Vector3(.6, 1.5+bob, 0).rotated(Vector3.UP, yaw)
	update_boost(delta)
	aim_pitch = lerpf(aim_pitch, pitch, 1.0-exp(-12.0*delta))
	if melee_step > 0:
		update_melee(delta)
	else:
		melee_twist = lerpf(melee_twist, 0, 1.0-exp(-10.0*delta))
		weapon_pose(delta)
	pivot.rotation = Vector3(pitch, yaw, 0)
	arm.spring_length = lerpf(arm.spring_length, 2.25 if shooting else (3.9 if dodge_time > 0 else 3.5), delta * 10)
	camera.fov = lerpf(camera.fov, 58 if shooting else (76 if dodge_time > 0 else 66), delta * 9)
	if melee_step == 0 and dodge_time <= 0 and (direction.length() > .1 or shooting):
		var angle = yaw if shooting else atan2(-direction.x, -direction.z)
		visual.rotation.y = lerp_angle(visual.rotation.y, angle, delta * 14)
	update_drink(delta)
	hand_ik_weight = 0.0 if (rolling or sword.visible or drinking > 0) else 1.0
	locomotion(axis, shooting, delta)
	if shooting:
		if sword_out > 0: holster_sword()
		if w.mode == "beam": update_beam(delta)
		else: shoot()
	elif beam_on:
		set_beam(false)
	if w.mode == "beam" and not shooting and reload_time <= 0 and ammo < w.capacity:
		beam_tick += delta
		if beam_tick > .6:
			heat_acc += delta * 40.0
			while heat_acc >= 1.0 and ammo < w.capacity:
				heat_acc -= 1.0
				ammo += 1
			mag[w.id] = ammo
	if Input.is_action_just_pressed("dodge"): dodge()
	if Input.is_action_just_pressed("jump"): jump()
	if Input.is_action_just_pressed("blade"): blade()
	if Input.is_action_just_pressed("heal"): drink_flask()
	if Input.is_action_just_pressed("reload"): reload_weapon()
	if Input.is_action_just_pressed("swap"): swap_weapon()
	if w.model == 3 and weapon_geometry.has_node("Spin"):
		weapon_geometry.get_node("Spin").rotation.z += delta * (32.0 if shooting else 2.0)
	if sword_out <= 0 and sword.visible and melee_step == 0:
		holster_sword()
	if sword.visible: place_sword()
	recoil = move_toward(recoil, 0, delta * 5)
	camera.rotation.x = recoil * .02
	camera.h_offset = randf_range(-1, 1) * shake * .08
	camera.v_offset = randf_range(-1, 1) * shake * .08
	if global_position.y < -10:
		take_damage(200)

# v7: picks the Mixamo clip for the current movement. Aiming uses 4-way strafe clips
# relative to where the body faces; the drawn greatsword has its own idle/walk/run.
func locomotion(axis: Vector2, shooting: bool, delta: float) -> void:
	if not anim or action_time > 0: return
	var flat = Vector3(velocity.x, 0, velocity.z)
	var speed = flat.length()
	if airborne_time > .08 and dodge_time <= 0:
		play_motion("jump_loop", .2)
		anim.speed_scale = 1.0
		visual.rotation.x = lerpf(visual.rotation.x, -.06 if velocity.y > 0 else .04, 1.0-exp(-8.0*delta))
		return
	var key = "idle"
	if sword.visible:
		key = "gs_run" if speed > 4.0 else ("gs_walk" if speed > .6 else "gs_idle")
	elif shooting and speed > .6:
		var local = flat.rotated(Vector3.UP, -visual.rotation.y)
		var fast = speed > 4.5
		if absf(local.x) > absf(local.z): key = ("run_" if fast else "walk_") + ("r" if local.x > 0 else "l")
		else: key = ("run_" if fast else "walk_") + ("b" if local.z > 0 else "f")
	elif axis.length() > .1 and speed > .6:
		key = "run_f" if speed > 3.2 else "walk_f"
	play_motion(key)
	var ref = {"run_f":6.3,"gs_run":6.3,"walk_f":2.6,"gs_walk":2.6}.get(key, 4.0)
	anim.speed_scale = clampf(speed / ref, .75, 1.3) if key != "idle" and key != "gs_idle" else 1.0

# Greatsword held in both hands: grip at the right hand, blade continuing past it,
# aligned with the line from the left hand (Mixamo greatsword clips are two-handed).
func place_sword() -> void:
	var sk = find_skeleton(model)
	if not sk: return
	var r = sk.find_bone("RightHand"); var l = sk.find_bone("LeftHand")
	if r < 0 or l < 0: return
	var rt: Transform3D = sk.global_transform * sk.get_bone_global_pose(r)
	var lt: Transform3D = sk.global_transform * sk.get_bone_global_pose(l)
	var rh = rt.origin + rt.basis.y.normalized() * .05 * model_size
	var lh = lt.origin + lt.basis.y.normalized() * .05 * model_size
	var dir = rh - lh
	if dir.length() < .02: dir = -visual.global_basis.z
	var up = rt.basis.x.normalized()
	if absf(up.dot(dir.normalized())) > .95: up = Vector3.UP
	sword.global_transform = Transform3D(Basis.looking_at(dir.normalized(), up).scaled(Vector3.ONE * .8 * model_size), rh)

func drink_flask() -> void:
	if dead or flasks <= 0 or drinking > 0 or dodge_time > 0 or melee_step > 0 or not is_on_floor(): return
	if sword.visible: holster_sword()
	flasks -= 1
	drinking = DRINK_TIME
	sipped = false
	end_action()
	play_action("drink", 0.0, 1.2, .12, DRINK_TIME)
	weapon_geometry.visible = false
	if not flask_prop: flask_prop = make_flask()
	flask_prop.visible = true

func make_flask() -> Node3D:
	var sk = find_skeleton(model)
	var holder = BoneAttachment3D.new(); holder.bone_name = "RightHand"; sk.add_child(holder)
	var glass = MeshInstance3D.new(); var cyl = CylinderMesh.new()
	cyl.top_radius = .028; cyl.bottom_radius = .042; cyl.height = .13
	glass.mesh = cyl
	var m = StandardMaterial3D.new(); m.albedo_color = Color(.95,.32,.22); m.emission_enabled = true
	m.emission = Color(1.0,.35,.18); m.emission_energy_multiplier = 2.2; m.roughness = .15
	glass.material_override = m
	glass.position = Vector3(0, .07, .03)
	holder.add_child(glass)
	var glow = OmniLight3D.new(); glow.light_color = Color(1,.45,.25); glow.light_energy = .9; glow.omni_range = 1.4
	glass.add_child(glow)
	return holder

func update_drink(delta: float) -> void:
	if drinking <= 0: return
	drinking = maxf(0, drinking - delta)
	if not sipped and DRINK_TIME - drinking >= SIP_AT:
		sipped = true
		health = minf(max_health, health + max_health * .45)
		game.sound.play_effect("success", 1.35)
	if drinking == 0: finish_drink()

func finish_drink() -> void:
	drinking = 0
	if flask_prop: flask_prop.visible = false
	weapon_geometry.visible = not sword.visible

func cancel_drink() -> void:
	end_action()
	finish_drink()

func weapon_pose(delta: float) -> void:
	var w = current()
	melee_pose = move_toward(melee_pose, 0, delta)
	var reload_blend = sin(clampf(1.0-reload_time/reload_duration,0,1)*PI) if reload_time>0 else 0.0
	weapon_mount.position = weapon_mount.position.lerp(Vector3(0.34, 1.22, -0.26+weapon_kick) * model_size, 1.0-exp(-18.0*delta))
	weapon_mount.rotation.x = lerpf(weapon_mount.rotation.x, aim_pitch*.7-.45*reload_blend, 1.0-exp(-12.0*delta))
	weapon_mount.rotation.y = lerpf(weapon_mount.rotation.y, 0, 1.0-exp(-14.0*delta))
	weapon_mount.rotation.z = lerpf(weapon_mount.rotation.z, -.25*reload_blend, 1.0-exp(-18.0*delta))
	if hand_targets.has("Left"):
		var grip = Vector3(-.07,0,w.grip)*model_size
		var magazine = Vector3(-.08,-.20,-.25)*model_size
		hand_targets.Left.position = hand_targets.Left.position.lerp(grip.lerp(magazine,reload_blend),1.0-exp(-15.0*delta))
	visual.position.y = lerpf(visual.position.y, 0.0, 1.0-exp(-14.0*delta))

# ----------------------------------------------------------------- aiming
func closest_aim_target() -> NRActor:
	var chosen: NRActor
	var best = .11
	var forward = -camera.global_basis.z
	for enemy in game.enemies:
		if not is_instance_valid(enemy) or enemy.dead:
			continue
		var point: Vector3 = enemy.global_position + Vector3.UP * (1.35 * enemy.model_size)
		var to_target = point - camera.global_position
		var angle = forward.angle_to(to_target)
		if angle < best and to_target.length() < 50 and game.line_of_sight(global_position+Vector3.UP*1.3, point):
			chosen = enemy
			best = angle
	return chosen

func aim_point() -> Vector3:
	var origin = camera.global_position
	var destination = origin - camera.global_basis.z * 80
	var query = PhysicsRayQueryParameters3D.create(origin, destination, 1 | 4, [get_rid()])
	var hit = get_world_3d().direct_space_state.intersect_ray(query)
	if not hit.is_empty():
		destination = hit.position
	var target = closest_aim_target() if aim_assist else null
	if target:
		destination = target.global_position + Vector3.UP * (1.2 * target.model_size)
	return destination

# ----------------------------------------------------------------- firearms
func shoot() -> void:
	if shot_cooldown > .001 or reload_time > 0:
		return
	var w = current()
	if ammo <= 0:
		reload_weapon()
		return
	shot_cooldown += w.delay  # carry remainder so fire rate is exact at any frame rate
	ammo -= 1
	mag[w.id] = ammo
	flash()
	muzzle_light.light_color = w.color
	recoil = minf(recoil + w.recoil, 1.8)
	game.sound.play_effect(w.sound, randf_range(.96, 1.04))
	var destination = aim_point()
	var from = muzzle.global_position
	match w.mode:
		"rocket":
			shake = maxf(shake, .5)
			game.player_projectile("rocket", from, (destination-from).normalized(), w)
		"bolt":
			barrel_side = -barrel_side
			from += weapon_mount.global_basis.x * .05 * barrel_side
			game.player_projectile("bolt", from, (destination-from).normalized(), w, aim_target)
		_:
			if w.model < 3: eject_casing()
			elif w.model == 3 and ammo % 3 == 0: eject_casing()
			var spread = w.spread*(1.0+move_input.length()*.8)
			for pellet in range(w.pellets):
				var dir = (destination - from).normalized()
				dir += camera.global_basis.x * randf_range(-spread, spread)
				dir += camera.global_basis.y * randf_range(-spread, spread)
				var query = PhysicsRayQueryParameters3D.create(from, from + dir.normalized() * 80, 1 | 4, [get_rid()])
				var hit = get_world_3d().direct_space_state.intersect_ray(query)
				var end = from + dir.normalized() * 80
				if not hit.is_empty():
					end = hit.position
					if hit.collider is NREnemy:
						var enemy: NREnemy = hit.collider
						var headshot = end.y - enemy.global_position.y > 1.55 * enemy.model_size
						enemy.take_damage(w.damage * (1.6 if headshot else 1.0))
						enemy.hit_push += dir.normalized() * w.push
						game.hud.hit_time = .15
					game.impact(end)
				game.tracer(from, end, w.color, .06)

func update_beam(delta: float) -> void:
	var w = current()
	if reload_time > 0:
		set_beam(false)
		return
	if ammo <= 0:
		set_beam(false)
		game.sound.play_effect("overheat")
		reload_weapon()
		return
	if not beam_on: set_beam(true)
	beam_tick = 0
	heat_acc += w.drain * delta
	while heat_acc >= 1.0 and ammo > 0:
		heat_acc -= 1.0
		ammo -= 1
	mag[w.id] = ammo
	var from = muzzle.global_position
	var destination = aim_point()
	var dir = (destination - from).normalized()
	var query = PhysicsRayQueryParameters3D.create(from, from + dir * 60, 1 | 4, [get_rid()])
	var hit = get_world_3d().direct_space_state.intersect_ray(query)
	var end = from + dir * 60
	if not hit.is_empty():
		end = hit.position
		if hit.collider is NREnemy:
			var enemy: NREnemy = hit.collider
			enemy.take_damage(w.damage * delta)
			enemy.hit_push += dir * w.push
			game.hud.hit_time = .08
		if Engine.get_physics_frames() % 4 == 0: game.impact(end)
	var length = from.distance_to(end)
	var beam_dir = (end - from) / maxf(length, .001)
	var orient = Basis(Quaternion(Vector3.UP, beam_dir))
	var pulse = 1.0 + sin(Time.get_ticks_msec() * .045) * .18 + randf() * .12
	beam_node.global_position = (from + end) * .5
	beam_node.global_basis = orient.scaled_local(Vector3(pulse, length, pulse))
	beam_glow.global_position = beam_node.global_position
	beam_glow.global_basis = orient.scaled_local(Vector3(pulse * 1.15, length, pulse * 1.15))
	beam_end = end
	beam_hit.global_position = end - beam_dir * .05
	beam_hit.scale = Vector3.ONE * (.8 + randf() * .5)
	beam_flare.global_position = from
	beam_flare.scale = Vector3.ONE * (.7 + randf() * .4)
	beam_light.global_position = end - beam_dir * .3
	weapon_kick = .02
	muzzle_light.visible = true
	muzzle_light.light_energy = 2.5
	muzzle_light.light_color = w.color
	shake = maxf(shake, .12)

func set_beam(on: bool) -> void:
	beam_on = on
	if on and not is_instance_valid(beam_node):
		var core_mat = StandardMaterial3D.new()
		core_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		core_mat.albedo_color = Color(.9, 1.0, 1.0)
		var glow_mat = StandardMaterial3D.new()
		glow_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		glow_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		glow_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		glow_mat.albedo_color = Color(.15, .75, 1.0, .55)
		glow_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		beam_node = beam_part(CylinderMesh.new(), .022, core_mat)
		beam_glow = beam_part(CylinderMesh.new(), .1, glow_mat)
		beam_hit = beam_part(SphereMesh.new(), .22, glow_mat)
		beam_flare = beam_part(SphereMesh.new(), .14, glow_mat)
		beam_light = OmniLight3D.new()
		beam_light.light_color = Color("6ff4ff"); beam_light.light_energy = 3.0; beam_light.omni_range = 3.5
		game.effects.add_child(beam_light)
	if is_instance_valid(beam_node):
		for part in [beam_node, beam_glow, beam_hit, beam_flare, beam_light]: part.visible = on
	game.sound.beam(on)

func beam_part(mesh: PrimitiveMesh, radius: float, material: Material) -> MeshInstance3D:
	if mesh is CylinderMesh:
		mesh.top_radius = radius; mesh.bottom_radius = radius; mesh.height = 1.0; mesh.radial_segments = 10; mesh.rings = 1
	elif mesh is SphereMesh:
		mesh.radius = radius; mesh.height = radius * 2; mesh.radial_segments = 12; mesh.rings = 6
	var node = MeshInstance3D.new()
	node.mesh = mesh
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	game.effects.add_child(node)
	return node

func reload_weapon() -> void:
	var w = current()
	if reload_time <= 0 and ammo < w.capacity and not dead:
		reload_duration = w.reload
		reload_time = reload_duration
		if beam_on: set_beam(false)
		game.sound.play_effect("reload" if w.mode != "beam" else "overheat")

func apply_loadout(ids: Array) -> void:
	if beam_on: set_beam(false)
	weapons = ARSENAL.loadout(ids)
	for w in weapons:
		if not mag.has(w.id): mag[w.id] = w.capacity
	weapon_index = clampi(weapon_index, 0, weapons.size()-1)
	equip_model(weapon_index)
	ammo = mag[current().id]
	reload_time = 0

func equip_weapon(id: String) -> void:
	if beam_on: set_beam(false)
	mag[current().id] = ammo
	var found = -1
	for i in range(weapons.size()):
		if weapons[i].id == id: found = i
	if found < 0:
		weapons[weapon_index] = ARSENAL.find(id)
		found = weapon_index
		var ids = []
		for w in weapons: ids.append(w.id)
		game.loadout = ids
		game.save_progress()
	weapon_index = found
	equip_model(weapon_index)
	reload_time = 0
	var w = current()
	ammo = mag.get(w.id, w.capacity)
	game.sound.play_effect("ui", .8)
	if ammo <= 0: reload_weapon()
	holster_sword()

func swap_weapon() -> void:
	if weapons.size() < 2: return
	if beam_on: set_beam(false)
	mag[current().id] = ammo
	weapon_index = (weapon_index + 1) % weapons.size()
	equip_model(weapon_index)
	reload_time = 0
	var w = current()
	ammo = mag.get(w.id, w.capacity)
	game.sound.play_effect("ui", .8)
	if ammo <= 0: reload_weapon()
	holster_sword()

# ----------------------------------------------------------------- boost dodge
func build_boost_rig() -> void:
	var flame = StandardMaterial3D.new()
	flame.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	flame.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	flame.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	flame.albedo_color = Color(.25, .6, 1.0, .55)
	flame.cull_mode = BaseMaterial3D.CULL_DISABLED
	var core = flame.duplicate(); core.albedo_color = Color(.75, .92, 1.0, .8)
	# Two boot jets and two back jets, Iron-style.
	for spec in [[Vector3(-.12,.08,.05),Vector3(0,-1,0)],[Vector3(.12,.08,.05),Vector3(0,-1,0)],[Vector3(-.13,1.28,.22),Vector3(0,-.55,.85)],[Vector3(.13,1.28,.22),Vector3(0,-.55,.85)]]:
		var jet = Node3D.new()
		jet.position = spec[0] * model_size
		visual.add_child(jet)
		jet.basis = Basis(Quaternion(Vector3.DOWN, spec[1].normalized()))
		var back = spec[0].y > 1.0
		for layer in [[.07 if not back else .05,.42 if not back else .3,flame],[.03,.2 if not back else .14,core]]:
			var m = MeshInstance3D.new()
			var c = CylinderMesh.new()
			c.top_radius = layer[0]; c.bottom_radius = 0.0; c.height = layer[1]; c.radial_segments = 10; c.rings = 1
			m.mesh = c; m.material_override = layer[2]; m.position.y = -layer[1] * .5
			m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			jet.add_child(m)
		jet.visible = false
		thrusters.append(jet)
	boost_light = OmniLight3D.new()
	boost_light.light_color = Color("7fd8ff"); boost_light.omni_range = 4.5; boost_light.light_energy = 0
	boost_light.position = Vector3(0, .5, .3); boost_light.visible = false
	visual.add_child(boost_light)
	exhaust = CPUParticles3D.new()
	exhaust.emitting = false
	exhaust.amount = 48
	exhaust.lifetime = .35
	exhaust.local_coords = false
	exhaust.position = Vector3(0, .25, .1)
	exhaust.direction = Vector3(0, -.3, 1)
	exhaust.spread = 25
	exhaust.initial_velocity_min = 3; exhaust.initial_velocity_max = 6
	exhaust.gravity = Vector3(0, 1, 0)
	exhaust.scale_amount_min = .5; exhaust.scale_amount_max = 1.2
	var spark = QuadMesh.new(); spark.size = Vector2(.16, .16)
	var sm = flame.duplicate(); sm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	sm.albedo_color = Color(1,1,1,1)
	sm.vertex_color_use_as_albedo = true
	var soft = GradientTexture2D.new()
	soft.fill = GradientTexture2D.FILL_RADIAL
	soft.fill_from = Vector2(.5,.5); soft.fill_to = Vector2(1,.5)
	soft.width = 32; soft.height = 32
	var g = Gradient.new(); g.set_color(0, Color(1,1,1,1)); g.set_color(1, Color(1,1,1,0))
	soft.gradient = g
	sm.albedo_texture = soft
	spark.material = sm
	exhaust.mesh = spark
	var fade = Gradient.new(); fade.set_color(0, Color(.6, .85, 1, .8)); fade.set_color(1, Color(.1, .3, 1, 0))
	exhaust.color_ramp = fade
	visual.add_child(exhaust)

func jump() -> void:
	if dead or melee_step > 0: return
	if coyote > 0 or is_on_floor():
		velocity.y = 8.6
		coyote = 0
		jump_count = 1
		air_dash = true  # a jump from the ground always restores the air boost
		game.sound.play_effect("jump", randf_range(.95, 1.05))
	elif jump_count == 1 and air_dash:
		# Second press in the air: a short jet-assisted lift.
		velocity.y = 7.0
		jump_count = 2
		air_dash = false
		for jet in thrusters: jet.visible = true
		dodge_time = .12
		dash_direction = Vector3(velocity.x, 0, velocity.z).normalized() if Vector2(velocity.x, velocity.z).length() > .5 else Vector3.FORWARD.rotated(Vector3.UP, yaw)
		game.sound.play_effect("boost", 1.15)

func dodge() -> void:
	if dodge_cooldown > 0 or dead:
		return
	if not is_on_floor():
		if not air_dash: return
		air_dash = false
	rolling = is_on_floor()
	if drinking > 0: cancel_drink()
	dodge_time = ROLL_TIME if rolling else DODGE_TIME
	dodge_cooldown = .75 if rolling else 1.0
	invulnerability = .42
	var axis = move_input + Vector2(Input.get_action_strength("right") - Input.get_action_strength("left"), Input.get_action_strength("back") - Input.get_action_strength("forward"))
	if axis.length() > .2:
		dash_direction = (Basis(Vector3.UP, yaw) * Vector3(axis.x, 0, axis.y)).normalized()
	else:
		dash_direction = Vector3(velocity.x, 0, velocity.z).normalized()
		if dash_direction.length() < .1:
			dash_direction = Vector3.FORWARD.rotated(Vector3.UP, yaw)
	backstepping = rolling and axis.length() <= .2 and Vector2(velocity.x, velocity.z).length() < 1.5
	if melee_step > 0: end_melee()
	if backstepping:
		# No direction held: quick hop backwards, still facing forward (souls backstep).
		dash_direction = visual.global_basis.z.normalized()
		dodge_time = .34
		end_action()
		play_action("hit", .05, 1.7, .04, .34)
		velocity.x = dash_direction.x * 9.0
		velocity.z = dash_direction.z * 9.0
		game.sound.play_effect("land", 1.5)
		return
	if rolling:
		# Souls-style forward roll (Mixamo), body turned into the roll direction.
		visual.rotation.y = atan2(-dash_direction.x, -dash_direction.z)
		end_action()
		play_action("roll", .15, 2.2, .05, ROLL_TIME)
		velocity.x = dash_direction.x * 11.0
		velocity.z = dash_direction.z * 11.0
		game.sound.play_effect("land", 1.35)
		return
	velocity.x = dash_direction.x * 18.5
	velocity.z = dash_direction.z * 18.5
	shake = maxf(shake, .35)
	game.sound.play_effect("boost")

func update_boost(delta: float) -> void:
	var active = dodge_time > 0 and not rolling
	var k = dodge_time / DODGE_TIME
	for jet in thrusters:
		jet.visible = active
		if active: jet.scale = Vector3(1, (.65 + .35 * k) * randf_range(.85, 1.15), 1)
	boost_light.visible = active
	boost_light.light_energy = 5.0 * k
	exhaust.emitting = active
	if active:
		visual.rotation.y = lerp_angle(visual.rotation.y, atan2(-dash_direction.x, -dash_direction.z), 1.0-exp(-25.0*delta))
		visual.rotation.x = lerpf(visual.rotation.x, -.42, 1.0-exp(-20.0*delta))
		visual.position.y = lerpf(visual.position.y, .42 * sin(k * PI), 1.0-exp(-22.0*delta))
	else:
		visual.rotation.x = lerpf(visual.rotation.x, 0, 1.0-exp(-12.0*delta))
	visual.rotation.z = lerpf(visual.rotation.z, -move_input.x*.065, 1.0-exp(-12.0*delta))

# ----------------------------------------------------------------- greatsword
func blade() -> void:
	if dead: return
	if melee_step == 0:
		if blade_cooldown > 0: return
		start_swing(1)
	elif melee_step < 3 and melee_t > SWINGS[melee_step-1].dur * .2:
		melee_queued = true

func start_swing(step: int) -> void:
	if beam_on: set_beam(false)
	melee_step = step
	melee_t = 0
	melee_queued = false
	melee_hits.clear()
	slam_done = false
	sword_out = 1.4
	sword.visible = true
	weapon_geometry.visible = false
	hand_ik_weight = 0.0
	for ik in hand_iks: ik.interpolation = 0.0
	var target = melee_target()
	if target:
		var to = target.global_position - global_position
		visual.rotation.y = atan2(-to.x, -to.z)
	else:
		visual.rotation.y = lerp_angle(visual.rotation.y, yaw, .8)
	if SWINGS[step-1].has("slam"): velocity.y = 5.0
	invulnerability = maxf(invulnerability, .12 if step < 3 else .3)
	var sw = SWINGS[step-1]
	end_action()
	play_action(sw.clip, sw.from, sw.speed, .05 if step == 1 else .03, sw.dur)
	game.sound.play_effect(SWINGS[step-1].sound, randf_range(.95, 1.05))

func melee_target() -> NREnemy:
	var best: NREnemy
	var best_d = 7.0
	for enemy in game.enemies:
		if not is_instance_valid(enemy) or enemy.dead: continue
		var d = global_position.distance_to(enemy.global_position)
		var to = (enemy.global_position - global_position).normalized()
		if d < best_d and Vector3.FORWARD.rotated(Vector3.UP, yaw).dot(to) > -.2:
			best = enemy; best_d = d
	return best

func melee_forward() -> Vector3:
	return Vector3.FORWARD.rotated(Vector3.UP, visual.rotation.y)

func update_melee(delta: float) -> void:
	var s = SWINGS[melee_step-1]
	melee_t += delta
	var p = clampf(melee_t / s.dur, 0, 1)
	melee_twist = 0.0
	# Record the real blade path around the strike; it becomes the slash trail.
	if melee_t >= s.active[0] - .07 and melee_t <= s.active[1] + .06 and sword.visible:
		var trail_pts: Array = melee_hits.get("_pts", [])
		trail_pts.append([visual.to_local(sword.global_transform * Vector3(0,0,-.3)), visual.to_local(sword.global_transform * Vector3(0,0,-1.6))])
		melee_hits["_pts"] = trail_pts
	elif melee_t > s.active[1] + .06 and not melee_hits.has("_trail"):
		melee_hits["_trail"] = true
		game.sword_trail(self, melee_step, melee_hits.get("_pts", []))
	if melee_t >= s.active[0] and melee_t <= s.active[1] + delta:
		melee_damage(s)
	if s.has("slam") and not slam_done and melee_t >= s.active[0] + .05:
		slam_done = true
		var at = global_position + melee_forward() * 1.6
		game.shockwave(at, 2.8, 70.0)
		shake = maxf(shake, 1.0)
		game.sound.play_effect("slam")
	if melee_queued and melee_step < 3 and melee_t >= s.active[1] + .03:
		start_swing(melee_step + 1)
	elif melee_t >= s.dur:
		end_melee()

func melee_damage(s: Dictionary) -> void:
	var forward = melee_forward()
	for enemy in game.enemies.duplicate():
		if not is_instance_valid(enemy) or enemy.dead or melee_hits.has(enemy.get_instance_id()): continue
		var offset = enemy.global_position - global_position
		offset.y = 0
		var reach = s.range + .3 * (enemy.model_size - 1.0)
		if offset.length() > reach: continue
		if offset.length() > .6 and forward.dot(offset.normalized()) < cos(s.arc): continue
		if not game.line_of_sight(global_position + Vector3.UP, enemy.global_position + Vector3.UP): continue
		melee_hits[enemy.get_instance_id()] = true
		enemy.take_damage(s.damage)
		enemy.hit_push += offset.normalized() * (9.0 if s.has("slam") else 5.0)
		enemy.stagger = .55
		enemy.cooldown = maxf(enemy.cooldown, .9)  # a sword hit interrupts their next attack
		if enemy.kind != "boss":
			enemy.windup = 0
			if is_instance_valid(enemy.warning): enemy.warning.queue_free()
		game.hud.hit_time = .2
		game.impact(enemy.global_position + Vector3.UP * 1.2 * enemy.model_size, Color("bcd4ff"), 10)
		game.sound.play_effect("sword_hit", randf_range(.9, 1.1))
		shake = maxf(shake, .45)
		game.hitstop(.035 if not s.has("slam") else .07)

func end_melee() -> void:
	blade_cooldown = .14 if melee_step >= 3 else .04
	melee_step = 0
	melee_queued = false
	sword_out = .9

func holster_sword() -> void:
	sword.visible = false
	weapon_geometry.visible = true
	sword_out = 0
	hand_ik_weight = 1.0
	if hand_targets.has("Right"): hand_targets.Right.position = Vector3(-.01,-.04,-.09) * model_size

# ----------------------------------------------------------------- damage
func take_damage(amount: float) -> void:
	if invulnerability > 0 or dead:
		return
	super.take_damage(amount)
	invulnerability = .25
	if drinking > 0 and not sipped and amount >= 8: cancel_drink()
	if not dead and amount >= 15 and melee_step == 0 and not rolling:
		play_action("hit", .0, 1.6, .05, .32)
	shake = maxf(shake, .3)
	game.hud.hurt_time = .35
	game.sound.play_effect("hurt", randf_range(.9, 1.05))
	if dead and beam_on: set_beam(false)

func eject_casing() -> void:
	if casing_count >= 10: return
	casing_count += 1
	var body = RigidBody3D.new()
	body.mass = .025
	body.collision_layer = 8
	body.collision_mask = 1
	var shape = SphereShape3D.new()
	shape.radius = .035
	var collision = CollisionShape3D.new()
	collision.shape = shape
	body.add_child(collision)
	var shell = MeshInstance3D.new()
	shell.mesh = game.casing_mesh()
	shell.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	body.add_child(shell)
	game.effects.add_child(body)
	body.global_position = weapon_mount.global_position
	body.linear_velocity = camera.global_basis.x*2.2+Vector3.UP*1.4
	body.angular_velocity = Vector3(8,5,2)
	get_tree().create_timer(2.5).timeout.connect(func():
		if is_instance_valid(body): body.queue_free()
		casing_count = maxi(0,casing_count-1)
	)
