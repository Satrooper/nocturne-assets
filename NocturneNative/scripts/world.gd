class_name NRWorld
extends Node3D

var grid: AStarGrid2D
var obstacles: Array[Rect2] = []
var stage: int = 0
static var materials: Dictionary = {}
var accent: Color = Color("73cddd")
var rain: GPUParticles3D
var objective_position = Vector3(0,0,-12)
var objective_marker: Node3D
var window_transforms: Array[Transform3D] = []
# Map extents and flow (expanded stages override these in sets.gd).
var area: Rect2i = Rect2i(-23,-21,47,43)
var player_start: Vector3 = Vector3(0,.05,15)
var wave_anchors: Array = []      # per-wave spawn centre; empty = classic arena layout
var boss_spawn: Vector3 = Vector3(0,.1,-17)
var wave_hints: Array = []        # announcement when a wave starts in a new room

static func material(color: Color, glow: bool = false) -> StandardMaterial3D:
	var key = color.to_html() + str(glow)
	if materials.has(key):
		return materials[key]
	var m = StandardMaterial3D.new()
	m.albedo_color = color
	m.metallic = .3
	m.roughness = .48
	if glow:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = 2.0
	materials[key] = m
	return m

static func part(parent: Node3D, pos: Vector3, size: Vector3, color: Color, glow: bool = false) -> MeshInstance3D:
	var mesh = MeshInstance3D.new()
	var shape = BoxMesh.new()
	shape.size = size
	mesh.mesh = shape
	mesh.material_override = material(color, glow)
	mesh.position = pos
	parent.add_child(mesh)
	if glow:
		mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return mesh

func block(pos: Vector3, size: Vector3, color: Color, nav: bool = true) -> StaticBody3D:
	var body = StaticBody3D.new()
	body.position = pos
	body.collision_layer = 1
	body.collision_mask = 0
	add_child(body)
	part(body, Vector3.ZERO, size, color)
	var collision = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)
	if nav:
		obstacles.append(Rect2(Vector2(pos.x-size.x/2-.5,pos.z-size.z/2-.5),Vector2(size.x+1,size.z+1)))
	return body

func build(index: int) -> void:
	stage = index
	accent = [Color("f5b677"),Color("d8ba78"),Color("b5ca83"),Color("f5a66e"),Color("a6c5e6")][stage]
	lighting()
	if stage == 0:
		load("res://scripts/urban.gd").new().build(self)
	else:
		load("res://scripts/sets.gd").new().build_set(self,stage)
	make_objective()
	build_navigation()
	if stage != 1: make_rain()

func make_objective() -> void:
	objective_marker = Node3D.new()
	objective_marker.position = objective_position
	add_child(objective_marker)
	var pedestal = block(objective_position+Vector3.UP*.5,Vector3(.9,1,.7),Color("343c3c"))
	if stage in [0,1]:
		part(objective_marker,Vector3(0,1.2,0),Vector3(.8,.5,.12),Color("273539"))
		part(objective_marker,Vector3(0,1.2,.065),Vector3(.66,.36,.015),accent,true)
		for x in [-.22,0,.22]:part(objective_marker,Vector3(x,.95,.15),Vector3(.08,.03,.08),Color("adb19b"))
	elif stage == 2:
		var bell = MeshInstance3D.new()
		var mesh = CylinderMesh.new();mesh.top_radius=.26;mesh.bottom_radius=.48;mesh.height=.65;mesh.radial_segments=20
		bell.mesh=mesh;bell.material_override=material(Color("a28a50"));bell.position.y=1.6;objective_marker.add_child(bell)
		for x in [-.7,.7]:part(objective_marker,Vector3(x,1,0),Vector3(.12,2,.12),Color("532c20"))
		part(objective_marker,Vector3(0,2.1,0),Vector3(1.6,.13,.16),Color("532c20"))
	elif stage == 3:
		var wheel=MeshInstance3D.new();var mesh=TorusMesh.new();mesh.inner_radius=.26;mesh.outer_radius=.35;mesh.rings=20;mesh.ring_segments=6
		wheel.mesh=mesh;wheel.position=Vector3(0,1.2,.35);wheel.rotation.x=PI*.5;wheel.material_override=material(Color("b76236"));objective_marker.add_child(wheel)
		for rot in [0,PI*.5]:
			var spoke=part(objective_marker,Vector3(0,1.2,.35),Vector3(.58,.05,.05),Color("b76236"));spoke.rotation.z=rot
	else:
		var seal=MeshInstance3D.new();var mesh=TorusMesh.new();mesh.inner_radius=.24;mesh.outer_radius=.31;mesh.rings=24;mesh.ring_segments=6
		seal.mesh=mesh;seal.material_override=material(accent,true);seal.rotation.x=PI*.5;seal.position=Vector3(0,1.35,0);objective_marker.add_child(seal)
	var label=Label3D.new();label.name="ObjectiveLabel";label.text="";label.position=Vector3(0,2.7,0);label.font_size=36;label.pixel_size=.01;label.billboard=BaseMaterial3D.BILLBOARD_ENABLED;objective_marker.add_child(label)

func set_objective_active(active: bool) -> void:
	objective_marker.get_node("ObjectiveLabel").text = "OBJECTIVE / USE" if active else ""

func safe_spawn(preferred: Vector3) -> Vector3:
	var start=Vector2i(clampi(roundi(preferred.x),area.position.x+2,area.end.x-3),clampi(roundi(preferred.z),area.position.y+2,area.end.y-3))
	var home=Vector2i(roundi(player_start.x),roundi(player_start.z))
	for radius in range(0,14):
		for dx in range(-radius,radius+1):
			for dz in range(-radius,radius+1):
				var cell=start+Vector2i(dx,dz)
				if grid.is_in_boundsv(cell) and not grid.is_point_solid(cell):
					if grid.get_id_path(cell,home).size()>0:
						return Vector3(cell.x,.05,cell.y)
	return Vector3(0,.05,5)

func build_navigation() -> void:
	grid = AStarGrid2D.new()
	grid.region = area
	grid.cell_size = Vector2.ONE
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.update()
	# Mark only the cells each obstacle covers (fast even on large maps).
	for rect in obstacles:
		for x in range(int(ceil(rect.position.x)), int(floor(rect.end.x))+1):
			for z in range(int(ceil(rect.position.y)), int(floor(rect.end.y))+1):
				if area.has_point(Vector2i(x,z)) and rect.has_point(Vector2(x,z)):
					grid.set_point_solid(Vector2i(x,z))

func tower(pos: Vector3, size: Vector3, seed_value: int) -> void:
	part(self,pos,size,Color("142633"))
	for y in range(3,int(size.y)-1,3):
		for x in [-1.5,0,1.5]:
			if posmod(y+int(x*2)+seed_value,4) != 0:
				window_transforms.append(Transform3D(Basis.IDENTITY,Vector3(pos.x+x,y,pos.z+size.z/2+.025)))
	part(self,Vector3(pos.x,pos.y+size.y/2+.2,pos.z),Vector3(size.x+.1,.2,size.z+.1),Color("364752"))

func finish_windows() -> void:
	var batch = MultiMeshInstance3D.new()
	var multi = MultiMesh.new()
	multi.transform_format = MultiMesh.TRANSFORM_3D
	var mesh = BoxMesh.new()
	mesh.size = Vector3(.75,1.25,.03)
	mesh.material = material(Color("416274"),true)
	multi.mesh = mesh
	multi.instance_count = window_transforms.size()
	for i in range(window_transforms.size()):
		multi.set_instance_transform(i,window_transforms[i])
	batch.multimesh = multi
	batch.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(batch)

func container(pos: Vector3, size: Vector3, color: Color) -> void:
	block(pos+Vector3.UP*size.y/2,size,color)
	for x in range(int(-size.x*2)+1,int(size.x*2),2):
		for side in [-1,1]:
			part(self,pos+Vector3(x*.25,size.y/2,side*(size.z/2+.03)),Vector3(.045,size.y-.15,.035),color.lightened(.16))
	part(self,pos+Vector3.UP*(size.y+.015),Vector3(size.x,.03,size.z),color.lightened(.08))

func planter(pos: Vector3) -> void:
	block(pos+Vector3.UP*.4,Vector3(2.4,.8,2.4),Color("4a555b"))
	part(self,pos+Vector3.UP*.81,Vector3(2.1,.03,2.1),Color("18231c"))
	var bush = MeshInstance3D.new()
	var sphere = SphereMesh.new()
	sphere.radius = 1.0
	sphere.height = 1.3
	bush.mesh = sphere
	bush.position = pos + Vector3.UP * 1.2
	bush.material_override = material(Color("334d3c"))
	add_child(bush)

func barrel(pos: Vector3) -> void:
	var body = block(pos+Vector3.UP*.65,Vector3(.8,1.3,.8),Color("34444a"))
	body.get_child(0).visible = false
	var cylinder = MeshInstance3D.new()
	var mesh = CylinderMesh.new()
	mesh.top_radius = .45
	mesh.bottom_radius = .45
	mesh.height = 1.3
	mesh.radial_segments = 16
	cylinder.mesh = mesh
	cylinder.material_override = material(Color("455860"))
	body.add_child(cylinder)
	part(body,Vector3(0,.05,.453),Vector3(.32,.28,.015),Color("d1a342"))

func text_sign(text: String, pos: Vector3, color: Color, font_size: int) -> void:
	var label = Label3D.new()
	label.text = text
	label.position = pos
	label.font_size = font_size
	label.pixel_size = .012
	label.modulate = color
	label.outline_size = 0
	add_child(label)

func lighting() -> void:
	var environment=WorldEnvironment.new()
	var env=Environment.new()
	env.background_mode=Environment.BG_SKY
	var sky=Sky.new()
	var sky_mat=ProceduralSkyMaterial.new()
	sky_mat.sky_top_color=[Color("07101c"),Color("09111b"),Color("49616b"),Color("5c5963"),Color("263a52")][stage]
	sky_mat.sky_horizon_color=[Color("243731"),Color("1b292d"),Color("748578"),Color("dcb681"),Color("9aaab3")][stage]
	sky_mat.ground_bottom_color=Color("152024")
	sky_mat.ground_horizon_color=sky_mat.sky_horizon_color
	sky.sky_material=sky_mat;env.sky=sky
	env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color=[Color("9eb3c9"),Color("d2c6ad"),Color("91ada1"),Color("e2c3a1"),Color("b1c4dd")][stage]
	env.ambient_light_energy=[.26,.42,.23,.25,.20][stage]
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	env.fog_enabled=true
	env.fog_light_color=sky_mat.sky_horizon_color
	env.fog_light_energy=.6
	env.ambient_light_sky_contribution=0.0
	env.fog_density=[.009,.003,.004,.004,.004][stage]
	environment.environment=env;add_child(environment)
	var sun=DirectionalLight3D.new()
	sun.rotation_degrees=Vector3([-40,-55,-48,-18,-35][stage],-32,0)
	sun.light_color=[Color("b4cce1"),Color("a8b7d0"),Color("e5e5cf"),Color("ffc589"),Color("b5cde7")][stage]
	sun.light_energy=[.25,.16,.65,.70,.20][stage]
	sun.shadow_enabled=true;sun.directional_shadow_max_distance=52;add_child(sun)

func make_rain() -> void:
	rain = GPUParticles3D.new()
	rain.amount = 400 if stage == 0 else 180
	rain.preprocess = 2.5
	rain.lifetime = 2.5 if stage == 0 else 12.0
	rain.visibility_aabb = AABB(Vector3(-30,-5,-25),Vector3(60,40,50))
	var process = ParticleProcessMaterial.new()
	process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	process.emission_box_extents = Vector3(27,1,24)
	process.direction = Vector3(-.08,-1,.03)
	process.initial_velocity_min = 11 if stage == 0 else .45
	process.initial_velocity_max = 15 if stage == 0 else 1.1
	process.gravity = Vector3(0,-2,0) if stage == 0 else Vector3(.1,-.05,.03)
	rain.process_material = process
	var mesh = BoxMesh.new()
	mesh.size = Vector3(.014,.3,.014) if stage == 0 else Vector3(.035,.025,.025)
	mesh.material = material(Color("667c8e") if stage == 0 else (Color("c6d4d9") if stage == 4 else Color("b8b189")))
	rain.draw_pass_1 = mesh
	rain.position.y = 13 if stage == 0 else 8
	add_child(rain)

func path_to(from: Vector3, to: Vector3) -> PackedVector3Array:
	var start = Vector2i(clampi(roundi(from.x),area.position.x,area.end.x-1),clampi(roundi(from.z),area.position.y,area.end.y-1))
	var finish = Vector2i(clampi(roundi(to.x),area.position.x,area.end.x-1),clampi(roundi(to.z),area.position.y,area.end.y-1))
	var points = PackedVector3Array()
	if grid.is_point_solid(start) or grid.is_point_solid(finish):
		return points
	for point in grid.get_point_path(start,finish):
		points.append(Vector3(point.x,0,point.y))
	return points
