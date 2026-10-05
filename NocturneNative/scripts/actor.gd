class_name NRActor
extends CharacterBody3D

signal defeated(actor)
var health: float = 100.0
var max_health: float = 100.0
var dead: bool = false
var model: Node3D
var anim: AnimationPlayer
var visual: Node3D
var weapon_mount: Node3D
var muzzle: Marker3D
var capsule: CollisionShape3D
var game: Node
var invulnerability: float = 0.0
var model_size: float = 1.0
var team_color: Color = Color("d1ff80")
var motion: String = ""
var muzzle_light: OmniLight3D
var weapon_geometry: Node3D
var weapon_kick: float = 0.0
var aim_pitch: float=0.0
var hand_targets: Dictionary={}
var hand_iks: Array=[]
var costume_role: String = "player"
var armor_tint = Color(.88,.92,.94)
# v7: one-shot Mixamo actions (sword swings, rolls, hits, reloads) lock out locomotion
var action_time: float = 0.0
var hand_ik_weight: float = 1.0
const MOTION_KEYS := {"Idle":"idle","Walk":"walk_f","Run":"run_f"}
const SOLDIER = preload("res://assets/soldier.glb")

func _ready() -> void:
	capsule = CollisionShape3D.new()
	var shape = CapsuleShape3D.new()
	shape.radius = 0.34 * model_size
	shape.height = 1.8 * model_size
	capsule.shape = shape
	capsule.position.y = shape.height / 2.0
	add_child(capsule)
	visual = Node3D.new()
	add_child(visual)
	model = SOLDIER.instantiate()
	model.scale = Vector3.ONE * model_size
	# Godot glTF import faces -Z, matching gameplay.
	model.rotation.y = 0
	visual.add_child(model)
	tint_armor(model)
	anim = find_animation(model)
	NRAnims.attach(anim)
	if anim:
		for name in anim.get_animation_list():
			if name.to_lower().ends_with("idle") or name.to_lower().ends_with("walk") or name.to_lower().ends_with("run"):
				anim.get_animation(name).loop_mode = Animation.LOOP_LINEAR
	play_motion("Idle")
	weapon_mount = Node3D.new()
	weapon_mount.position = Vector3(0.34, 1.22, -0.26) * model_size
	visual.add_child(weapon_mount)
	weapon_geometry = Node3D.new()
	weapon_mount.add_child(weapon_geometry)
	var barrel_end: float = load("res://scripts/weapon_visual.gd").build(weapon_geometry,1)
	load("res://scripts/mesh_batch.gd").merge(weapon_geometry)
	muzzle = Marker3D.new()
	muzzle.position = Vector3(0,.025,barrel_end)
	weapon_mount.add_child(muzzle)
	muzzle_light = OmniLight3D.new()
	muzzle_light.light_color = Color("ffbb70")
	muzzle_light.omni_range = 4.0
	muzzle_light.light_energy = 0
	muzzle_light.visible = false
	muzzle_light.shadow_enabled = false
	muzzle.add_child(muzzle_light)
	setup_hand_ik.call_deferred()
	decorate.call_deferred()
	NRWorld.part(visual, Vector3(0,1.5,.2)*model_size, Vector3(.075,.022,.025)*model_size, team_color, false)

func find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for child in node.get_children():
		var found = find_animation(child)
		if found:
			return found
	return null

func play_motion(name: String, blend: float = .15) -> void:
	if not anim or motion == name or action_time > 0:
		return
	var key: String = MOTION_KEYS.get(name, name)
	if anim.has_animation("mx/"+key):
		anim.play("mx/"+key, blend)
		motion = name
		return
	for clip in anim.get_animation_list():
		if clip.to_lower().ends_with(name.to_lower()):
			anim.play(clip, .15)
			motion = name
			return

func play_action(key: String, from: float = 0.0, speed: float = 1.0, blend: float = .08, hold: float = -1.0) -> void:
	if not anim or not anim.has_animation("mx/"+key): return
	anim.play("mx/"+key, blend, speed)
	anim.seek(from, true)
	var a = anim.get_animation("mx/"+key)
	action_time = hold if hold >= 0 else (a.length - from) / maxf(speed, .01)
	motion = key

func end_action() -> void:
	action_time = 0
	motion = ""

func update_actor(delta: float) -> void:
	invulnerability = maxf(0, invulnerability - delta)
	if action_time > 0:
		action_time = maxf(0, action_time - delta)
		if action_time == 0: motion = ""
	for ik in hand_iks:
		ik.interpolation = move_toward(ik.interpolation, hand_ik_weight, delta * 6.0)
	weapon_kick = move_toward(weapon_kick,0,delta*.9)
	weapon_mount.position.z = (-.26+weapon_kick)*model_size
	if muzzle_light:
		muzzle_light.light_energy = move_toward(muzzle_light.light_energy, 0, delta * 70)
		# A zero-energy light still costs GPU time; hide it between shots.
		muzzle_light.visible = muzzle_light.light_energy > 0.01
	if not is_on_floor():
		velocity.y -= 22.0 * delta

func take_damage(amount: float) -> void:
	if dead or invulnerability > 0:
		return
	health = maxf(0, health - amount)
	if health <= 0:
		dead = true
		collision_layer = 0
		collision_mask = 0
		defeated.emit(self)
		for ik in hand_iks:ik.stop()
		if anim and anim.has_animation("mx/death_front"):
			# Real fall instead of the old tip-over.
			action_time = 0
			play_action("death_front" if randf() < .6 else "death_back", .0, 1.25, .06, 99.0)
		else:
			if anim: anim.stop()
			var tween = create_tween()
			tween.tween_property(visual, "rotation:z", PI * .48, .25)
			tween.parallel().tween_property(visual, "position:y", -.15, .25)

func flash() -> void:
	muzzle_light.visible = true
	muzzle_light.light_energy = 4.0
	weapon_kick = .065

func tint_armor(node: Node) -> void:
	if node is MeshInstance3D:
		for surface in range(node.mesh.get_surface_count()):
			var source = node.get_active_material(surface)
			if source is StandardMaterial3D:
				var m = source.duplicate()
				m.albedo_color = armor_tint
				m.metallic = .08
				m.roughness = .76
				node.set_surface_override_material(surface,m)
	for child in node.get_children():
		tint_armor(child)

func find_skeleton(node: Node) -> Skeleton3D:
	if node is Skeleton3D:
		return node
	for child in node.get_children():
		var found = find_skeleton(child)
		if found: return found
	return null

func setup_hand_ik() -> void:
	var skeleton = find_skeleton(model)
	if not skeleton: return
	var aim_pose=load("res://scripts/aim_pose.gd").new();aim_pose.actor=self;skeleton.add_child(aim_pose)
	for side in ["Right","Left"]:
		var root_name = ""
		var tip_name = ""
		for i in range(skeleton.get_bone_count()):
			var bone_name = skeleton.get_bone_name(i)
			if bone_name.ends_with(side+"UpperArm"): root_name = bone_name
			if bone_name.ends_with(side+"Hand"): tip_name = bone_name
		if root_name.is_empty() or tip_name.is_empty(): continue
		var target = Marker3D.new()
		target.position = Vector3(-.01,-.04,-.09) if side == "Right" else Vector3(-.07,0,-.44)
		target.position *= model_size
		weapon_mount.add_child(target)
		hand_targets[side]=target
		var ik = SkeletonIK3D.new()
		ik.root_bone = root_name
		ik.tip_bone = tip_name
		ik.override_tip_basis = false
		ik.max_iterations = 8 if costume_role == "player" else 3
		skeleton.add_child(ik)
		ik.target_node = ik.get_path_to(target)
		ik.start()
		hand_iks.append(ik)

func equip_model(index: int) -> void:
	muzzle.position.z = load("res://scripts/weapon_visual.gd").build(weapon_geometry,index)
	load("res://scripts/mesh_batch.gd").merge(weapon_geometry)

func decorate() -> void:
	load("res://scripts/costume.gd").build(self,costume_role,game.stage)
	optimise_shadows()

func optimise_shadows() -> void:
	for node in find_children("*","GeometryInstance3D",true,false):
		if node is MeshInstance3D and node.skin == null and not (node.mesh is ArrayMesh and node.get_parent() is Skeleton3D):
			node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
