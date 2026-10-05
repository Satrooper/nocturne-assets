extends RefCounted
const W = preload("res://scripts/weapon_visual.gd")
static func attach(actor: NRActor,suffix: String,point: Vector3) -> Node3D:
	var skeleton=actor.find_skeleton(actor.model)
	var mount=Node3D.new()
	var mounts: Array=actor.get_meta("costume_mounts",[])
	mounts.append(mount);actor.set_meta("costume_mounts",mounts)
	if not skeleton:
		actor.visual.add_child(mount);mount.position=point*actor.model_size;return mount
	var bone=-1
	for i in range(skeleton.get_bone_count()):
		if skeleton.get_bone_name(i).ends_with(suffix):bone=i;break
	if bone<0:
		actor.visual.add_child(mount);mount.position=point*actor.model_size;return mount
	var attachment=BoneAttachment3D.new();attachment.bone_name=skeleton.get_bone_name(bone);skeleton.add_child(attachment)
	attachment.add_child(mount)
	var desired=Transform3D(actor.visual.global_basis.scaled(Vector3.ONE*actor.model_size),actor.visual.to_global(point*actor.model_size))
	var bone_world=skeleton.global_transform*skeleton.get_bone_global_pose(bone)
	mount.transform=bone_world.affine_inverse()*desired
	return mount
static func curved(root: Node3D,p: Vector3,s: Vector3,m: Material) -> void:
	var node=MeshInstance3D.new();var mesh=SphereMesh.new();mesh.radius=.5;mesh.height=1;mesh.radial_segments=12;mesh.rings=6
	node.mesh=mesh;node.material_override=m;node.position=p;node.scale=s;root.add_child(node)
static func sculpted_head(actor: NRActor, style: Dictionary) -> Node3D:
	var skeleton=actor.find_skeleton(actor.model)
	if not skeleton: return null
	for mesh in actor.model.find_children("*","MeshInstance3D",true,false):
		if mesh.name.contains("visor"): mesh.visible=false
	var head=load("res://scripts/head.gd").build(style)
	actor.visual.add_child(head)
	head.physics_interpolation_mode=Node.PHYSICS_INTERPOLATION_MODE_OFF
	var rig=load("res://scripts/head_rig.gd").new()
	skeleton.add_child(rig)
	rig.setup(skeleton,head,actor.model_size,actor.visual.global_basis)
	actor.set_meta("sculpted_head",head)
	return head
static func build(actor: NRActor,role: String,stage: int) -> void:
	var accent=[Color("b57945"),Color("b9ad85"),Color("77633c"),Color("b96634"),Color("777e91")][stage]
	if role=="player":accent=Color("557078")
	var armor=W.metal(accent,.48)
	var cloth=W.metal(Color("20292b"),.93)
	cloth.metallic=.02
	var edge=W.metal(Color("9ca3a1"),.32)
	var orange=W.metal(Color("ce9658"),.5)
	var chest=attach(actor,"UpperChest",Vector3(0,1.40,0))
	curved(chest,Vector3(0,0,-.18),Vector3(.46,.38,.16),armor)
	for x in [-.18,.18]:
		W.piece(chest,Vector3(x,.035,-.28),Vector3(.04,.32,.03),cloth)
		W.piece(chest,Vector3(x,-.055,-.305),Vector3(.065,.06,.017),edge)
	for x in [-.13,0,.13]:
		curved(chest,Vector3(x,-.13,-.24),Vector3(.10,.18,.085),cloth)
		W.piece(chest,Vector3(x,-.075,-.286),Vector3(.07,.025,.018),armor)
	var waist=attach(actor,"Hips",Vector3(0,.95,0))
	for x in [-.24,.24]:
		curved(waist,Vector3(x,.02,.06),Vector3(.12,.19,.16),cloth)
		W.piece(waist,Vector3(x,.1,.12),Vector3(.09,.025,.025),edge)
	if role in ["heavy","boss","player"]:
		for side in ["Left","Right"]:
			var sign_x=-1 if side=="Left" else 1
			var shoulder=attach(actor,side+"Arm",Vector3(sign_x*.28,1.48,0))
			curved(shoulder,Vector3.ZERO,Vector3(.30,.22,.31) if role=="boss" else Vector3(.22,.17,.25),armor)
			W.piece(shoulder,Vector3(0,.105,-.03),Vector3(.14,.025,.18),edge)
	if role=="player":
		sculpted_head(actor,load("res://scripts/head.gd").PLAYER)
	var helmet=attach(actor,"Head",Vector3(0,1.70,0))
	if role != "player":
		faction(actor,role,stage,chest,waist)
	if false:
		curved(helmet,Vector3(0,.035,0),Vector3(.32,.27,.32),armor)
		W.piece(helmet,Vector3(0,0,-.163),Vector3(.24,.06,.035),cloth)
		W.piece(helmet,Vector3(0,.006,-.184),Vector3(.19,.016,.008),orange)
		for x in [-.16,.16]:curved(helmet,Vector3(x,-.035,0),Vector3(.055,.1,.1),cloth)
	if role=="runner":
		W.piece(chest,Vector3(0,0,.20),Vector3(.25,.28,.08),armor)
	if role=="boss":
		if stage==0:
			curved(chest,Vector3(0,.0,-.30),Vector3(.55,.42,.10),armor)
			for x in [-.20,0,.20]:W.piece(chest,Vector3(x,0,-.36),Vector3(.055,.3,.025),edge)
		elif stage==1:
			W.piece(chest,Vector3(0,0,.23),Vector3(.27,.32,.13),cloth)
			W.piece(chest,Vector3(.16,.28,.23),Vector3(.025,.30,.025),edge)
		elif stage==2:
			for sign_x in [-1,1]:
				W.piece(head_of(actor,helmet),Vector3(sign_x*.15,.2,-.02),Vector3(.05,.3,.05),orange,Vector3(0,0,sign_x*-.5))
				for i in range(4):W.piece(waist,Vector3(sign_x*.21,-.08-i*.085,-.01),Vector3(.22,.08,.25),armor,Vector3(0,0,sign_x*.18))
		elif stage==3:
			for x in [-.16,.16]:W.barrel(chest,Vector3(x,-.03,.30),.12,.58,armor)
			for y in [-.15,.13]:W.piece(chest,Vector3(0,y,.42),Vector3(.53,.04,.04),edge)
		else:
			for i in range(6):W.piece(chest,Vector3(0,-.18-i*.12,.25+i*.025),Vector3(.45+i*.015,.14,.07),cloth,Vector3(.18,0,0))
			for x in [-.07,0,.07]:W.piece(head_of(actor,helmet),Vector3(x,.27,.02),Vector3(.035,.16,.035),edge)
	# Visible sheathed blade on the player's back and melee specialists.
	if role=="player" or role=="runner" or (role=="boss" and stage in [2,4]):
		W.piece(chest,Vector3(-.12,-.06,.27),Vector3(.055,.77,.06),cloth,Vector3(0,0,-.28))
		W.piece(chest,Vector3(.025,.37,.27),Vector3(.06,.22,.06),armor,Vector3(0,0,-.28))
		W.piece(chest,Vector3(0,.25,.27),Vector3(.20,.04,.10),edge,Vector3(0,0,-.28))

	for mount in actor.get_meta("costume_mounts",[]):load("res://scripts/mesh_batch.gd").merge(mount)

static func head_of(actor: NRActor, fallback: Node3D) -> Node3D:
	var h = actor.get_meta("sculpted_head", null)
	return h if is_instance_valid(h) else fallback

const SKINS = [Color("7a5646"),Color("5c3d30"),Color("9a735d"),Color("4a3127"),Color("b08a72"),Color("6b4a3b"),Color("c4a088")]
const HAIRS = [Color("16110f"),Color("2a1d16"),Color("3b2a1f"),Color("121010")]

static func mat(color: Color, rough: float = .8, metal: float = 0.0, glow: float = 0.0) -> StandardMaterial3D:
	var key = "costume:" + color.to_html() + str(rough) + str(metal) + str(glow)
	var cache = load("res://scripts/head.gd").flat_cache
	if cache.has(key): return cache[key]
	var m = StandardMaterial3D.new(); m.albedo_color = color; m.roughness = rough; m.metallic = metal
	if glow > 0: m.emission_enabled = true; m.emission = color; m.emission_energy_multiplier = glow
	cache[key] = m
	return m

static func blob(root: Node3D, p: Vector3, radii: Vector3, m: Material, rot: Vector3 = Vector3.ZERO, segments: int = 14) -> MeshInstance3D:
	var node = MeshInstance3D.new(); var sphere = SphereMesh.new(); sphere.radius = .5; sphere.height = 1; sphere.radial_segments = segments; sphere.rings = segments/2
	node.mesh = sphere; node.material_override = m; node.position = p; node.scale = radii*2.0; node.rotation = rot
	root.add_child(node); return node

static func cone(root: Node3D, p: Vector3, r_top: float, r_bottom: float, h: float, m: Material, rot: Vector3 = Vector3.ZERO, segments: int = 16) -> MeshInstance3D:
	var node = MeshInstance3D.new(); var c = CylinderMesh.new(); c.top_radius = r_top; c.bottom_radius = r_bottom; c.height = h; c.radial_segments = segments; c.rings = 1
	node.mesh = c; node.material_override = m; node.position = p; node.rotation = rot
	root.add_child(node); return node

# Each stage fields its own faction: face, headgear, clothing and stance.
static func faction(actor: NRActor, role: String, stage: int, chest: Node3D, waist: Node3D) -> void:
	var rng = RandomNumberGenerator.new(); rng.seed = actor.get_instance_id()
	var face = {"skin":SKINS[rng.randi() % SKINS.size()],"hair":HAIRS[rng.randi() % HAIRS.size()],"detail":0,
		"jaw":rng.randf_range(.9,1.15),"nose":rng.randf_range(.9,1.25),"cheek":1.0,"seed":rng.randi() % 7}
	face["beard"] = face.hair
	face["lips"] = face.skin.darkened(.22)
	var beards = ["none","stubble","full"]
	match stage:
		0: face["hair_style"] = "buzz"; face["beard_style"] = beards[rng.randi() % 3]
		1: face["hair_style"] = "slick"; face["beard_style"] = ["none","stubble"][rng.randi() % 2]
		2: face["hair_style"] = "none"; face["beard_style"] = "none"
		3: face["hair_style"] = "none"; face["beard_style"] = "none"; face["eyes"] = false
		_: face["hair_style"] = "none"; face["beard_style"] = "none"; face["eyes"] = false
	var head = sculpted_head(actor, face)
	if not head: return
	var posture = 0.0
	var sway = 0.0
	match stage:
		0: # Syndicate: hoodies or caps, LED face bandanas, bomber jackets.
			var fabric = mat([Color("1d2228"),Color("2b1f2a"),Color("23282a")][rng.randi() % 3], .95)
			var led = mat([Color("39f0ff"),Color("ff3fa8"),Color("ffd23f")][rng.randi() % 3], .4, 0, 3.0)
			if role in ["runner","marksman"]:
				blob(head, Vector3(0,.15,.0), Vector3(.088,.05,.1), fabric)
				cone(head, Vector3(0,.135,-.1), .095, .1, .012, fabric, Vector3(.25,0,0))
			else:
				blob(head, Vector3(0,.095,.028), Vector3(.098,.12,.108), fabric, Vector3.ZERO, 16)
				blob(chest, Vector3(0,.2,.12), Vector3(.2,.08,.12), fabric)
			blob(head, Vector3(0,.015,-.045), Vector3(.083,.042,.068), mat(Color("121417"), .9))
			W.piece(head, Vector3(0,.022,-.112), Vector3(.07,.006,.004), led)
			W.piece(chest, Vector3(0,.0,-.255), Vector3(.34,.36,.02), fabric)
			W.piece(chest, Vector3(0,.0,-.31), Vector3(.012,.36,.01), mat(Color("aeb4b8"),.3,.8))
			posture = .22 if role == "runner" else .05
		1: # Palace security: suits, ties, shades, earpieces.
			var suit = mat(Color("15171c"), .55)
			var shirt = mat(Color("dfe2e4"), .6)
			var shades = mat(Color("06080a"), .08, .6)
			for side in [-1,1]:
				blob(head, Vector3(side*.032,.083,-.103), Vector3(.022,.013,.006), shades)
			W.piece(head, Vector3(0,.088,-.106), Vector3(.02,.004,.004), shades)
			for side in [-1,1]: W.piece(head, Vector3(side*.07,.083,-.05), Vector3(.004,.004,.1), shades)
			blob(head, Vector3(.079,.07,.0), Vector3(.008,.01,.008), mat(Color("1b1b1b"),.4))
			W.piece(chest, Vector3(0,.08,-.262), Vector3(.1,.16,.01), shirt)
			W.piece(chest, Vector3(0,.02,-.27), Vector3(.03,.26,.008), mat(Color("5a1418"),.5))
			for side in [-1,1]:
				W.piece(chest, Vector3(side*.1,.04,-.255), Vector3(.1,.36,.018), suit, Vector3(0,side*.25,side*.16))
			posture = -.03
		2: # Shinobi: straw kasa or full hood, face wrap, sash.
			var indigo = mat(Color("1d2340"), .93)
			var straw = mat(Color("9c8250"), .95)
			blob(head, Vector3(0,.088,.012), Vector3(.087,.112,.1), indigo, Vector3.ZERO, 16)
			blob(head, Vector3(0,.02,-.04), Vector3(.083,.045,.072), indigo)
			if role in ["guard","heavy","shield"]:
				cone(head, Vector3(0,.205,0), .02, .27, .11, straw, Vector3.ZERO, 24)
				cone(head, Vector3(0,.152,0), .27, .27, .006, straw, Vector3.ZERO, 24)
			else:
				W.piece(head, Vector3(0,.13,.09), Vector3(.03,.03,.22), indigo, Vector3(.6,0,0))
			W.piece(waist, Vector3(0,.12,0), Vector3(.52,.08,.36), mat(Color("8d1c1c"),.8))
			W.piece(waist, Vector3(.18,.02,-.16), Vector3(.08,.22,.05), mat(Color("8d1c1c"),.8), Vector3(0,0,.3))
			W.piece(chest, Vector3(0,.05,-.24), Vector3(.05,.4,.02), indigo, Vector3(0,0,.45))
			posture = .2 if role == "runner" else .14
		3: # Furnace crew: hard hat, gas mask, goggles, air tank.
			var hat = mat([Color("d6a21e"),Color("c55a1b"),Color("e3e0d8")][rng.randi() % 3], .45)
			var rubber = mat(Color("1a1c1d"), .7)
			blob(head, Vector3(0,.09,.005), Vector3(.088,.115,.1), rubber, Vector3.ZERO, 16)
			blob(head, Vector3(0,.18,0), Vector3(.1,.06,.115), hat)
			cone(head, Vector3(0,.165,-.01), .13, .135, .012, hat, Vector3(.08,0,0), 20)
			blob(head, Vector3(0,.035,-.085), Vector3(.045,.04,.05), rubber)
			for side in [-1,1]:
				cone(head, Vector3(side*.055,.02,-.1), .028, .028, .04, mat(Color("4b5257"),.4,.6), Vector3(PI*.5,0,side*-.6))
				blob(head, Vector3(side*.032,.085,-.098), Vector3(.02,.02,.008), mat(Color("ff9a3a"),.1,0,1.4))
			cone(chest, Vector3(0,-.02,.28), .1, .1, .55, mat(Color("8c2b1c"),.5,.4))
			W.piece(chest, Vector3(0,-.04,-.262), Vector3(.3,.34,.015), mat(Color("b96a2a"),.85))
			posture = .08
		_: # Cult: deep pointed hood, porcelain mask, long robe.
			var robe = mat([Color("1b0f12"),Color("2a0c10"),Color("15131a")][rng.randi() % 3], .97)
			var porcelain = mat(Color("e8e2d6"), .25)
			blob(head, Vector3(0,.1,.03), Vector3(.105,.135,.12), robe, Vector3.ZERO, 16)
			cone(head, Vector3(0,.24,.07), 0.0, .07, .14, robe, Vector3(-.5,0,0))
			blob(head, Vector3(0,.065,-.088), Vector3(.064,.085,.03), porcelain)
			for side in [-1,1]:
				W.piece(head, Vector3(side*.026,.083,-.117), Vector3(.022,.006,.01), mat(Color("050505"),.9))
			W.piece(head, Vector3(0,.11,-.113), Vector3(.008,.03,.006), mat(Color("8e1b1b"),.5))
			cone(waist, Vector3(0,-.45,0), .24, .44, .95, robe, Vector3.ZERO, 18)
			blob(chest, Vector3(0,.16,.02), Vector3(.24,.1,.17), robe)
			posture = .1
			sway = .06
	if role == "heavy": posture -= .06
	actor.set_meta("posture", posture)
	actor.set_meta("sway", sway)
	var batch = load("res://scripts/mesh_batch.gd")
	batch.merge(head)
