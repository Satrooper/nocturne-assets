class_name NREnemy
extends NRActor
var kind: String="guard"
var boss_type: int=0
var cooldown: float=1.8
var path_timer: float=0
var path: PackedVector3Array=PackedVector3Array()
var waypoint: int=0
var windup: float=0
var warning: MeshInstance3D
var stagger: float=0
var hit_push: Vector3=Vector3.ZERO
var phase_two: bool=false
var attack_origin: Vector3
var charge_direction: Vector3
var charge_time: float=0
var recovery: float=0
var attack_count: int=0
var charge_hit: bool=false
func _ready() -> void:
	collision_layer=4;collision_mask=1|2|4
	boss_type=game.stage
	costume_role=kind
	team_color=Color("d9a572") if kind=="runner" else Color("cc7272")
	armor_tint=[Color(.56,.51,.44),Color(.38,.43,.49),Color(.55,.48,.33),Color(.65,.42,.25),Color(.43,.45,.56)][game.stage]
	if kind=="boss":
		model_size=[1.35,1.12,1.50,1.50,1.55][boss_type]
		max_health=[800,700,900,1050,1250][boss_type]
	elif kind=="heavy" or kind=="shield":max_health=180
	elif kind=="marksman":max_health=85
	else:max_health=75 if kind=="runner" else 110
	health=max_health
	super._ready()
	if kind=="boss":equip_model(2 if boss_type==0 else 1)
	if kind=="runner" or (kind=="boss" and boss_type==2):
		weapon_geometry.visible=false
		var blade=NRWorld.part(weapon_mount,Vector3(0,-.08,-.47),Vector3(.045,.04,.83),Color("929c96"))
		NRWorld.part(weapon_mount,Vector3(0,-.08,-.09),Vector3(.25,.05,.07),Color("817153"))
	if kind=="shield":
		var shield=NRWorld.part(visual,Vector3(-.22,1.0,-.43),Vector3(.55,.9,.13),Color("394749"))
		NRWorld.part(shield,Vector3(0,.25,-.08),Vector3(.38,.12,.025),Color("182327"))
		NRWorld.part(shield,Vector3(0,-.18,-.08),Vector3(.42,.07,.02),Color("b8a87b"))
func _physics_process(delta: float) -> void:
	if not game or game.mode!="playing" or dead:return
	update_actor(delta)
	cooldown-=delta;path_timer-=delta
	stagger=maxf(0,stagger-delta);recovery=maxf(0,recovery-delta)
	var player: NRActor=game.player
	var offset=player.global_position-global_position;offset.y=0
	var distance=offset.length()
	var can_see=game.line_of_sight(global_position+Vector3.UP*1.4,player.global_position+Vector3.UP*1.2)
	if kind=="boss" and health<max_health*.5 and not phase_two:
		phase_two=true
		game.announce(game.boss_names[boss_type]+" / PHASE II")
		if boss_type==1:
			for x in [-7,7]:game.spawn_enemy("guard",game.world.safe_spawn(global_position+Vector3(x,0,-4)))
	if windup>0:
		windup-=delta
		velocity.x=0;velocity.z=0
		if windup<=0:
			if is_instance_valid(warning):warning.queue_free()
			charge_direction=(attack_origin-global_position).normalized();charge_direction.y=0
			charge_time=.65;charge_hit=false
	elif charge_time>0:
		charge_time-=delta
		velocity.x=charge_direction.x*12;velocity.z=charge_direction.z*12
		play_motion("Run")
		if distance<2.2 and can_see and not charge_hit:
			player.take_damage(26);charge_hit=true
		if charge_time<=0:recovery=1.25
	else:
		var preferred=1.7 if kind=="runner" else (18.0 if kind=="marksman" else 9.0)
		if kind=="boss":preferred=[5.0,12.0,3.0,9.0,5.0][boss_type]
		var direction=Vector3.ZERO
		if distance>preferred or not can_see:
			if path_timer<=0:
				path_timer=.5+randf()*.2
				path=game.world.path_to(global_position,player.global_position);waypoint=1
			if path.size()>waypoint:
				direction=path[waypoint]-global_position;direction.y=0
				if direction.length()<.65:waypoint+=1
				direction=direction.normalized()
			elif can_see:direction=offset.normalized()
		elif kind=="marksman" and distance<8:
			direction=-offset.normalized()
		elif kind=="boss" and boss_type==1:
			direction=offset.normalized().rotated(Vector3.UP,PI*.5 if sin(game.stage_clock*.6)>0 else -PI*.5)
		var speed=4.5 if kind=="runner" else (2.0 if kind in ["heavy","shield"] else 2.7)
		if kind=="boss":speed=[2.8,3.5,3.6,2.1,3.1][boss_type]
		if stagger>0:speed*=.25
		if recovery>0:speed*=.12
		velocity.x=direction.x*speed;velocity.z=direction.z*speed
		if distance>.2:visual.rotation.y=lerp_angle(visual.rotation.y,atan2(-offset.x,-offset.z),delta*8)
		play_motion("Run" if kind=="runner" and direction.length()>.1 else ("Walk" if direction.length()>.1 else "Idle"))
		if cooldown<=0 and can_see and recovery<=0:
			if kind=="runner":
				if distance<2:player.take_damage(13);cooldown=.95
			elif kind=="boss":boss_attack(distance)
			else:
				cooldown=2.5 if kind=="marksman" else 1.9+randf()*.4
				fire_pattern(1,0,18 if kind=="marksman" else 10)
	if anim:
		var gait=[1.0,.92,1.18,.85,.78][clampi(game.stage,0,4)]*(1.12 if kind=="runner" else (.86 if kind=="heavy" else 1.0))
		anim.speed_scale=gait
	velocity.x+=hit_push.x;velocity.z+=hit_push.z
	hit_push=hit_push.move_toward(Vector3.ZERO,delta*14)
	move_and_slide()
func fire_pattern(number: int,spread: float,damage: float) -> void:
	var target=game.player.global_position+Vector3.UP*1.15
	for i in range(number):
		var origin=muzzle.global_position
		var direction=(target-origin).normalized().rotated(Vector3.UP,(i-(number-1)*.5)*spread)
		game.enemy_projectile(origin,direction,damage)
	flash()
func begin_charge() -> void:
	attack_origin=game.player.global_position
	windup=.9 if not phase_two else .65
	warning=game.make_ring(attack_origin+Vector3.UP*.05,1.8,Color("ef9c60"))
	game.announce("CHARGE / MOVE OFF THE MARK")
func boss_attack(distance: float) -> void:
	attack_count+=1
	match boss_type:
		0:
			cooldown=2.1
			if attack_count%3==0 and distance<15:begin_charge()
			else:fire_pattern(5,.095,8)
		1:
			cooldown=.75 if phase_two else 1.2
			fire_pattern(3,.035,9)
			if attack_count%5==0:
				game.hazard(game.player.global_position,2.3,1.0,.2,24,Color("dd967a"));cooldown=2.0
		2:
			cooldown=2.4 if phase_two else 3.0
			if distance>5 and attack_count%2==0:begin_charge()
			else:
				game.hazard(game.player.global_position,3.0,1.0,.18,30,Color("dcb578"));recovery=1.6
		3:
			cooldown=3.3
			var forward=(game.player.global_position-global_position).normalized()
			for i in range(3 if phase_two else 2):
				game.hazard(global_position+forward*(3+i*3),2.1,1.0,3.2,8,Color("ff8342"))
			recovery=2.3
		4:
			cooldown=1.8 if phase_two else 2.3
			if attack_count%3==0:begin_charge()
			elif phase_two and attack_count%2==0:
				game.hazard(game.player.global_position,3.2,.85,.3,30,Color("a7badb"))
			else:fire_pattern(5,.105,11)
func take_damage(amount: float) -> void:
	if dead:return
	if kind=="shield" and game.player:
		var incoming=(game.player.global_position-global_position).normalized()
		if (-visual.global_basis.z).dot(incoming)>.55:amount*=.4
	if kind=="boss":
		if boss_type==0 and not phase_two:amount*=.72
		if boss_type==3:amount*=1.5 if recovery>0 else .72
	stagger=.18 if kind!="boss" else .045
	if not dead and kind != "boss" and action_time <= 0 and randf() < .65:
		play_action("hit", .0, 1.6, .05, .3)
	super.take_damage(amount)
	if dead:
		if is_instance_valid(warning):warning.queue_free()
		get_tree().create_timer(3).timeout.connect(queue_free)
