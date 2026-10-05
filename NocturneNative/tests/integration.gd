extends SceneTree
var failures: int = 0
var checks: int = 0
var game: Node
func _init() -> void:
	run.call_deferred()
func verify(condition: bool, label: String) -> void:
	checks += 1
	if condition:
		print("PASS ",label)
	else:
		failures += 1
		push_error("FAIL "+label)
func until(condition: Callable, limit: int = 240) -> void:
	for i in range(limit):
		if condition.call(): return
		await physics_frame
func frames(count: int) -> void:
	for i in range(count):
		await physics_frame
func freeze_enemies() -> void:
	for enemy in game.enemies:
		enemy.set_physics_process(false)
func budget() -> void:
	var batches = 0
	for n in game.world.find_children("*","GeometryInstance3D",true,false):
		if n is MultiMeshInstance3D or n is MeshInstance3D: batches += 1
	var limit = 140 if game.world.wave_anchors.size() > 0 else 100
	verify(batches < limit,"stage %d geometry merged into %d batches" % [game.stage+1,batches])
	verify(game.world.path_to(game.world.player_start, game.world.boss_spawn).size() > 0,"stage %d boss room reachable on foot" % (game.stage+1))

func target(at: Vector3) -> NREnemy:
	for e in game.enemies.duplicate():
		if is_instance_valid(e): e.take_damage(99999)
	var foe = game.spawn_enemy("heavy", at)
	foe.set_physics_process(false)
	return foe

func spawn_at(at: Vector3) -> NREnemy:
	var foe = target(at)
	game.clear_timer = -1
	await frames(3)
	return foe

func equip(id: String) -> void:
	var player: NRPlayer = game.player
	player.weapons = load("res://scripts/arsenal.gd").loadout([id])
	player.weapon_index = 0
	player.equip_model(0)
	player.ammo = player.weapons[0].capacity
	player.reload_time = 0
	player.shot_cooldown = 0

func test_v5_features(foe: NREnemy) -> void:
	var player: NRPlayer = game.player
	budget()
	verify(player.weapons.size() == 3,"default loadout carries three weapons")
	player.global_position = Vector3(0,.05,12)
	player.yaw = 0; player.pitch = -.05
	await frames(4)
	# Rocket launcher: projectile flies, explodes, damages by area.
	equip("launcher")
	foe = await spawn_at(Vector3(0,0,4))
	await frames(4)
	var hp = foe.health
	player.shoot()
	verify(game.player_shots.size() == 1,"rocket launcher fires a projectile")
	await frames(30)
	verify(foe.health < hp and game.player_shots.is_empty(),"rocket explosion damages target")
	# Plasma blaster: visible bolts that hit.
	equip("blaster")
	foe = await spawn_at(Vector3(0,0,4))
	await frames(3)
	hp = foe.health
	player.shoot()
	verify(game.player_shots.size() == 1 and game.player_shots[0].kind == "bolt","blaster fires a plasma bolt")
	await frames(20)
	verify(foe.health < hp,"plasma bolt damages target")
	# Beam laser: continuous damage while charge drains.
	equip("laser")
	foe = await spawn_at(Vector3(0,0,4))
	await frames(3)
	hp = foe.health
	player.fire_input = true
	await frames(30)
	verify(player.beam_on and player.ammo < 100,"laser beam drains charge while firing")
	verify(foe.health < hp,"laser beam damages continuously")
	player.fire_input = false
	await frames(2)
	verify(not player.beam_on,"laser beam stops on release")
	# Minigun: high rate of fire and spinning barrels.
	equip("mg")
	foe = await spawn_at(Vector3(0,0,4))
	player.fire_input = true
	await frames(30)
	player.fire_input = false
	verify(player.weapons[0].capacity - player.ammo >= 9,"minigun fires 20 rounds per second")
	verify(player.weapon_geometry.has_node("Spin"),"minigun has rotating barrel cluster")
	# Greatsword 3-hit combo ending in a slam.
	equip("pistol")
	foe = await spawn_at(Vector3(0,0,10))
	foe.max_health = 9999; foe.health = 9999
	player.global_position = Vector3(0,.05,12)
	await frames(3)
	player.blade_cooldown = 0
	player.blade()
	verify(player.sword.visible and not player.weapon_geometry.visible,"sword drawn for melee")
	await until(func(): return player.melee_t > .2)
	player.blade()
	await until(func(): return player.melee_step == 2)
	verify(player.melee_step == 2,"second tap chains combo")
	await until(func(): return player.melee_t > .2)
	player.blade()
	await until(func(): return player.melee_step == 3)
	verify(player.melee_step == 3,"third tap starts heavy slam")
	await until(func(): return player.melee_step == 0)
	verify(player.slam_done and foe.health < 9999-150,"combo and slam deal damage")
	await until(func(): return Engine.time_scale == 1.0, 30)
	verify(Engine.time_scale == 1.0,"hit-stop always releases")
	# Ground dodge (v7: roll).
	player.global_position = Vector3(0,.05,12)
	player.dodge_cooldown = 0
	player.move_input = Vector2(1,0)
	var start = player.global_position
	player.dodge()
	await frames(2)
	verify(player.rolling and player.motion == "roll" and not player.thrusters[0].visible,"ground dodge is a souls-style roll (no jets)")
	verify(player.invulnerability > 0,"roll grants invulnerability")
	await frames(18)
	player.move_input = Vector2.ZERO
	verify(player.global_position.distance_to(start) > 2.8,"roll covers ground")
	# v7 healing flask
	await frames(40)
	player.health = 40.0
	var flasks_before = player.flasks
	player.drink_flask()
	verify(player.drinking > 0 and player.motion == "drink" and player.flasks == flasks_before - 1,"flask starts the drink animation and uses one charge")
	await frames(90)
	verify(player.health > 70.0 and player.drinking == 0 and not player.flask_prop.visible,"flask heals after the sip and the flask is put away")
	player.flasks = 0
	player.drink_flask()
	verify(player.drinking == 0,"no drinking when the flasks are empty")
	player.flasks = player.FLASK_MAX
	await frames(20)
	verify(not player.thrusters[0].visible,"thrusters cut out after boost")
	equip("pistol")
	player.weapons = load("res://scripts/arsenal.gd").loadout(["pistol","rifle","launcher"])
	player.mag.clear()
	for w in player.weapons: player.mag[w.id] = w.capacity
	player.weapon_index = 0; player.equip_model(0); player.ammo = 12

func test_v6_features() -> void:
	var player: NRPlayer = game.player
	# Pause freezes animation and enemies, not just input.
	var foe = await spawn_at(Vector3(4,0,2))
	foe.set_physics_process(true)
	player.global_position = Vector3(0,.05,12)
	player.move_input = Vector2(0,-1)
	await frames(10)
	game.pause_game()
	var anim_pos = player.anim.current_animation_position
	var foe_pos = foe.global_position
	await frames(20)
	verify(get_root().get_tree().paused and is_equal_approx(player.anim.current_animation_position, anim_pos),"pause freezes running animation")
	verify(foe.global_position.is_equal_approx(foe_pos),"pause freezes enemies")
	game.resume_game()
	verify(not get_root().get_tree().paused and player.move_input == Vector2.ZERO,"resume unfreezes with input cleared")
	foe.set_physics_process(false)
	# Jump and air jet.
	player.global_position = Vector3(0,.05,12)
	await frames(15)
	var ground = player.global_position.y
	player.jump()
	var peak = ground
	for i in range(40):
		await physics_frame
		peak = maxf(peak, player.global_position.y)
	verify(peak - ground > 1.2,"jump reaches about 1.6 m")
	await until(func(): return player.is_on_floor(), 120)
	verify(player.is_on_floor(),"player lands after jump")
	player.jump()
	await frames(14)
	var before_air = player.global_position.y
	player.jump()
	await frames(10)
	verify(player.jump_count == 2 and player.global_position.y > before_air,"second jump fires jet lift")
	await until(func(): return player.is_on_floor(), 180)
	player.jump()
	await frames(8)
	player.dodge_cooldown = 0
	player.dodge()
	verify(player.dodge_time > 0 and not player.air_dash,"boost works in mid-air")
	await until(func(): return player.is_on_floor(), 180)
	# Laser beam visually reaches the target (was ~1 m long before v6).
	equip("laser")
	player.global_position = Vector3(0,.05,12); player.yaw = 0; player.pitch = -.05
	foe = await spawn_at(Vector3(0,0,2))
	player.fire_input = true
	await frames(12)
	var beam_len = player.beam_node.global_basis.y.length()
	var muzzle_dist = player.muzzle.global_position.distance_to(player.beam_end)
	player.fire_input = false
	verify(absf(beam_len - muzzle_dist) < .3 and muzzle_dist > 6,"laser beam stretches all the way to its hit point")
	verify(player.beam_end.distance_to(foe.global_position + Vector3.UP) < 1.5,"laser beam ends on the enemy")
	await frames(2)
	# Bullet tracers stretch along their direction.
	equip("rifle")
	foe = await spawn_at(Vector3(0,0,2))
	player.shoot()
	var tracer = game.tracer_pool[(game.tracer_cursor - 1 + game.tracer_pool.size()) % game.tracer_pool.size()]
	verify(tracer.global_basis.y.length() > 5,"bullet tracers reach the target")
	# Faster sword: full three-hit combo finishes in under a second.
	equip("pistol")
	foe = await spawn_at(Vector3(0,0,10))
	player.global_position = Vector3(0,.05,12)
	await frames(3)
	var started = Time.get_ticks_msec()
	var sim = 0.0
	player.blade_cooldown = 0
	player.blade()
	while player.melee_step != 0 and sim < 3.0:
		if player.melee_step < 3 and player.melee_t > .08: player.blade()
		await physics_frame
		sim += get_root().get_physics_process_delta_time() * Engine.time_scale
	verify(sim < 1.2 and player.slam_done,"three-hit greatsword combo (real motion) completes in under 1.2 s of game time")
	# Weapon wheel equips any gun in battle and updates the loadout.
	game.hud.open_wheel()
	verify(game.hud.wheel_open and Engine.time_scale < .5,"weapon wheel opens with slow-motion")
	game.hud.close_wheel(5)
	verify(player.current().id == "laser" and game.loadout.has("laser"),"weapon wheel equips the beam laser")
	verify(Engine.time_scale == 1.0,"closing wheel restores time")
	# Audio categories and radio.
	verify(AudioServer.get_bus_index("Weapons") >= 0 and AudioServer.get_bus_index("Movement") >= 0,"separate audio buses exist")
	game.sound.set_volume("Weapons", .3)
	verify(absf(AudioServer.get_bus_volume_db(AudioServer.get_bus_index("Weapons")) - linear_to_db(.3)) < .01,"gun volume slider changes the weapons bus")
	game.sound.set_volume("Weapons", .9)
	game.sound.set_radio("radio3")
	verify(game.sound.music_name == "radio3","radio station plays chosen track")
	game.spawn_wave()
	game.sound.play_music("boss")
	verify(game.sound.music_name == "radio3","chosen station is not overridden by boss music")
	game.sound.set_radio("")
	verify(game.sound.music_name == "boss","AUTO returns to the context track")
	verify(game.sound.TRACKS.size() == 12,"twelve radio tracks available")
	for t in game.sound.TRACKS:
		verify(ResourceLoader.exists("res://assets/music/%s.ogg" % t[0]),"track file present: "+t[1])
	for e in game.enemies.duplicate(): e.take_damage(99999)
	game.loadout = ["pistol","rifle","launcher"]
	game.save_progress()
	player.apply_loadout(game.loadout)
	player.weapon_index = 0; player.equip_model(0); player.ammo = 12

func run() -> void:
	game = load("res://scenes/Main.tscn").instantiate()
	root.add_child(game)
	game.loadout = ["pistol","rifle","launcher"]  # tests must not inherit a saved loadout
	await frames(3)
	verify(game.mode == "menu","native scene loads into menu")
	verify(ProjectSettings.get_setting("input_devices/pointing/emulate_mouse_from_touch"),"touch taps reach menu buttons")
	verify(ProjectSettings.get_setting("rendering/renderer/rendering_method.mobile") == "mobile","phone build uses Metal mobile renderer")
	verify(game.sound.music_name == "menu","menu music selected")
	game.show_contracts()
	var contract_buttons = game.hud.panel.find_children("*","Button",true,false)
	verify(contract_buttons.size() == 6,"all five contracts offered without unlocking")
	contract_buttons[3].pressed.emit()
	await frames(2)
	verify(game.mode == "playing" and game.stage == 3,"fourth contract starts directly from menu")
	verify(game.sound.music_name == "stage4","stage music selected per contract")
	game.show_menu()
	game.show_arsenal()
	verify(game.hud.panel.find_children("*","Button",true,false).size() == 8,"arsenal lists seven weapons")
	game.show_menu()
	game.start_stage(0)
	freeze_enemies()
	await frames(10)
	var player: NRPlayer = game.player
	verify(player.anim != null and player.anim.is_playing(),"skeletal model and animation player imported")
	verify(game.enemies.size() == 6,"first wave spawns")
	verify(player.camera.global_position.distance_to(player.global_position) < 5,"close third-person camera")
	var origin = player.global_position
	player.move_input = Vector2(0,-1)
	await frames(25)
	player.move_input = Vector2.ZERO
	verify(player.global_position.z < origin.z-1,"camera-relative movement advances")
	player.yaw = PI*.5
	origin = player.global_position
	player.move_input = Vector2(0,-1)
	await frames(20)
	player.move_input = Vector2.ZERO
	verify(player.global_position.x < origin.x-1,"movement rotates with camera")
	player.global_position = Vector3(0,.1,12)
	player.yaw = 0
	await frames(3)
	var foe: NREnemy = game.enemies[0]
	foe.global_position = Vector3(0,0,1)
	await frames(3)
	verify(player.closest_aim_target() == foe,"front enemy acquired by assist")
	foe.global_position = Vector3(0,0,18)
	await frames(3)
	verify(player.closest_aim_target() != foe,"aim assist rejects enemies behind camera")
	foe.global_position = Vector3(0,0,1)
	await frames(3)
	var before = foe.health
	player.shoot()
	verify(player.ammo == 11,"firing consumes ammunition")
	verify(foe.health < before,"weapon ray damages target")
	verify(foe.hit_push.length() > 0,"bullet applies enemy knockback")
	verify(player.casing_count == 1,"shot spawns bounded physical casing")
	verify(player.muzzle.position.z > -.5,"sidearm has short muzzle geometry")
	player.ammo = 0
	player.reload_weapon()
	await frames(85)
	verify(player.ammo == 12,"timed reload refills magazine")
	player.swap_weapon()
	await frames(85)
	verify(player.ammo == 30 and player.weapon_index == 1,"weapon swap reloads assault rifle")
	verify(player.muzzle.position.z < -.9,"rifle equips distinct long-barrel geometry")
	player.dodge()
	var hp = player.health
	player.take_damage(30)
	verify(player.health == hp,"dodge invulnerability blocks damage")
	await frames(30)
	player.take_damage(20)
	verify(player.health < hp,"damage applies after dodge expires")
	game.pause_game()
	origin = player.global_position
	player.move_input = Vector2(1,0)
	await frames(8)
	verify(player.global_position.is_equal_approx(origin),"pause stops simulation")
	game.resume_game()
	verify(player.move_input == Vector2.ZERO and not player.fire_input,"resume clears held touch state")
	verify(not game.line_of_sight(Vector3(-10,1,0),Vector3(-10,1,-14)),"cover blocks line of sight")
	var route = game.world.path_to(Vector3(-10,0,0),Vector3(-10,0,-14))
	verify(route.size() > 14,"navigation routes around parked van")
	player.global_position = Vector3(0,0,12)
	player.yaw = 0
	foe.global_position = Vector3(0,0,10)
	var wall = game.world.block(Vector3(0,1.5,11),Vector3(2,3,.3),Color.GRAY)
	await frames(3)
	before = foe.health
	player.blade_cooldown = 0
	player.blade()
	await frames(30)
	verify(foe.health == before,"melee cannot pass through solid cover")
	wall.free()
	player.global_position = Vector3(0,0,12)
	await frames(3)
	player.blade_cooldown = 0
	player.blade()
	await frames(30)
	verify(foe.health < before,"unobstructed close melee connects")
	await test_v5_features(foe)
	await test_v6_features()
	for index in range(5):
		game.start_stage(index)
		freeze_enemies()
		await frames(3)
		verify(game.world.grid!=null,"navigation grid exists in stage "+str(index+1))
		budget()
		for enemy in game.enemies:
			verify(game.world.path_to(enemy.position,game.player.position).size()>0,"spawn has navigable path in stage "+str(index+1))
		for wave_index in range(game.wave_counts[index]):
			for cleanup_round in range(3):
				for enemy in game.enemies.duplicate():
					if enemy.kind == "boss" and not enemy.phase_two:
						enemy.health = enemy.max_health*.4
						enemy._physics_process(.01)
						verify(enemy.phase_two,"boss enters second phase in stage "+str(index+1))
						enemy.attack_count=2 if index in [0,4] else (4 if index==1 else 0)
						enemy.boss_attack(5)
						verify(enemy.windup>0 if index in [0,4] else game.hazards.size()>0,"distinct boss special attack in stage "+str(index+1))
						enemy.windup=0
						enemy.charge_time=0
						enemy.set_physics_process(false)
					enemy.take_damage(99999)
				if game.enemies.is_empty(): break
			game._physics_process(2.1)
			if game.objective_pending:
				game.player.position=Vector3(0,.1,15)
				game.interact_objective()
				verify(game.objective_pending,"objective rejects distant activation in stage "+str(index+1))
				game.player.position=game.world.objective_position+Vector3(0,.1,2)
				game.interact_objective()
				verify(game.objective_done and not game.objective_pending,"objective unlocks boss in stage "+str(index+1))
			freeze_enemies()
			await frames(2)
		verify(game.mode == "complete","all encounters complete in stage "+str(index+1))
		verify(game.cleared[index],"stage "+str(index+1)+" marked cleared")
	verify(game.unlocked == 4,"progress unlocks fifth contract")
	game.start_stage(0)
	freeze_enemies()
	await frames(2)
	game.player.invulnerability=0
	var old_health=game.player.health
	game.hazard(game.player.global_position,2.0,1.0,.3,10,Color.ORANGE)
	game.update_hazards(.2)
	verify(game.player.health==old_health,"telegraph does not damage before activation")
	game.pause_game()
	game._physics_process(2.0)
	verify(game.player.health==old_health,"pause freezes hazards")
	game.resume_game()
	game.update_hazards(.85)
	verify(game.player.health<old_health,"active hazard damages player inside radius")
	game.player.invulnerability = 0
	game.player.take_damage(999)
	verify(game.mode == "dead","player death opens retry flow")
	game.start_stage(0)
	freeze_enemies()
	await frames(2)
	verify(game.mode == "playing" and game.player.health == 100,"retry restores player")
	var graphics=game.graphics
	graphics.adaptive=false
	for quality in range(3):
		graphics.choose(quality)
		verify(is_equal_approx(game.get_viewport().scaling_3d_scale,graphics.MAX_SCALE[quality]),"quality preset applies render scale "+str(quality))
	graphics.choose(2)
	for i in range(30):graphics.adjust(40,2)
	verify(is_equal_approx(graphics.scale,graphics.MIN_SCALE[2]),"adaptive resolution respects quality minimum")
	for i in range(90):graphics.adjust(60,2)
	verify(is_equal_approx(graphics.scale,graphics.MAX_SCALE[2]),"adaptive resolution recovers without exceeding maximum")
	graphics.choose(1)
	verify(graphics.MAX_SCALE[1] < 1.0 and graphics.fps_mode == 60,"default renders 3D below native for upscaling at 60 fps")
	verify(game.player.weapon_geometry.get_child_count()<=4,"rifle or sidearm rigid details are batched by material")
	verify(game.player.hand_targets.size()==2,"both hand targets follow the weapon mount")
	verify(game.player.hand_targets.Left.get_parent()==game.player.weapon_mount,"reload hand target uses weapon local space")
	graphics.adaptive=true;graphics.choose(2)
	game.queue_free()
	await frames(4)
	NRWorld.materials.clear()
	print("RESULT: ",checks-failures,"/",checks," checks passed")
	quit(1 if failures else 0)
