extends RefCounted
# Stage-one geometry is instanced by material; physics uses simple separate bodies.
var w: NRWorld
var groups: Dictionary = {}
var mats: Dictionary = {}
var rng = RandomNumberGenerator.new()
func mat(name: String, color: Color, rough: float=.7, metal: float=0.0, glow: float=0.0) -> Material:
	if mats.has(name): return mats[name]
	var m = StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = rough
	m.metallic = metal
	if glow > 0:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = glow
	mats[name] = m
	return m
func masonry(name: String, color: Color, bricks: bool=true) -> Material:
	if mats.has(name): return mats[name]
	var asset="brick_wall_001" if bricks else ("concrete_pavement_03" if name=="walk" else "concrete_wall_006")
	var tint=color.lightened(.55)
	var m=load("res://scripts/materials.gd").scanned(asset,tint,2.2 if bricks else 2.5,1.0,0.0,.12)
	mats[name]=m
	return m

# Batching zones follow the level's rooms: the main hall in two halves (so each half
# gets its own 8 nearest lamps), then each deeper room and side room separately.
static func cell(p: Vector3) -> String:
	if p.z > -22.5: return "h0" if p.z > 0 else "h1"
	var depth = 1 + floori((-22.5 - p.z) / 24.0)
	return "r%d%s" % [depth, "e" if p.x > 16.2 else ""]

func box(p: Vector3, s: Vector3, m: Material, rotation: Vector3=Vector3.ZERO) -> void:
	var key = str(m.get_instance_id())+":"+cell(p)  # per material, per room (≤8 lights per mesh on phones)
	if not groups.has(key): groups[key] = {"material":m,"transforms":[]}
	groups[key].transforms.append(Transform3D(Basis.from_euler(rotation).scaled_local(s),p))
func solid(p: Vector3, s: Vector3, m: Material, nav: bool=true) -> void:
	box(p,s,m)
	var body = StaticBody3D.new()
	body.position=p
	body.collision_layer=1
	var c = CollisionShape3D.new()
	var shape = BoxShape3D.new()
	shape.size=s
	c.shape=shape
	body.add_child(c)
	w.add_child(body)
	# Large walls hide whatever is behind them (occlusion culling).
	if s.y >= 2.5 and maxf(s.x,s.z) >= 4.0 and minf(s.x,s.z) >= .25:
		var occ=OccluderInstance3D.new(); var occ_shape=BoxOccluder3D.new(); occ_shape.size=s*.98
		occ.occluder=occ_shape; body.add_child(occ)
	if nav: w.obstacles.append(Rect2(Vector2(p.x-s.x/2-.45,p.z-s.z/2-.45),Vector2(s.x+.9,s.z+.9)))
func beam(a: Vector3,b: Vector3,width: float,m: Material) -> void:
	var key = str(m.get_instance_id())+":beam:"+cell((a+b)*.5)
	if not groups.has(key): groups[key] = {"material":m,"transforms":[]}
	var basis = Basis(Quaternion(Vector3.UP,(b-a).normalized())).scaled_local(Vector3(width,a.distance_to(b),width))
	groups[key].transforms.append(Transform3D(basis,(a+b)*.5))
func lamp(p: Vector3,c: Color,energy: float,radius: float,shadows: bool=false) -> void:
	var light = OmniLight3D.new()
	light.position=p
	light.light_color=c
	light.light_energy=energy
	light.omni_range=radius
	light.omni_attenuation=1.3
	light.shadow_enabled=shadows
	w.add_child(light)
func sign_text(t: String,p: Vector3,size: int,c: Color,rot: float=0) -> void:
	var label=Label3D.new()
	label.text=t
	label.position=p
	label.rotation.y=rot
	label.font_size=size
	label.pixel_size=.009
	label.modulate=c
	label.outline_size=0
	w.add_child(label)
func build(world: NRWorld) -> void:
	w=world
	rng.seed=824
	var steel=mat("iron",Color("1a282a"),.39,.72)
	var trim=mat("stone",Color("494a43"))
	var curb=mat("curb",Color("77796c"))
	var black=mat("rubber",Color("111719"),.94)
	var gold=mat("sodium",Color("ffd493"),.3,0,1.8)
	var cyan=mat("cyan",Color("63b4ab"),.3,0,1.1)
	var road=ShaderMaterial.new()
	road.shader=load("res://assets/shaders/wet_road.gdshader")
	road.set_shader_parameter("asphalt",load("res://assets/textures/asphalt_color.jpg"))
	road.set_shader_parameter("normal_tex",load("res://assets/textures/asphalt_normal.jpg"))
	road.set_shader_parameter("rough_tex",load("res://assets/textures/asphalt_roughness.jpg"))
	for x in range(-20,24,8):
		for z in range(-20,24,8): solid(Vector3(x,-.3,z),Vector3(8,.6,8),road,false)
	for side in [-1,1]:
		solid(Vector3(side*15.5,.08,0),Vector3(5,.16,44),masonry("walk",Color("434840"),false),false)
		for z in range(-22,23,2):
			box(Vector3(side*13,.12,z),Vector3(.22,.25,1.97),curb)
		for i in range(6):
			building(side, -23.0+i*9.0, i)
	# Lane paint, drainage channels and crosswalk wear.
	var paint=mat("paint",Color("928669"),.8)
	for z in range(-21,22,4):
		for x in [-.13,.13]: box(Vector3(x,.012,z),Vector3(.085,.016,2.4),paint)
	for x in range(-11,12,2): box(Vector3(x,.015,17),Vector3(.65,.02,2.6),mat("crossing",Color("85897f")))
	for x in [-12.5,12.5]:
		for z in [-15,0,14]:
			box(Vector3(x,.02,z),Vector3(.8,.035,1.3),black)
			for k in range(8): box(Vector3(x-.35+k*.1,.045,z),Vector3(.027,.02,1.2),steel)
	# Elevated railway: open trusses, riveted piers, ties and cross-bracing.
	for x in [-6.3,6.3]:
		box(Vector3(x,7.8,0),Vector3(.25,1.05,52),steel)
		for z in [-18,-5,8,21]:
			solid(Vector3(x,3.8,z),Vector3(.52,7.6,.58),steel)
			box(Vector3(x,.18,z),Vector3(1.0,.36,1.1),trim)
			for y in [1.0,3.0,5.0,7.0]: box(Vector3(x,y,z),Vector3(.65,.11,.71),steel)
			for dz in [-2.5,2.5]: beam(Vector3(x,5.1,z),Vector3(x,7.6,z+dz),.18,steel)
		for z in range(-24,25,3):
			beam(Vector3(x,7.35,z),Vector3(x,8.28,z+3),.11,steel)
			beam(Vector3(x,8.28,z),Vector3(x,7.35,z+3),.11,steel)
	for z in range(-24,25,2): box(Vector3(0,8.4,z),Vector3(13,.19,.26),steel)
	for x in [-3.7,-2.2,2.2,3.7]: box(Vector3(x,8.64,0),Vector3(.12,.16,53),steel)
	for z in [-16,-2,12]:
		box(Vector3(0,7.25,z),Vector3(12.8,.4,.4),steel)
		box(Vector3(0,7.0,z),Vector3(1.4,.08,.35),gold)
		lamp(Vector3(0,6.7,z),Color("ffc589"),3.4,13,z==-2)
	# Parked vehicles provide grounded street cover; center firing lane stays clear.
	car(Vector3(-10,0,-7),Color("3c4b49"),true)
	car(Vector3(10,0,6),Color("514239"),false)
	car(Vector3(-10,0,16),Color("242f35"),false)
	for x in [-11,11]:
		for z in [-18,-2,14]:
			box(Vector3(x,2.9,z),Vector3(.10,5.8,.10),steel)
			box(Vector3(x- signf(x)*.6,5.7,z),Vector3(1.3,.12,.3),steel)
			box(Vector3(x-signf(x)*1.1,5.62,z),Vector3(.42,.055,.25),gold)
			lamp(Vector3(x-signf(x),5.3,z),Color("ffba73"),3.2,10)
	# Projecting shop signs are readable down the street, with colored spill.
	for spec in [Vector3(-15,4.7,9),Vector3(15,5.0,-7),Vector3(-15,5.0,-16)]:
		var red=mat("neon red",Color("d33d23"),.4,0,1.0)
		box(spec,Vector3(1.15,2.6,.25),steel)
		box(spec+Vector3(0,0,.14),Vector3(1.03,2.45,.035),red)
		sign_text("H\nO\nT\nE\nL" if spec.x<0 else "B\nA\nR",spec+Vector3(0,0,.18),42,Color("ffe1a1"))
		beam(spec+Vector3(0,1.25,0),Vector3(signf(spec.x)*18,spec.y+1.25,spec.z),.08,steel)
		lamp(spec+Vector3(0,-1,1),Color("f36c3d"),1.6,6)
	# Barricades and loose street detail.
	for x in [-4,4]:
		solid(Vector3(x,.48,-20),Vector3(3.5,.95,.7),masonry("barrier",Color("5a5b50"),false))
		for off in [-1.2,-.4,.4,1.2]: box(Vector3(x+off,.57,-19.63),Vector3(.32,.60,.025),paint,Vector3(0,0,-.35))
	for side in [-1,1]:
		for z in [-12,2,15]:
			solid(Vector3(side*14,.5,z),Vector3(.8,1,.8),steel)
			box(Vector3(side*14,1.04,z),Vector3(.95,.10,.95),black)
			for k in range(5): box(Vector3(side*14-.4+k*.2,.5,z+.41),Vector3(.035,.85,.02),trim)
		for z in range(-19,22,5):
			box(Vector3(side*13.9,.46,z),Vector3(.12,.92,.12),steel)
			box(Vector3(side*13.9,.82,z),Vector3(.14,.06,.14),gold)
	for i in range(45):
		var p=Vector3(rng.randf_range(-12,12),.025,rng.randf_range(-21,21))
		box(p,Vector3(.14,.008,.21),mat("litter",Color("7e8270")),Vector3(0,rng.randf()*TAU,0))
	# Close the arena with a distant security gate, preserving the original bounds.
	solid(Vector3(0,1,-22),Vector3(48,2,.3),steel,false)
	box(Vector3(0,4.2,-22),Vector3(15,.8,.3),black)
	sign_text("NORTHLINE  /  TRANSIT AUTHORITY",Vector3(0,4.2,-21.8),51,Color("cabfa2"))
	solid(Vector3(0,1,22),Vector3(48,2,.3),steel,false)
	var terminal=masonry("terminal",Color("3e4943"))
	box(Vector3(0,9,-27),Vector3(39,18,8),terminal)
	for y in [6,10,14]:
		box(Vector3(0,y-1.3,-22.9),Vector3(39,.23,.5),trim)
		for x in range(-17,18,3):
			box(Vector3(x,y,-22.9),Vector3(1.7,2.1,.12),black)
			box(Vector3(x,y,-22.8),Vector3(1.42,1.86,.03),mat("distant window",Color("a49772"),.3,0,.4))
	box(Vector3(0,9,-22.7),Vector3(11,1.2,.2),steel)
	sign_text("N O R T H L I N E",Vector3(0,9,-22.5),90,Color("d7ba7b"))
	finish()
	var probe=ReflectionProbe.new()
	probe.position=Vector3(0,3,0)
	probe.size=Vector3(46,20,48)
	probe.box_projection=true
	probe.intensity=.8
	probe.max_distance=75
	probe.update_mode=ReflectionProbe.UPDATE_ONCE
	w.add_child(probe)
func building(side: int,z: float,index: int) -> void:
	var x=side*22.0
	var h=14.0+float((index*7)%4)*3.0
	var color=[Color("524237"),Color("393f3b"),Color("4e4540"),Color("353d3d")][index%4]
	var wall=masonry("brick"+str(index%4),color)
	var trim=mat("stone",Color("494a43"))
	var frame=mat("frames",Color("171f1d"),.43,.5)
	var glass=mat("glass",Color("15292c"),.16,.5)
	var lit=mat("window"+str(index%3),[Color("9c8960"),Color("597c79"),Color("b59a6e")][index%3],.35,.1,.35)
	solid(Vector3(x,h/2,z),Vector3(8,h,8.85),wall)
	var front=side*17.96
	for y in [3.7,7.0,10.3,13.6,16.9,20.2]:
		if y>h: continue
		box(Vector3(front,y,z),Vector3(.33,.15,8.95),trim)
		if y+2.5>h: continue
		for dz in [-2.8,0,2.8]:
			box(Vector3(front-side*.10,y+1.35,z+dz),Vector3(.18,2.3,1.7),frame)
			box(Vector3(front-side*.21,y+1.35,z+dz),Vector3(.025,1.94,1.4),lit if (index+int(y)+int(dz))%3==0 else glass)
			box(Vector3(front-side*.24,y+1.35,z+dz),Vector3(.06,.07,1.5),frame)
			box(Vector3(front-side*.24,y+1.35,z+dz),Vector3(.06,2,.07),frame)
			box(Vector3(front-side*.34,y+.24,z+dz),Vector3(.65,.15,1.95),trim)
	# Ground floor has recessed shop windows, doors, awnings and lit lettering.
	for dz in [-2.6,2.6]:
		box(Vector3(front-side*.08,1.65,z+dz),Vector3(.12,2.75,2.5),frame)
		box(Vector3(front-side*.16,1.7,z+dz),Vector3(.025,2.4,2.2),glass)
		for off in [-.8,0,.8]: box(Vector3(front-side*.20,1.7,z+dz+off),Vector3(.04,2.4,.05),trim)
	box(Vector3(front-side*.16,1.4,z),Vector3(.06,2.7,1.2),frame)
	box(Vector3(front-side*.21,1.65,z),Vector3(.03,1.7,.94),glass)
	box(Vector3(front-side*.34,3.4,z),Vector3(.65,.58,8.3),frame)
	var tint=Color("cdb18a") if side<0 else Color("81b5a9")
	var names=["NORTHLINE HOTEL","AFTER HOURS","KOWLOON KITCHEN","RADIO / REPAIR","MIDNIGHT MARKET","EASTERN BANK"]
	sign_text(names[(index+(0 if side<0 else 2))%6],Vector3(front-side*.69,3.43,z),42,tint,PI*.5 if side<0 else -PI*.5)
	var awning=mat("awning"+str(index%2),Color("25423b") if index%2==0 else Color("583b32"))
	box(Vector3(front-side*.9,2.95,z),Vector3(1.5,.10,8.4),awning,Vector3(0,0,side*.10))
	box(Vector3(front-side*1.6,2.8,z),Vector3(.06,.25,8.4),awning)
	if index%2==0: lamp(Vector3(front-side*1.4,2.5,z),tint,2.5,7)
	# Cornices, external pipework and a fire escape on alternating facades.
	box(Vector3(front,h-.1,z),Vector3(.7,.35,9.0),trim)
	box(Vector3(front-side*.18,h*.5,z+4),Vector3(.12,h,.12),frame)
	if index%2==0:
		for y in [6.8,10.1]:
			box(Vector3(front-side*.8,y,z),Vector3(1.6,.12,5.8),frame)
			box(Vector3(front-side*1.6,y+.95,z),Vector3(.06,.06,5.8),frame)
			for dz in range(-3,4): box(Vector3(front-side*1.6,y+.5,z+dz*.9),Vector3(.045,1,.045),frame)
			for k in range(13): box(Vector3(front-side*.8,y+k*.25,z-2.6+k*.4),Vector3(1,.075,.3),frame)
		box(Vector3(front-side*.45,4.8,z+3),Vector3(.9,.8,1.2),trim)
func car(p: Vector3,color: Color,van: bool) -> void:
	var paint=mat("car"+color.to_html(),color,.24,.65)
	var tire=mat("rubber",Color("111719"),.94)
	var window=mat("car glass",Color("142326"),.12,.6)
	var metal=mat("chrome",Color("727b79"),.24,.8)
	var length=5.3 if van else 4.5
	solid(p+Vector3(0,.65,0),Vector3(2.1,1.15,length),paint)
	box(p+Vector3(0,1.4,.1),Vector3(1.95,.8,3.9 if van else 2.4),paint)
	box(p+Vector3(0,1.48,-1.9 if van else -1.17),Vector3(1.7,.59,.04),window,Vector3(-.16,0,0))
	if not van: box(p+Vector3(0,1.48,1.25),Vector3(1.7,.55,.04),window,Vector3(.22,0,0))
	for side in [-1,1]:
		box(p+Vector3(side*.987,1.46,-.3),Vector3(.028,.57,1.5),window)
		box(p+Vector3(side*1.02,1.0,0),Vector3(.035,.04,.28),metal)
		box(p+Vector3(side*1.16,1.3,-.9),Vector3(.28,.15,.20),paint)
		for z in [-1.55,1.55]:
			var wheel=MeshInstance3D.new()
			var c=CylinderMesh.new()
			c.top_radius=.43;c.bottom_radius=.43;c.height=.24;c.radial_segments=16
			wheel.mesh=c;wheel.material_override=tire
			wheel.rotation.z=PI*.5;wheel.position=p+Vector3(side*1.05,.43,z)
			w.add_child(wheel)
			box(p+Vector3(side*1.18,.43,z),Vector3(.03,.39,.39),metal)
		box(p+Vector3(side*.7,.78,-length/2-.02),Vector3(.47,.22,.06),mat("headlight",Color("c9c3a4"),.2,0,.5))
		box(p+Vector3(side*.78,.82,length/2+.02),Vector3(.27,.25,.06),mat("tail",Color("a52419"),.2,0,.6))
	box(p+Vector3(0,.36,-length/2),Vector3(2.2,.20,.2),tire)
	box(p+Vector3(0,.65,length/2+.05),Vector3(.52,.18,.025),metal)
func finish() -> void:
	for entry in groups.values():
		var instance=MultiMeshInstance3D.new()
		var mm=MultiMesh.new()
		mm.transform_format=MultiMesh.TRANSFORM_3D
		var mesh=BoxMesh.new()
		mesh.size=Vector3.ONE
		mesh.material=entry.material
		mm.mesh=mesh
		mm.instance_count=entry.transforms.size()
		var largest=0.0
		for i in range(entry.transforms.size()):
			mm.set_instance_transform(i,entry.transforms[i])
			var b: Basis=entry.transforms[i].basis
			largest=maxf(largest,maxf(b.x.length(),maxf(b.y.length(),b.z.length())))
		instance.multimesh=mm
		# Thin trim (paint, rails, frames) adds shadow draw calls without visible shadows.
		if largest < .4: instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		w.add_child(instance)
