extends "res://scripts/urban.gd"
var custom: Dictionary = {}
func surface(name: String,c: Color,style: int) -> Material:
	if mats.has(name): return mats[name]
	var library=load("res://scripts/materials.gd")
	var m: Material
	match style:
		0:m=library.scanned("marble_01",c.lightened(.2),3.0,.42)
		1:m=library.scanned("forest_ground_04",Color(.77,.81,.70),3.2)
		2:m=library.scanned("rusty_metal_02",c.lightened(.5),2.0,.9,.35)
		3:m=library.scanned("rock_boulder_dry" if name.contains("stone") else "concrete_wall_006",c.lightened(.25),2.5)
		5:m=library.scanned("forest_ground_04",Color(.87,.73,.55),4.0)
		_:
			m=ShaderMaterial.new();m.shader=load("res://assets/shaders/surface.gdshader");m.set_shader_parameter("tint",c);m.set_shader_parameter("style",style)
	mats[name]=m
	return m

func instance_mesh(key: String,mesh: Mesh,m: Material,p: Vector3,s: Vector3,rotation: Vector3=Vector3.ZERO) -> void:
	key += ":"+cell(p)
	if not custom.has(key): custom[key]={"mesh":mesh,"material":m,"transforms":[]}
	custom[key].transforms.append(Transform3D(Basis.from_euler(rotation).scaled_local(s),p))
func cylinder(p: Vector3,r: float,h: float,m: Material,rotation: Vector3=Vector3.ZERO) -> void:
	var mesh=CylinderMesh.new();mesh.top_radius=.5;mesh.bottom_radius=.5;mesh.height=1;mesh.radial_segments=6 if w.stage==2 else 12
	instance_mesh("cylinder"+str(m.get_instance_id()),mesh,m,p,Vector3(r*2,h,r*2),rotation)
func rock(p: Vector3,s: Vector3,m: Material) -> void:
	var mesh=SphereMesh.new();mesh.radius=.5;mesh.height=1;mesh.radial_segments=9;mesh.rings=5
	instance_mesh("rock"+str(m.get_instance_id()),mesh,m,p,s,Vector3(.15,rng.randf()*TAU,.12))
func ring(p: Vector3,r: float,thick: float,m: Material) -> void:
	var mesh=TorusMesh.new();mesh.inner_radius=r-thick;mesh.outer_radius=r;mesh.rings=32;mesh.ring_segments=6
	instance_mesh("ring"+str(r)+str(m.get_instance_id()),mesh,m,p,Vector3.ONE)
func water(p: Vector3,s: Vector3,c: Color) -> void:
	var m=ShaderMaterial.new();m.shader=load("res://assets/shaders/water.gdshader");m.set_shader_parameter("tint",c)
	box(p,s,m)
func finish_all() -> void:
	finish()
	for key in custom:
		var entry=custom[key]
		var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D
		mm.mesh=entry.mesh
		mm.instance_count=entry.transforms.size()
		for i in range(mm.instance_count): mm.set_instance_transform(i,entry.transforms[i])
		var node=MultiMeshInstance3D.new();node.multimesh=mm;node.material_override=entry.material
		if key.begins_with("noshadow"):
			node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;node.visibility_range_end=45 if key.begins_with("noshadow grass") else 60
		elif key.begins_with("ferns"):
			node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;node.visibility_range_end=30
		elif key.begins_with("bamboo leaves"):node.visibility_range_end=48
		w.add_child(node)
func reflection(p: Vector3,size: Vector3) -> void:
	var probe=ReflectionProbe.new();probe.position=p;probe.size=size;probe.box_projection=true;probe.intensity=.7;probe.max_distance=75
	w.add_child(probe)
func text(t: String,p: Vector3,c: Color=Color("e6d3a1"),size: int=50) -> void:
	sign_text(t,p,size,c)
func bounds(m: Material,h: float=3.0,back_gaps: Array=[]) -> void:
	if not back_gaps.is_empty():
		for x in [-24,24]: solid(Vector3(x,h*.5,0),Vector3(.6,h,45),m,false)
		solid(Vector3(0,h*.5,22),Vector3(48,h,.6),m,false)
		wall_run(-24,24,-22,true,h,m,back_gaps)
		return
	for x in [-24,24]: solid(Vector3(x,h*.5,0),Vector3(.6,h,45),m,false)
	for z in [-22,22]: solid(Vector3(0,h*.5,z),Vector3(48,h,.6),m,false)
func build_set(world: NRWorld,index: int) -> void:
	w=world;rng.seed=410+index
	match index:
		1: palace()
		2: bamboo(); bamboo_grounds()
		3: refinery()
		4: cathedral(); cathedral_depths()
	finish_all()
func palace() -> void:
	var marble=surface("ivory marble",Color("c8bc9e"),0)
	var dark=surface("green marble",Color("203b35"),0)
	var brass=mat("brass",Color("b49c5f"),.24,.8)
	var wood=mat("walnut",Color("30201b"),.48)
	var velvet=mat("velvet",Color("5d1e24"),.94)
	var light=mat("warm glass",Color("ffe1a6"),.2,0,1.2)
	for x in range(-20,24,8):
		for z in range(-18,23,8): solid(Vector3(x,-.3,z),Vector3(8,.6,8),marble,false)
	bounds(dark,11)
	box(Vector3(0,11,0),Vector3(49,.4,45),wood)
	for x in [-20,-12,-4,4,12,20]:
		box(Vector3(x,10.65,0),Vector3(.16,.16,44),brass)
	for z in range(-20,23,7): box(Vector3(0,10.65,z),Vector3(48,.16,.16),brass)
	# Burgundy runner leads from the reception to the secured inner lounge.
	box(Vector3(0,.015,0),Vector3(5,.025,39),velvet)
	for x in [-2.48,2.48]: box(Vector3(x,.034,0),Vector3(.06,.015,39),brass)
	for x in [-10,10]:
		for z in [-14,-2,10]:
			solid(Vector3(x,4.7,z),Vector3(1.4,9.4,1.4),dark)
			for y in [.25,1,8.8,9.3]: box(Vector3(x,y,z),Vector3(1.8,.18,1.8),brass)
			for side in [-1,1]: box(Vector3(x+side*.70,4.8,z+.72),Vector3(.055,8,.035),brass)
			for dz in [-.72,.72]: box(Vector3(x,4.8,z+dz),Vector3(1.35,.05,.035),brass)
	# Mezzanines, balustrades and wall panelling.
	for side in [-1,1]:
		box(Vector3(side*19,5.8,0),Vector3(9,.35,44),marble)
		for z in range(-20,22,2):
			box(Vector3(side*14.6,6.4,z),Vector3(.08,1.05,.08),brass)
			box(Vector3(side*23.55,3,z),Vector3(.15,5.4,.055),brass)
		box(Vector3(side*14.6,6.98,0),Vector3(.11,.12,44),brass)
		for z in [-16,-6,5,16]:
			box(Vector3(side*23.5,3,z),Vector3(.2,3.3,5.0),wood)
			box(Vector3(side*23.32,3,z),Vector3(.1,2.9,4.6),mat("painting",Color("55645a")))
			for dy in [-1.65,1.65]: box(Vector3(side*23.1,3+dy,z),Vector3(.14,.12,5.1),brass)
			cylinder(Vector3(side*22.8,4.4,z),.20,.7,light)
			lamp(Vector3(side*22,4,z),Color("ffd39c"),2.0,7)
	# Aquarium displays flank the mid-hall; framing makes the glass readable.
	for side in [-1,1]:
		solid(Vector3(side*17,1.5,-3),Vector3(3,3,8),dark)
		box(Vector3(side*15.43,1.8,-3),Vector3(.04,2.1,7.2),mat("aquarium",Color("124549"),.12,.4,.18))
		for z in [-6,-3,0]:
			for y in [.9,1.5,2.3]:
				rock(Vector3(side*15.35,y,z),Vector3(.04,.12,.34),mat("fish",Color("8bc3ad"),.3,0,.25))
		lamp(Vector3(side*14.9,2,-3),Color("65b9be"),2,7)
	# Reception, upholstered sofas, coffee tables and potted palms.
	for x in [-6,6]:
		solid(Vector3(x,.75,-17),Vector3(6,1.5,1.8),wood)
		box(Vector3(x,1.55,-17),Vector3(6.25,.13,2),marble)
		for dx in [-2,-1,0,1,2]: box(Vector3(x+dx,.7,-15.98),Vector3(.05,1.25,.03),brass)
	for x in [-17,17]:
		for z in [8,-12]:
			solid(Vector3(x,.45,z),Vector3(4,.9,1.5),velvet)
			box(Vector3(x,.9,z+.65),Vector3(4,1.05,.35),velvet)
			for dx in [-1.8,1.8]: box(Vector3(x+dx,.72,z),Vector3(.35,.55,1.5),velvet)
			solid(Vector3(x,.35,z-2),Vector3(3,.7,1.2),wood)
			box(Vector3(x,.73,z-2),Vector3(3.1,.08,1.3),marble)
	for z in [-11,4,15]:
		beam(Vector3(0,10.8,z),Vector3(0,8.1,z),.045,brass)
		for r in [1.3,2.1]:
			ring(Vector3(0,8.0,z),r,.08,brass)
			for j in range(16):
				var a=TAU*j/16
				cylinder(Vector3(sin(a)*r,7.65,z+cos(a)*r),.055,.65,light)
		lamp(Vector3(0,7.5,z),Color("ffe0b0"),2.6,14,z==4)
	text("T H E   G L A S S   P A L A C E",Vector3(0,4.8,-21.6),Color("d7bc76"),80)
	text("PRIVATE  /  MEMBERS LOUNGE",Vector3(0,3.4,-21.5),Color("aaad98"),35)
	reflection(Vector3(0,3,0),Vector3(47,15,45))
func leaf_mesh() -> ArrayMesh:
	var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for branch in range(4):
		var angle=TAU*float(branch)/4.0+.24
		var forward=Vector3(sin(angle),.08,cos(angle))
		var cross_dir=Vector3(forward.z,0,-forward.x)
		for i in range(1,7):
			for side in [-1,1]:
				var base=forward*(float(i)*.16)
				var tip=base+forward*.18+cross_dir*float(side)*(.38-float(i)*.025)+Vector3(0,-.04,0)
				var middle=base.lerp(tip,.5)+Vector3(0,.035,0)
				var width=forward*.035
				var points=[base,middle+width,tip,base,tip,middle-width]
				var uvs=[Vector2(.5,0),Vector2(1,.5),Vector2(.5,1),Vector2(.5,0),Vector2(.5,1),Vector2(0,.5)]
				for k in range(6):st.set_uv(uvs[k]);st.add_vertex(points[k])
	st.generate_normals();return st.commit()
func foliage_material(name: String,c: Color) -> Material:
	if mats.has(name):return mats[name]
	var m=ShaderMaterial.new();m.shader=load("res://assets/shaders/leaves.gdshader");m.set_shader_parameter("tint",c);mats[name]=m;return m
func bamboo() -> void:
	var dirt=surface("forest floor",Color("3d4b24"),1)
	var stone=surface("moss stone",Color("5c6651"),3)
	var stalk=mat("bamboo stalk",Color("526a2d"),.7)
	var nodes=mat("bamboo nodes",Color("778747"),.85)
	var wood=mat("shrine red",Color("672d21"),.7)
	var roof=mat("roof",Color("26312d"),.48)
	var leaves=leaf_mesh()
	var foliage=foliage_material("bamboo foliage",Color("3f642b"))
	solid(Vector3(0,-.3,0),Vector3(49,.6,46),dirt,false)
	bounds(stone,1.8,[[0,6,1.8]])
	# A dense instanced grove leaves the central path and combat clearings navigable.
	for i in range(180):
		var x=rng.randf_range(8,30)*(1 if i%2==0 else -1)
		var z=rng.randf_range(-27,25)
		var h=rng.randf_range(7,13)
		cylinder(Vector3(x,h/2,z),.09,h,stalk,Vector3(0,0,rng.randf_range(-.08,.08)))
		for y in range(1,int(h)): cylinder(Vector3(x,y,z),.106,.045,nodes)
		for j in range(5):
			instance_mesh("bamboo leaves",leaves,foliage,Vector3(x,h-j*1.2,z),Vector3(2.4,1.4,2.4),Vector3(.1,rng.randf()*TAU,.2))
	for i in range(110):
		var p=Vector3(rng.randf_range(-22,22),.13,rng.randf_range(-21,21))
		if abs(p.x)>5:
			instance_mesh("ferns",leaves,foliage,p,Vector3(.8,.8,.8),Vector3(.12,rng.randf()*TAU,0))
	for side in [-1,1]:
		for z in [-15,-5,6,17]:
			var x=side*(7+abs(z)%3)
			solid(Vector3(x,.65,z),Vector3(2,1.3,2),stone)
			rock(Vector3(x,.95,z),Vector3(3,2.0,2.5),stone)
			rock(Vector3(x+.5,1.6,z),Vector3(2,.3,1.5),mat("moss",Color("425d2e")))
	# Stepping stones, lanterns and the shallow side stream.
	for z in range(-17,19,2):
		rock(Vector3(sin(z*.25)*1.4,.02,z),Vector3(2.6,.09,1.7),stone)
	water(Vector3(15,.03,0),Vector3(6,.04,37),Color("254c40"))
	for z in range(-18,21,3):
		for x in [11,19]:rock(Vector3(x,.25,z),Vector3(2.1,.7,2),stone)
	for z in [-12,0,12]:
		for x in [-4,4]:
			cylinder(Vector3(x,.5,z),.22,1,stone)
			box(Vector3(x,1.2,z),Vector3(.7,.65,.7),wood)
			box(Vector3(x,1.2,z+.36),Vector3(.45,.4,.035),mat("lantern",Color("e8bd7b"),.3,0,1.4))
			box(Vector3(x,1.59,z),Vector3(.94,.18,.94),roof)
			lamp(Vector3(x,1.3,z+.5),Color("f7bb6e"),1.0,4)
	# Successive shrine gates and a raised ceremonial backdrop.
	for z in [8,-6,-18]:
		for x in [-5.5,5.5]:
			solid(Vector3(x,3.3,z),Vector3(.48,6.6,.5),wood)
			box(Vector3(x,.4,z),Vector3(.8,.8,.8),stone)
		box(Vector3(0,5.5,z),Vector3(12,.38,.45),wood)
		box(Vector3(0,6.5,z),Vector3(13,.45,.9),roof)
		for x in [-6.2,6.2]:box(Vector3(x,6.68,z),Vector3(1.6,.3,.9),roof,Vector3(0,0,signf(x)*.18))
		beam(Vector3(-5,5.5,z+.3),Vector3(5,5.5,z+.3),.055,mat("rope",Color("a49065")))
		for x in [-3,-1,1,3]:box(Vector3(x,5.22,z+.35),Vector3(.15,.45,.025),mat("paper",Color("d6d0b3")),Vector3(0,0,.2))
	text("H O L L O W   B A M B O O",Vector3(0,5.35,-23.2),Color("d5cbab"),48)
	reflection(Vector3(10,3,0),Vector3(28,20,45))
func refinery() -> void:
	var sand=surface("sand",Color("8a6b43"),5)
	var iron=surface("rust",Color("5d6255"),2)
	var steel=mat("steel",Color("323c3c"),.45,.7)
	var hazard=mat("warning yellow",Color("ba913f"),.6)
	var black=mat("warning black",Color("242927"))
	var concrete=surface("concrete",Color("6b6452"),3)
	var fire=mat("furnace glow",Color("ff6222"),.4,0,2.0)
	solid(Vector3(0,-.3,0),Vector3(49,.6,46),sand,false)
	bounds(concrete,1.8)
	for side in [-1,1]:
		for z in [-15,0,15]:
			var x=side*18
			solid(Vector3(x,3.1,z),Vector3(5.6,6.2,5.6),iron)
			cylinder(Vector3(x,6.5,z),2.8,1,iron)
			for y in [.2,3,6.2]:ring(Vector3(x,y,z),2.9,.1,steel)
			for k in range(12):box(Vector3(x-side*2.9,.6+k*.5,z),Vector3(.1,.045,.65),hazard)
			for dz in [-.4,.4]:box(Vector3(x-side*2.9,3.2,z+dz),Vector3(.10,6.4,.08),steel)
			text("0"+str(abs(z)/5+1)+" / PRESSURE",Vector3(x,4.6,z+2.83),Color("d6c69b"),35)
		for y in [1.8,2.5]:cylinder(Vector3(side*13.6,y,0),.25,43,iron,Vector3(PI*.5,0,0))
		for z in range(-20,23,6):
			box(Vector3(side*13.6,1.2,z),Vector3(1,.2,.7),steel)
			box(Vector3(side*13.6,.6,z),Vector3(.2,1.2,.2),steel)
	# Two pipe bridges with open mesh walkways and safety rails.
	for z in [-9,10]:
		for x in [-11,11]:solid(Vector3(x,3.5,z),Vector3(.4,7,.5),steel)
		box(Vector3(0,6.9,z),Vector3(23,.25,2),steel)
		for x in range(-11,12):
			box(Vector3(x,7.5,z+.95),Vector3(.05,1.1,.05),hazard)
			box(Vector3(x,7.5,z-.95),Vector3(.05,1.1,.05),hazard)
		for dz in [-.95,.95]:box(Vector3(0,8.1,z+dz),Vector3(23,.06,.06),hazard)
		for dz in [-.5,.5]:cylinder(Vector3(0,6.35,z+dz),.22,24,iron,Vector3(0,0,PI*.5))
	for x in [-7,7]:
		for z in [-4,14]:
			solid(Vector3(x,.65,z),Vector3(3,1.3,1.4),concrete)
			for off in [-1,-.3,.4,1.1]:box(Vector3(x+off,.7,z+.715),Vector3(.3,1,.02),hazard,Vector3(0,0,.3))
	for p in [Vector3(-6,0,-15),Vector3(8,0,3),Vector3(-9,0,5)]:
		for dx in [-.6,.6]:
			cylinder(p+Vector3(dx,.65,0),.44,1.3,iron)
			for y in [.15,1.1]:ring(p+Vector3(dx,y,0),.46,.025,steel)
	# Furnace portal and smokestacks provide a strong distant silhouette.
	box(Vector3(0,5,-25),Vector3(18,10,5),iron)
	box(Vector3(0,3,-22.35),Vector3(8,5,.12),black)
	box(Vector3(0,2.6,-22.25),Vector3(6,3.8,.05),fire)
	for x in range(-3,4):box(Vector3(x,2.6,-22.15),Vector3(.15,4,.12),steel)
	lamp(Vector3(0,3,-20),Color("ff7638"),5,12,true)
	for x in [-9,9,20]:
		cylinder(Vector3(x,12,-28),1.4,24,iron)
		for y in [5,10,15,20]:ring(Vector3(x,y,-28),1.5,.08,hazard)
	text("A S H W O R K S",Vector3(0,8,-22.3),Color("d9bc75"),85)
	for x in [-22,22]:
		for z in [-12,8]:
			box(Vector3(x,6,z),Vector3(.13,12,.13),steel)
			box(Vector3(x,11.6,z),Vector3(1,.4,.3),mat("floodlight",Color("ffdeb0"),.3,0,1.5))
			lamp(Vector3(x,10.8,z),Color("ffd094"),2,13)
	for i in range(22):
		var p=Vector3(rng.randf_range(-28,28),.25,rng.randf_range(-28,24))
		if abs(p.x)>20:rock(p,Vector3(2.5,1,2),sand)
func arch(p: Vector3,width: float,height: float,m: Material) -> void:
	var half=width*.5
	for side in [-1,1]:
		box(p+Vector3(side*half,height*.3,0),Vector3(.45,height*.6,.65),m)
		for j in range(8):
			var t=float(j)/8
			var t2=float(j+1)/8
			var a=Vector3(side*half*(1.0-t),height*.6+height*.4*sin(t*PI*.5),0)
			var b=Vector3(side*half*(1.0-t2),height*.6+height*.4*sin(t2*PI*.5),0)
			beam(p+a,p+b,.46,m)
func cathedral() -> void:
	var stone=surface("cathedral stone",Color("4d535b"),3)
	var trim=surface("cut stone",Color("717780"),3)
	var snow=surface("snow",Color.WHITE,4)
	var dark=mat("iron black",Color("161c24"),.4,.5)
	var brass=mat("old gold",Color("89794b"),.42,.7)
	var ember=mat("candles",Color("f1be78"),.3,0,2)
	for x in range(-20,24,8):
		for z in range(-18,23,8):solid(Vector3(x,-.3,z),Vector3(8,.6,8),stone,false)
	bounds(stone,17,[[0,8,10.5]])
	box(Vector3(0,17.5,0),Vector3(49,.4,45),stone)
	box(Vector3(0,.015,0),Vector3(4,.025,40),mat("procession carpet",Color("351d27"),.93))
	for x in [-10,10]:
		for z in [-15,-4,8,19]:
			solid(Vector3(x,5.5,z),Vector3(1.2,11,1.2),stone)
			for off in [-.6,.6]:cylinder(Vector3(x+off,5.5,z+.6),.15,11,trim)
			box(Vector3(x,.3,z),Vector3(2,.6,2),trim)
			box(Vector3(x,10.6,z),Vector3(2,.6,2),trim)
		for z in [-15,-4,8]:
			arch(Vector3(x,0,z),7,10,trim)
	for z in [-16,-3,10]:
		arch(Vector3(0,9,z),20,8,trim)
		for side in [-1,1]:beam(Vector3(side*10,11,z),Vector3(0,17,z-6),.24,trim)
	# Stained-glass lancets and masonry ribs.
	for side in [-1,1]:
		for z in [-15,-4,8,18]:
			box(Vector3(side*23.6,6,z),Vector3(.25,7,4),dark)
			for iy in range(7):
				for iz in range(4):
					var colors=[Color("406183"),Color("825039"),Color("677459"),Color("7f667a")]
					var m=mat("glass"+str((iy+iz)%4),colors[(iy+iz)%4],.23,.1,.65)
					box(Vector3(side*23.43,3+iy*.94,z-1.45+iz*.95),Vector3(.035,.83,.83),m)
			lamp(Vector3(side*21,5,z),Color("6486ac"),1.6,9)
		for z in [-11,1,13]:
			box(Vector3(side*17,1.4,z),Vector3(3,2.8,2),trim)
			rock(Vector3(side*17,3.1,z),Vector3(1.7,2.6,1.2),stone)
			rock(Vector3(side*17,4.6,z),Vector3(.75,.85,.75),trim)
	# Pews force flanking choices; aisle remains open for dodging the Warden.
	for side in [-1,1]:
		for z in [-7,2,11]:
			solid(Vector3(side*6,.5,z),Vector3(5,1,1.4),dark)
			box(Vector3(side*6,1,z+.55),Vector3(5,1,.3),dark)
			box(Vector3(side*6,1.5,z+.55),Vector3(5,.09,.34),brass)
			for x in [side*4,side*8]:
				cylinder(Vector3(x,1.8,z+.65),.045,.55,ember)
			lamp(Vector3(side*6,2,z),Color("ebb776"),1.4,6)
	for i in range(36):
		var p=Vector3(rng.randf_range(-22,22),.15,rng.randf_range(-21,21))
		if abs(p.x)>12:
			rock(p,Vector3(rng.randf_range(.5,1.8),.6,1),trim)
			rock(p+Vector3(0,.26,0),Vector3(1,.10,.8),snow)
	for side in [-1,1]:
		box(Vector3(side*21,.02,0),Vector3(4,.04,44),snow)
		box(Vector3(side*24,12.1,0),Vector3(1,.12,44),snow)
	arch(Vector3(0,0,-21.4),11,12,trim)
	for x in [-4.3,4.3]: box(Vector3(x,5.5,-21.64),Vector3(.3,10.5,.3),brass)
	text("B L A C K   C A T H E D R A L",Vector3(0,12.9,-21.3),Color("b9c1c8"),65)
	lamp(Vector3(0,10,-18),Color("9db5d9"),4,14,true)
	reflection(Vector3(0,4,0),Vector3(48,24,45))

# =====================================================================
# v6 expansions: multi-room maps and prop kits.
# =====================================================================
var book_xforms: Array[Transform3D] = []
var book_colors: Array[Color] = []
var art_cache: Dictionary = {}

func wall_run(a: float, b: float, fixed: float, along_x: bool, h: float, m: Material, gaps: Array) -> void:
	# Builds one straight wall from a to b with door gaps [[centre, width, door_height], ...].
	var cuts = []
	for g in gaps: cuts.append([g[0]-g[1]*.5, g[0]+g[1]*.5, g[2]])
	cuts.sort_custom(func(p, q): return p[0] < q[0])
	var cursor = a
	for c in cuts + [[b, b, h]]:
		if c[0] - cursor > .05:
			var mid = (cursor + c[0]) * .5
			var size = Vector3(c[0]-cursor, h, .6) if along_x else Vector3(.6, h, c[0]-cursor)
			solid(Vector3(mid, h*.5, fixed) if along_x else Vector3(fixed, h*.5, mid), size, m)
		if c[1] > c[0] and h - c[2] > .1:
			var lmid = (c[0]+c[1])*.5; var lh = h - c[2]
			var lsize = Vector3(c[1]-c[0], lh, .6) if along_x else Vector3(.6, lh, c[1]-c[0])
			solid(Vector3(lmid, c[2]+lh*.5, fixed) if along_x else Vector3(fixed, c[2]+lh*.5, lmid), lsize, m, false)
		cursor = maxf(cursor, c[1])

func room(x0: float, x1: float, z0: float, z1: float, h: float, m: Material, doors: Dictionary, ceiling: Material = null, floor_m: Material = null) -> void:
	for side in ["n","s","w","e"]:
		if doors.get(side) is String: continue   # "skip": shared with another room
		var gaps: Array = doors.get(side, [])
		match side:
			"n": wall_run(x0, x1, z1, true, h, m, gaps)
			"s": wall_run(x0, x1, z0, true, h, m, gaps)
			"w": wall_run(z0, z1, x0, false, h, m, gaps)
			"e": wall_run(z0, z1, x1, false, h, m, gaps)
	if floor_m:
		solid(Vector3((x0+x1)*.5, -.3, (z0+z1)*.5), Vector3(x1-x0, .6, z1-z0), floor_m, false)
	if ceiling:
		box(Vector3((x0+x1)*.5, h+.2, (z0+z1)*.5), Vector3(x1-x0+.6, .4, z1-z0+.6), ceiling)

func ramp(from: Vector3, to: Vector3, width: float, m: Material) -> void:
	var mid = (from + to) * .5
	var run = Vector2(to.x-from.x, to.z-from.z).length()
	var rise = to.y - from.y
	var length = sqrt(run*run + rise*rise)
	var yaw = atan2(to.x-from.x, to.z-from.z)
	var pitch = -atan2(rise, run)
	var basis = Basis.from_euler(Vector3(pitch, yaw, 0), EULER_ORDER_YXZ)
	var body = StaticBody3D.new(); body.collision_layer = 1
	var shape = CollisionShape3D.new(); var b = BoxShape3D.new(); b.size = Vector3(width, .2, length)
	shape.shape = b; body.add_child(shape); w.add_child(body)
	body.transform = Transform3D(basis, mid - basis.y * .1)
	groups_append(m, Transform3D(basis.scaled_local(Vector3(width, .2, length)), mid - basis.y * .1))

func groups_append(m: Material, t: Transform3D) -> void:
	var key = str(m.get_instance_id())+":"+cell(t.origin)
	if not groups.has(key): groups[key] = {"material":m,"transforms":[]}
	groups[key].transforms.append(t)

func art(name: String) -> Material:
	if art_cache.has(name): return art_cache[name]
	var m = StandardMaterial3D.new()
	m.albedo_texture = load("res://assets/textures/art/%s.jpg" % name)
	m.roughness = .55
	art_cache[name] = m
	return m

func painting(p: Vector3, size: Vector2, rot_y: float, name: String, frame: Material) -> void:
	var basis = Basis(Vector3.UP, rot_y)
	var node = MeshInstance3D.new(); var quad = QuadMesh.new(); quad.size = size
	node.mesh = quad; node.material_override = art(name)
	node.transform = Transform3D(basis, p + basis * Vector3(0,0,.055))
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	w.add_child(node)
	for e in [[Vector3(0,size.y*.5+.07,0),Vector3(size.x+.28,.14,.09)],[Vector3(0,-size.y*.5-.07,0),Vector3(size.x+.28,.14,.09)],
			[Vector3(size.x*.5+.07,0,0),Vector3(.14,size.y,.09)],[Vector3(-size.x*.5-.07,0,0),Vector3(.14,size.y,.09)]]:
		groups_append(frame, Transform3D(basis.scaled_local(e[1]), p + basis * e[0]))

func candles(centre: Vector3, count: int, radius: float, wax: Material, flame: Material, light: bool = true) -> void:
	var cyl = CylinderMesh.new(); cyl.top_radius = .5; cyl.bottom_radius = .5; cyl.height = 1; cyl.radial_segments = 8; cyl.rings = 1
	var tip = SphereMesh.new(); tip.radius = .5; tip.height = 1; tip.radial_segments = 6; tip.rings = 3
	for i in range(count):
		var a = rng.randf() * TAU; var r = sqrt(rng.randf()) * radius
		var h = rng.randf_range(.12, .42)
		var base = centre + Vector3(cos(a)*r, 0, sin(a)*r)
		instance_mesh("candle wax", cyl, wax, base + Vector3(0,h*.5,0), Vector3(.045,h,.045))
		instance_mesh("noshadow flame", tip, flame, base + Vector3(0,h+.035,0), Vector3(.025,.06,.025))
	if light: lamp(centre + Vector3(0,.8,0), Color("ffb867"), 1.3, 5.5)

func chandelier(p: Vector3, r: float, iron: Material, flame: Material, wax: Material) -> void:
	ring(p, r, .05, iron)
	ring(p + Vector3(0,.5,0), r*.55, .04, iron)
	for k in range(4):
		var a = TAU*k/4.0
		beam(p + Vector3(cos(a)*r,0,sin(a)*r), p + Vector3(0,2.2,0), .04, iron)
	beam(p + Vector3(0,2.2,0), p + Vector3(0,9,0), .05, iron)
	var n = int(r * 14)
	for k in range(n):
		var a = TAU*k/n
		var c = p + Vector3(cos(a)*r, .05, sin(a)*r)
		cylinder(c + Vector3(0,.12,0), .03, .24, wax)
		rock(c + Vector3(0,.29,0), Vector3(.05,.1,.05), flame)
	lamp(p + Vector3(0,-.3,0), Color("ffc078"), 2.6, r*4.5 + 4.0)

func bookshelf(p: Vector3, width: float, height: float, rot_y: float, wood: Material) -> void:
	var basis = Basis(Vector3.UP, rot_y)
	var depth = .45
	for e in [[Vector3(0,height*.5,-(depth*.5-.02)),Vector3(width,height,.04)],[Vector3(-width*.5,height*.5,0),Vector3(.06,height,depth)],
			[Vector3(width*.5,height*.5,0),Vector3(.06,height,depth)],[Vector3(0,height,0),Vector3(width+.1,.08,depth+.06)]]:
		groups_append(wood, Transform3D(basis.scaled_local(e[1]), p + basis * e[0]))
	var shelves = int(height / .42)
	var palette = [Color("5b1f1c"),Color("1f3a2c"),Color("2a2f4f"),Color("6b4a24"),Color("3d2a1f"),Color("7a6a4a"),Color("2b1b28"),Color("8a3a22")]
	for sidx in range(shelves):
		var y = .06 + sidx * .42
		groups_append(wood, Transform3D(basis.scaled_local(Vector3(width,.04,depth)), p + basis * Vector3(0,y,0)))
		var x = -width*.5 + .06
		while x < width*.5 - .08:
			var bw = rng.randf_range(.035,.075); var bh = rng.randf_range(.24,.36); var bd = rng.randf_range(.22,.3)
			var lean = rng.randf_range(-.06,.06) if rng.randf() < .12 else 0.0
			if rng.randf() < .05: x += rng.randf_range(.06,.2); continue
			var t = Transform3D(basis * Basis(Vector3.BACK, lean).scaled_local(Vector3(bw,bh,bd)), p + basis * Vector3(x+bw*.5, y+.02+bh*.5, .0))
			book_xforms.append(t)
			book_colors.append(palette[rng.randi() % palette.size()].lightened(rng.randf_range(-.1,.15)))
			x += bw + .004

func book_stack(p: Vector3, count: int) -> void:
	var y = p.y
	for i in range(count):
		var s = Vector3(rng.randf_range(.18,.26),.04,rng.randf_range(.24,.32))
		book_xforms.append(Transform3D(Basis(Vector3.UP, rng.randf_range(-.4,.4)).scaled_local(s), Vector3(p.x,y+s.y*.5,p.z)))
		book_colors.append([Color("5b1f1c"),Color("1f3a2c"),Color("2a2f4f"),Color("6b4a24")][rng.randi()%4])
		y += s.y

func finish_books() -> void:
	if book_xforms.is_empty(): return
	var mm = MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_colors = true
	var mesh = BoxMesh.new(); mesh.size = Vector3.ONE
	var m = StandardMaterial3D.new(); m.vertex_color_use_as_albedo = true; m.vertex_color_is_srgb = true; m.roughness = .78
	mesh.material = m
	mm.mesh = mesh; mm.instance_count = book_xforms.size()
	for i in range(book_xforms.size()):
		mm.set_instance_transform(i, book_xforms[i]); mm.set_instance_color(i, book_colors[i])
	var node = MultiMeshInstance3D.new(); node.multimesh = mm
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	w.add_child(node)

func grass(area_rect: Rect2, count: int, tint: Color, avoid: Array = []) -> void:
	var blade = ArrayMesh.new()
	var arrays = []; arrays.resize(Mesh.ARRAY_MAX)
	var verts = PackedVector3Array(); var uvs = PackedVector2Array(); var normals = PackedVector3Array(); var idx = PackedInt32Array()
	for k in range(3):
		var basis = Basis(Vector3.UP, k * 2.1).rotated(Vector3.RIGHT, (k-1) * .22)
		var off = Vector3((k-1)*.35, 0, (k%2)*.3 - .15)
		var start = verts.size()
		for v in [[Vector3(-.5,0,0),Vector2(0,0)],[Vector3(.5,0,0),Vector2(1,0)],[Vector3(-.3,.5,.05),Vector2(.2,.5)],[Vector3(.3,.5,.05),Vector2(.8,.5)],[Vector3(0,1,.15),Vector2(.5,1)]]:
			verts.append(basis * v[0] + off); uvs.append(v[1]); normals.append(Vector3(0,1,.5).normalized())
		for i in [0,1,2, 1,3,2, 2,3,4]: idx.append(start + i)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_INDEX] = idx
	blade.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var m = ShaderMaterial.new(); m.shader = load("res://assets/shaders/leaves.gdshader"); m.set_shader_parameter("tint", tint)
	for i in range(count):
		var p = Vector3(rng.randf_range(area_rect.position.x, area_rect.end.x), 0, rng.randf_range(area_rect.position.y, area_rect.end.y))
		var skip = false
		for r in avoid: if r.has_point(Vector2(p.x, p.z)): skip = true
		if skip: continue
		var hgt = rng.randf_range(.25,.6)
		instance_mesh("noshadow grass", blade, m, p, Vector3(rng.randf_range(.07,.11), hgt, rng.randf_range(.07,.11)), Vector3(0, rng.randf()*TAU, 0))

func flowers(area_rect: Rect2, count: int, palette: Array) -> void:
	var petal = SphereMesh.new(); petal.radius = .5; petal.height = 1; petal.radial_segments = 6; petal.rings = 3
	var stem_m = mat("stem", Color("3f5a28"), .8)
	for i in range(count):
		var c = Vector3(rng.randf_range(area_rect.position.x, area_rect.end.x), 0, rng.randf_range(area_rect.position.y, area_rect.end.y))
		var col: Color = palette[rng.randi() % palette.size()]
		var fm = mat("flower"+col.to_html(), col, .6, 0, .15)
		var h = rng.randf_range(.25,.5)
		instance_mesh("noshadow stem", petal, stem_m, c + Vector3(0,h*.5,0), Vector3(.012,h,.012))
		for k in range(5):
			var a = TAU*k/5.0 + rng.randf()
			instance_mesh("noshadow petal"+col.to_html(), petal, fm, c + Vector3(cos(a)*.055,h,sin(a)*.055), Vector3(.085,.022,.055), Vector3(0,-a,0))
		instance_mesh("noshadow centre", petal, mat("flower centre", Color("e3b43a"), .6), c + Vector3(0,h+.012,0), Vector3(.05,.03,.05))

func tree(p: Vector3, height: float, canopy: Material, bark: Material, spread: float = 2.6) -> void:
	cylinder(p + Vector3(0,height*.35,0), .22, height*.7, bark, Vector3(rng.randf_range(-.06,.06),0,rng.randf_range(-.06,.06)))
	for k in range(4):
		var a = TAU*k/4.0 + rng.randf()
		beam(p + Vector3(0,height*.55,0), p + Vector3(cos(a)*spread*.6, height*.85, sin(a)*spread*.6), .1, bark)
	for k in range(9):
		var a = rng.randf()*TAU; var r = rng.randf_range(0, spread)
		rock(p + Vector3(cos(a)*r, height*rng.randf_range(.75,1.05), sin(a)*r), Vector3.ONE*rng.randf_range(1.2,2.0)*Vector3(1,.7,1), canopy)
	solid(p + Vector3(0,1.5,0), Vector3(.5,3,.5), bark, true)

func stone_lantern(p: Vector3, stone: Material, glow: Material) -> void:
	solid(p + Vector3(0,.35,0), Vector3(.5,.7,.5), stone)
	cylinder(p + Vector3(0,.95,0), .09, .5, stone)
	box(p + Vector3(0,1.32,0), Vector3(.48,.08,.48), stone)
	box(p + Vector3(0,1.5,0), Vector3(.34,.3,.34), glow)
	cylinder(p + Vector3(0,1.72,0), .34, .1, stone, Vector3.ZERO)
	box(p + Vector3(0,1.86,0), Vector3(.18,.18,.18), stone)
	lamp(p + Vector3(0,1.5,0), Color("ffb468"), 1.2, 5.0)

func light_shaft(p: Vector3, radius: float, height: float, color: Color) -> void:
	var node = MeshInstance3D.new(); var c = CylinderMesh.new()
	c.top_radius = radius*.6; c.bottom_radius = radius; c.height = height; c.radial_segments = 20; c.rings = 1; c.cap_top = false; c.cap_bottom = false
	var m = StandardMaterial3D.new(); m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.albedo_color = Color(color.r, color.g, color.b, .07); m.cull_mode = BaseMaterial3D.CULL_DISABLED
	node.mesh = c; node.material_override = m; node.position = p + Vector3(0,height*.5,0)
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	w.add_child(node)

func particles(p: Vector3, extents: Vector3, amount: int, color: Color, size: float, fall: float, glow: bool) -> void:
	var g = GPUParticles3D.new(); g.amount = amount; g.lifetime = 8.0; g.preprocess = 8.0
	g.position = p; g.visibility_aabb = AABB(-extents - Vector3(2,6,2), extents*2 + Vector3(4,12,4))
	var pm = ParticleProcessMaterial.new(); pm.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	pm.emission_box_extents = extents; pm.gravity = Vector3(.2, -fall, .1); pm.initial_velocity_min = .05; pm.initial_velocity_max = .3
	pm.direction = Vector3(.3,-.2,.1); pm.spread = 180; pm.angular_velocity_min = -90; pm.angular_velocity_max = 90
	g.process_material = pm
	var q = QuadMesh.new(); q.size = Vector2(size, size*.7)
	var m = StandardMaterial3D.new(); m.albedo_color = color; m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	if glow:
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD; m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		var soft = GradientTexture2D.new(); soft.fill = GradientTexture2D.FILL_RADIAL; soft.fill_from = Vector2(.5,.5); soft.fill_to = Vector2(1,.5)
		var gr = Gradient.new(); gr.set_color(0, Color(1,1,1,1)); gr.set_color(1, Color(1,1,1,0)); soft.gradient = gr
		m.albedo_texture = soft
	q.material = m; g.draw_pass_1 = q
	w.add_child(g)

# ---------------------------------------------------------------- Black Cathedral depths
func cathedral_depths() -> void:
	var stone = surface("cathedral stone", Color("4d535b"), 3)
	var trim = surface("cut stone", Color("717780"), 3)
	var floor_m = surface("nave floor", Color("5f5a55"), 0)
	var dark = mat("iron black", Color("161c24"), .4, .5)
	var brass = mat("old gold", Color("89794b"), .42, .7)
	var gold = mat("organ gold", Color("b39350"), .3, .85)
	var wood = mat("dark oak", Color("2e1d14"), .62)
	var oak = mat("library oak", Color("4a3020"), .6)
	var wax = mat("wax", Color("e6dcc4"), .6)
	var flame = mat("candle flame", Color("ffbf6a"), .3, 0, 4.0)
	var crimson = mat("crimson cloth", Color("5a1218"), .95)
	var marble = surface("white marble", Color("cfc8bb"), 0)
	var bone = mat("bone", Color("cbbf9f"), .8)
	w.area = Rect2i(-23, -69, 57, 90)
	w.objective_position = Vector3(0, .45, -39.2)
	w.wave_anchors = [Vector3(0,0,-6), Vector3(0,0,-30), Vector3(25,0,-33), Vector3(0,0,-58)]
	w.wave_hints = ["", "THEY HOLD THE CHANCEL / PUSH THROUGH THE NAVE", "MOVEMENT IN THE LIBRARY", "THE WARDEN WAKES IN THE CRYPT"]
	w.boss_spawn = Vector3(0, .1, -59)
	# Chancel (A): open from the nave; doors east to the library, south to the crypt.
	room(-16, 16, -46, -22, 16, stone, {"n":"skip", "e":[[-32,4,5]], "s":[[-13.2,3.4,5],[13.2,3.4,5]]}, stone, floor_m)
	box(Vector3(0,.016,-30), Vector3(4,.025,16), mat("procession carpet", Color("351d27"), .93))
	# Raised altar stage with a ramp.
	solid(Vector3(0,.225,-41.75), Vector3(18,.45,7.5), marble)
	ramp(Vector3(0,0,-35.5), Vector3(0,.45,-38), 18, marble)
	for x in [-9,9]: box(Vector3(x,.6,-41.75), Vector3(.25,.3,7.5), gold)
	solid(Vector3(0,1.0,-42.2), Vector3(3.4,1.1,1.3), marble)
	box(Vector3(0,1.57,-42.2), Vector3(3.6,.05,1.5), mat("altar linen", Color("e5ddc8"), .9))
	box(Vector3(0,1.4,-41.53), Vector3(3.2,.5,.02), crimson)
	for x in [-1.3,1.3]:
		cylinder(Vector3(x,1.85,-42.2), .05, .5, gold); cylinder(Vector3(x,2.25,-42.2), .035, .3, wax); rock(Vector3(x,2.45,-42.2), Vector3(.05,.11,.05), flame)
	lamp(Vector3(0,2.6,-41.6), Color("ffc27a"), 2.2, 7)
	# Pipe organ and rose window.
	solid(Vector3(0,1.6,-45), Vector3(14,3.2,1.6), wood)
	for i in range(29):
		var x = -7 + i * .5
		var h = 3.0 + 7.5 * (1.0 - pow(absf(x)/7.2, 1.6))
		cylinder(Vector3(x, 3.2 + h*.5, -45.3), .17, h, gold)
		box(Vector3(x, 3.2 + h*.25, -45.12), Vector3(.12,.06,.02), dark)
	for k in range(16):
		var a = TAU*k/16.0
		beam(Vector3(0,13.2,-45.65), Vector3(cos(a)*2.8, 13.2+sin(a)*2.8, -45.65), .1, trim)
		var colors = [Color("3c5a8c"), Color("8c3a2c"), Color("c99a3c"), Color("47744a")]
		box(Vector3(cos(a+.2)*1.9, 13.2+sin(a+.2)*1.9, -45.72), Vector3(.9,.9,.04), mat("rose"+str(k%4), colors[k%4], .2, 0, 1.6))
	ring(Vector3(0,13.2,-45.6), 3.0, .18, trim)
	lamp(Vector3(0,12,-43), Color("8fa9e0"), 2.0, 12)
	# Choir stalls, columns, banners and paintings.
	for side in [-1,1]:
		for z in [-26.5,-29.5,-32.5]:
			solid(Vector3(side*6.8,.45,z), Vector3(4.2,.9,.9), wood)
			box(Vector3(side*6.8,1.2,z+.4), Vector3(4.2,.9,.12), wood)
			box(Vector3(side*6.8,.98,z-.35), Vector3(4.2,.05,.4), brass)
		for z in [-25,-30.5,-36]:
			solid(Vector3(side*10.5,8,z), Vector3(1.1,16,1.1), trim)
			for off in [-.5,.5]: cylinder(Vector3(side*10.5+off,8,z+.5), .12, 16, stone)
		for z in [-27.75, -33.25]:
			box(Vector3(side*10.5, 9.5, z), Vector3(.05, 5.5, 1.6), crimson)
			box(Vector3(side*10.48, 10.2, z), Vector3(.06, .9, .9), gold)
		var arts = ["portrait_saint","landscape_dusk","portrait_noble","storm_sea"]
		for k in range(4):
			painting(Vector3(side*15.65, 4.6, -25 - k*5.2), Vector2(2.2,2.8), -side*PI*.5, arts[(k + (2 if side > 0 else 0)) % 4], gold)
		for z in [-27.5,-37.5]:
			box(Vector3(side*14.6,.5,z), Vector3(1.2,1,.5), dark)
			candles(Vector3(side*14.6,1.0,z), 18, .45, wax, flame)
	chandelier(Vector3(0,9.2,-28), 2.2, dark, flame, wax)
	chandelier(Vector3(0,9.2,-36), 2.2, dark, flame, wax)
	solid(Vector3(-3.8,.6,-37), Vector3(.5,1.2,.5), wood)
	box(Vector3(-3.8,1.25,-37), Vector3(.8,.08,.6), wood)
	book_stack(Vector3(-3.8,1.29,-37), 1)
	reflection(Vector3(0,6,-34), Vector3(32,16,24))
	# Library (B).
	room(16, 34, -42, -24, 7.5, stone, {"w":"skip"}, mat("library ceiling", Color("2a1e18"), .8), mat("library floor", Color("3b2a1d"), .55))
	for x in [18.5, 22.5, 26.5, 30.5]:
		bookshelf(Vector3(x, 0, -41.4), 3.8, 5.2, 0, oak)
		bookshelf(Vector3(x, 0, -24.6), 3.8, 5.2, PI, oak)
	for z in [-27.5, -31.5, -35.5, -39]:
		bookshelf(Vector3(33.4, 0, z), 3.6, 5.2, -PI*.5, oak)
	for z in [-29.5, -36]:
		solid(Vector3(24.5, .42, z), Vector3(4.2, .84, 1.6), oak)
		box(Vector3(24.5, .86, z), Vector3(4.4, .05, 1.8), wood)
		for x in [22.8, 26.2]:
			solid(Vector3(x, .24, z + 1.3), Vector3(.6,.48,.6), wood); box(Vector3(x, .8, z + 1.58), Vector3(.6,.7,.08), wood)
			solid(Vector3(x, .24, z - 1.3), Vector3(.6,.48,.6), wood); box(Vector3(x, .8, z - 1.58), Vector3(.6,.7,.08), wood)
		book_stack(Vector3(23.2, .89, z), 3); book_stack(Vector3(25.9, .89, z + .3), 2)
		box(Vector3(24.6, .9, z - .2), Vector3(.5,.02,.34), mat("open page", Color("e2d6b4"), .9))
		candles(Vector3(24.5, .89, z), 3, .15, wax, flame)
	cylinder(Vector3(30.5,.45,-33), .06, .9, brass); rock(Vector3(30.5,1.2,-33), Vector3(.55,.55,.55), mat("globe", Color("4c6b7a"), .45))
	ring(Vector3(30.5,1.2,-33), .33, .02, brass)
	beam(Vector3(31.2,0,-40.9), Vector3(31.5,4.6,-40.95), .06, wood); beam(Vector3(31.8,0,-40.9), Vector3(32.1,4.6,-40.95), .06, wood)
	for y in range(1,8): beam(Vector3(31.2+y*.04,y*.6,-40.9), Vector3(31.8+y*.04,y*.6,-40.9), .03, wood)
	box(Vector3(25,.02,-33), Vector3(9,.02,6), mat("library rug", Color("4a1d1e"), .95))
	painting(Vector3(16.35, 3.6, -38.5), Vector2(1.6,2.0), PI*.5, "still_life", gold)
	painting(Vector3(16.35, 3.6, -27.5), Vector2(1.6,2.0), PI*.5, "portrait_widow", gold)
	chandelier(Vector3(25,5.6,-33), 1.4, dark, flame, wax)
	lamp(Vector3(20,3.5,-33), Color("ffb878"), 1.4, 8)
	reflection(Vector3(25,3.5,-33), Vector3(18,7,18))
	# Crypt (C): colonnade ring, tombs, statues, ossuary niches, candle fields.
	room(-16, 16, -70, -46, 9, stone, {"n":"skip"}, stone, surface("crypt floor", Color("3a3d42"), 3))
	for k in range(10):
		var a = TAU*k/10.0
		var c = Vector3(cos(a)*9, 0, -58 + sin(a)*9)
		solid(c + Vector3(0,4.5,0), Vector3(.9,9,.9), trim)
		cylinder(c + Vector3(0,.3,0), .7, .6, stone); cylinder(c + Vector3(0,8.6,0), .7, .5, stone)
	ring(Vector3(0,8.9,-58), 9, .25, trim)
	for k in range(4):
		var a = TAU*k/4.0 + PI*.25
		var c = Vector3(cos(a)*12.5, 0, -58 + sin(a)*9.5)
		solid(c + Vector3(0,.45,0), Vector3(2.4,.9,1.1), marble)
		box(c + Vector3(0,.98,0), Vector3(2.6,.16,1.3), trim)
		rock(c + Vector3(0,1.12,0), Vector3(1.6,.22,.55), marble)
	for k in range(4):
		var a = TAU*k/4.0
		var c = Vector3(cos(a)*6.2, 0, -58 + sin(a)*6.2)
		solid(c + Vector3(0,.6,0), Vector3(1,1.2,1), stone)
		cylinder(c + Vector3(0,2.0,0), .38, 1.6, marble, Vector3.ZERO)
		rock(c + Vector3(0,3.05,0), Vector3(.4,.46,.4), marble)
		for side in [-1,1]: beam(c + Vector3(side*.22,2.75,.2), c + Vector3(side*.62,1.35,.5), .32, marble)
		cylinder(c + Vector3(0,3.38,0), .3, .025, mat("statue halo", Color("c9a95a"), .3, .8), Vector3(PI*.5,0,0))
		candles(c + Vector3(0,0,0) + Vector3(cos(a)*1.4,0,sin(a)*1.4), 26, .7, wax, flame, k % 2 == 0)
	for side in [-1,1]:
		for z in [-50,-54,-62,-66]:
			box(Vector3(side*15.6,3.2,z), Vector3(.3,2.6,2.4), dark)
			for iy in range(3):
				for iz in range(4):
					rock(Vector3(side*15.45, 2.2 + iy*.8, z - .9 + iz*.6), Vector3(.24,.26,.24), bone)
	candles(Vector3(0,0,-58), 40, 2.4, wax, flame)
	chandelier(Vector3(0,7.5,-58), 3.0, dark, flame, wax)
	light_shaft(Vector3(0,0,-58), 3.2, 9, Color("9fb6e8"))
	lamp(Vector3(0,8,-58), Color("8fa9e0"), 2.5, 16)
	reflection(Vector3(0,4.5,-58), Vector3(32,9,24))
	finish_books()

# ---------------------------------------------------------------- Hollow Bamboo grounds
func bamboo_grounds() -> void:
	var gravel = surface("raked gravel", Color("b9b2a0"), 5)
	var moss = surface("meadow earth", Color("4a5a2a"), 1)
	var stone = surface("moss stone", Color("5c6651"), 3)
	var red = mat("shrine red", Color("672d21"), .7)
	var vermilion = mat("torii vermilion", Color("b33a22"), .55)
	var black = mat("lacquer black", Color("161412"), .45)
	var wood = mat("cedar", Color("6e4a2d"), .7)
	var paper = mat("shoji paper", Color("f2e6c8"), .9, 0, .35)
	var tatami = mat("tatami", Color("a8a46a"), .95)
	var roof = mat("roof", Color("26312d"), .48)
	var glow = mat("lantern glow", Color("ffcf8a"), .5, 0, 2.2)
	var blossom = foliage_material("cherry blossom", Color("e7a9c0"))
	var green = foliage_material("maple green", Color("3d6b2c"))
	var bark = mat("bark", Color("3a2a20"), .9)
	w.area = Rect2i(-23, -73, 56, 94)
	w.objective_position = Vector3(0, .05, -39.5)
	w.wave_anchors = [Vector3(0,0,-6), Vector3(0,0,-32), Vector3(0,0,-61)]
	w.wave_hints = ["", "THE SHRINE GUARD GATHERS / FOLLOW THE TORII", "THE BELLKEEPER WAITS IN THE MEADOW"]
	w.boss_spawn = Vector3(0, .1, -62)
	# Shrine courtyard (A).
	room(-18, 18, -48, -22, 1.8, stone, {"n":"skip", "e":[[-33,3,1.8]], "s":[[-12,4,1.8],[12,4,1.8]]}, null, gravel)
	for x in [-2.6,2.6]: cylinder(Vector3(x,2.4,-23.5), .2, 4.8, vermilion)
	box(Vector3(0,4.7,-23.5), Vector3(7.4,.32,.5), black); box(Vector3(0,4.15,-23.5), Vector3(6,.2,.32), vermilion)
	box(Vector3(0,4.42,-23.5), Vector3(.22,.4,.24), vermilion)
	for z in range(-26, -39, -2):
		rock(Vector3(rng.randf_range(-.3,.3),.04,z), Vector3(1.2,.12,.9), stone)
	for z in [-27,-32,-37]:
		for x in [-3.4, 3.4]: stone_lantern(Vector3(x,0,z), stone, glow)
	# Koi pond with lilies, lotus and koi.
	water(Vector3(9.5,.02,-32), Vector3(8,.05,9), Color("1d3b38"))
	for k in range(22):
		var a = TAU*k/22.0
		rock(Vector3(9.5+cos(a)*4.3,.15,-32+sin(a)*4.8), Vector3(rng.randf_range(.5,.9),.35,rng.randf_range(.5,.8)), stone)
	for k in range(14):
		var lp = Vector3(rng.randf_range(6.5,12.5),.06,rng.randf_range(-35.5,-28.5))
		cylinder(lp, rng.randf_range(.18,.3), .02, mat("lily pad", Color("3a6b2a"), .6))
		if k % 3 == 0: rock(lp + Vector3(0,.08,0), Vector3(.16,.12,.16), mat("lotus", Color("f0a6c2"), .5, 0, .2))
	for k in range(6):
		var kp = Vector3(rng.randf_range(7,12),.0,rng.randf_range(-35,-29))
		rock(kp, Vector3(.42,.07,.12), mat("koi "+str(k%2), [Color("e8642a"),Color("f2efe6")][k%2], .35))
	w.obstacles.append(Rect2(Vector2(5.2,-36.8),Vector2(8.6,9.6)))
	# Cherry and maple trees, falling petals.
	for tp in [Vector3(-12,0,-27), Vector3(-13,0,-40), Vector3(14,0,-43), Vector3(-7,0,-45)]:
		tree(tp, 5.0, blossom, bark, 2.4)
	tree(Vector3(15,0,-25), 4.4, green, bark, 2.0)
	particles(Vector3(0,6,-35), Vector3(16,1,12), 140, Color("f2b7cb"), .07, .25, false)
	grass(Rect2(-17.5,-47.5,35,25), 2600, Color(.3,.46,.14), [Rect2(-4.5,-47.5,9,26), Rect2(5,-37,9,10)])
	flowers(Rect2(-17,-47,10,20), 70, [Color("e9e2f2"), Color("f4c64a"), Color("c84b7a")])
	# Shrine: raised floor, pillars, layered roof with flared eaves, bell, rope, lanterns.
	solid(Vector3(0,.25,-45), Vector3(10,.5,5), wood)
	ramp(Vector3(0,0,-41.4), Vector3(0,.5,-42.5), 4, wood)
	for x in [-4.6,-1.6,1.6,4.6]:
		for z in [-43,-47]: cylinder(Vector3(x,2.3,z), .16, 3.6, red)
	box(Vector3(0,4.2,-45), Vector3(11,.3,6), wood)
	for k in range(4):
		box(Vector3(0,4.5+k*.32,-45), Vector3(12.4-k*2.2,.3,7.0-k*1.2), roof)
	for side in [-1,1]: beam(Vector3(side*6,4.4,-41.6), Vector3(side*6.9,5.0,-41.2), .22, roof)
	box(Vector3(0,3.3,-44.9), Vector3(.2,.8,.2), wood)
	ring(Vector3(0,3.75,-42.9), .9, .08, mat("straw rope", Color("c9b27a"), .9))
	for x in [-3.2,3.2]:
		cylinder(Vector3(x,3.4,-42.9), .22, .5, glow); lamp(Vector3(x,3.2,-42.6), Color("ffb468"), 1.5, 6)
	box(Vector3(0,.8,-43.8), Vector3(1.4,.6,.7), wood)
	painting(Vector3(-2.8,2.3,-46.6), Vector2(.8,2.0), 0, "scroll_cranes", wood)
	# Teahouse interior (B).
	room(18, 32, -40, -26, 3.4, wood, {"w":"skip"}, roof, tatami)
	for z in range(-39, -26, 2):
		for x in range(19, 32, 2): box(Vector3(x+.5, .005, z+.5), Vector3(1.95,.01,.95), mat("tatami edge", Color("23251c"), .9))
	for x in [21,24,27,30]:
		box(Vector3(x,1.8,-39.65), Vector3(2.6,2.6,.04), paper)
		for k in range(4): box(Vector3(x-1.3+k*.87,1.8,-39.6), Vector3(.03,2.6,.05), black)
		for y in [.9,1.8,2.7]: box(Vector3(x,y,-39.6), Vector3(2.6,.03,.05), black)
	for z in [-37,-33,-29]:
		box(Vector3(31.65,1.8,z), Vector3(.04,2.6,3.2), paper)
	for c in [Vector3(22.5,0,-30), Vector3(27.5,0,-30), Vector3(25,0,-35.5)]:
		solid(c + Vector3(0,.18,0), Vector3(1.6,.36,1), black)
		for d in [Vector3(-1.1,0,0), Vector3(1.1,0,0)]: box(c + d + Vector3(0,.06,0), Vector3(.6,.12,.6), mat("zabuton", Color("6b2230"), .95))
		cylinder(c + Vector3(-.3,.4,0), .045, .07, mat("tea cup", Color("d9cfb8"), .3))
		cylinder(c + Vector3(.25,.43,0), .09, .14, mat("iron kettle", Color("1d1b1a"), .5, .4))
	for x in [21.5,25,28.5]:
		beam(Vector3(x,3.4,-33), Vector3(x,2.6,-33), .015, black)
		rock(Vector3(x,2.35,-33), Vector3(.36,.5,.36), mat("paper lantern", Color("ffd9a0"), .9, 0, 1.6))
		lamp(Vector3(x,2.3,-33), Color("ffc890"), 1.2, 5)
	painting(Vector3(31.62,1.9,-31), Vector2(.7,1.75), -PI*.5, "scroll_bamboo", black)
	solid(Vector3(30.5,.35,-26.9), Vector3(1,.7,.6), black)
	rock(Vector3(30.5,.95,-26.9), Vector3(.9,.5,.6), green)
	# Meadow (C): grass, flowers, trees, stream and waterfall.
	room(-20, 20, -74, -48, 2.2, stone, {"n":"skip"}, null, moss)
	solid(Vector3(0,4,-73.3), Vector3(16,8,1.2), stone)
	for k in range(12): rock(Vector3(rng.randf_range(-8,8),rng.randf_range(1,7),-72.4), Vector3(rng.randf_range(1.2,2.4),rng.randf_range(1,2),1.2), stone)
	water(Vector3(0,4,-72.3), Vector3(3.2,8,.12), Color("8fb7c4"))
	water(Vector3(0,.03,-69.5), Vector3(10,.05,5), Color("1f4044"))
	w.obstacles.append(Rect2(Vector2(-5.5,-72.5),Vector2(11,6)))
	particles(Vector3(0,.6,-70), Vector3(4,.4,1.5), 60, Color(1,1,1,.35), .35, -.3, true)
	grass(Rect2(-19.5,-73,39,24.5), 7000, Color(.32,.5,.15), [Rect2(-5,-72.5,10,6)])
	flowers(Rect2(-19,-66,38,17), 340, [Color("e9e2f2"), Color("f4c64a"), Color("c84b7a"), Color("7a6ad8"), Color("f08a4a")])
	for tp in [Vector3(-15,0,-52), Vector3(16,0,-55), Vector3(-16,0,-67), Vector3(15,0,-68)]:
		tree(tp, 5.5, green if tp.x > 0 else blossom, bark, 2.8)
	for k in range(8):
		var rp = Vector3(rng.randf_range(-17,17),.3,rng.randf_range(-70,-50))
		if absf(rp.x) < 4 and rp.z < -64: continue
		rock(rp, Vector3(rng.randf_range(.8,1.8),rng.randf_range(.5,1.1),rng.randf_range(.8,1.5)), stone)
	particles(Vector3(0,1.4,-60), Vector3(17,1,11), 90, Color("d8ff7a"), .06, -.02, true)
	lamp(Vector3(0,3,-60), Color("cfe6ff"), 1.0, 18)
	reflection(Vector3(0,3,-35), Vector3(36,8,26))
