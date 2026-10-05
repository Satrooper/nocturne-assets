extends RefCounted
static func metal(color: Color, rough: float=.35) -> StandardMaterial3D:
	var m=StandardMaterial3D.new()
	m.albedo_color=color;m.metallic=.78;m.roughness=rough
	return m
static func piece(root: Node3D,p: Vector3,s: Vector3,m: Material,rot: Vector3=Vector3.ZERO) -> void:
	var node=MeshInstance3D.new()
	var mesh=BoxMesh.new();mesh.size=s
	node.mesh=mesh;node.material_override=m;node.position=p;node.rotation=rot
	root.add_child(node)
static func barrel(root: Node3D,p: Vector3,radius: float,length: float,m: Material) -> void:
	var node=MeshInstance3D.new()
	var mesh=CylinderMesh.new()
	mesh.top_radius=radius;mesh.bottom_radius=radius;mesh.height=length;mesh.radial_segments=12
	node.mesh=mesh;node.material_override=m;node.position=p;node.rotation.x=PI*.5
	root.add_child(node)
static func glow(color: Color, energy: float=2.4) -> StandardMaterial3D:
	var m=StandardMaterial3D.new()
	m.albedo_color=color;m.emission_enabled=true;m.emission=color;m.emission_energy_multiplier=energy;m.roughness=.3
	return m
static func cone(root: Node3D,p: Vector3,r0: float,r1: float,length: float,m: Material,segments: int=12) -> MeshInstance3D:
	var node=MeshInstance3D.new()
	var mesh=CylinderMesh.new()
	mesh.top_radius=r0;mesh.bottom_radius=r1;mesh.height=length;mesh.radial_segments=segments;mesh.rings=1
	node.mesh=mesh;node.material_override=m;node.position=p;node.rotation.x=-PI*.5
	root.add_child(node)
	return node
static func ring(root: Node3D,p: Vector3,r: float,thick: float,m: Material) -> void:
	var node=MeshInstance3D.new();var mesh=TorusMesh.new()
	mesh.inner_radius=r-thick;mesh.outer_radius=r;mesh.rings=16;mesh.ring_segments=6
	node.mesh=mesh;node.material_override=m;node.position=p;node.rotation.x=PI*.5
	root.add_child(node)
static func clear(root: Node3D) -> void:
	for child in root.get_children():
		root.remove_child(child)
		child.queue_free()
static func build(root: Node3D,index: int) -> float:
	clear(root)
	if index>=3: return exotic(root,index)
	var alloy=metal(Color("333d41"))
	var edge=metal(Color("7b8381"),.27)
	var polymer=metal(Color("161d21"),.77)
	var tan=metal(Color("574e3c"),.7)
	polymer.metallic=.02;tan.metallic=.05
	if index==0:
		piece(root,Vector3(0,.025,-.19),Vector3(.075,.105,.34),alloy)
		piece(root,Vector3(0,-.12,-.08),Vector3(.072,.20,.09),polymer,Vector3(-.24,0,0))
		barrel(root,Vector3(0,0,-.37),.024,.12,edge)
		piece(root,Vector3(0,.086,-.31),Vector3(.025,.025,.028),polymer)
		piece(root,Vector3(0,.086,-.05),Vector3(.05,.025,.028),polymer)
		for i in range(5): piece(root,Vector3(.039,.025,-.08-i*.018),Vector3(.007,.074,.006),edge)
		piece(root,Vector3(.0,-.078,-.18),Vector3(.08,.014,.15),alloy)
		return -.44
	piece(root,Vector3(0,0,-.26),Vector3(.095,.14,.36),alloy)
	piece(root,Vector3(0,-.13,-.12),Vector3(.08,.22,.10),polymer,Vector3(-.25,0,0))
	piece(root,Vector3(0,.01,.03),Vector3(.075,.10,.20),alloy)
	piece(root,Vector3(0,-.035,.17),Vector3(.10,.20,.15),tan)
	piece(root,Vector3(0,-.025,.25),Vector3(.12,.23,.025),polymer)
	barrel(root,Vector3(0,.025,-.66),.025,.46,edge)
	if index==1:
		piece(root,Vector3(0,-.19,-.32),Vector3(.072,.25,.14),alloy,Vector3(.12,0,0))
		piece(root,Vector3(0,0,-.50),Vector3(.115,.115,.23),tan)
		for i in range(9):
			piece(root,Vector3(0,.09,-.13-i*.053),Vector3(.105,.02,.022),polymer)
			piece(root,Vector3(.059,.0,-.40-i*.023),Vector3(.009,.05,.012),polymer)
		barrel(root,Vector3(0,.145,-.22),.042,.16,polymer)
		barrel(root,Vector3(0,.145,-.307),.029,.012,edge)
	else:
		barrel(root,Vector3(0,-.045,-.61),.031,.42,alloy)
		piece(root,Vector3(0,-.035,-.49),Vector3(.13,.12,.22),tan)
		for i in range(7): piece(root,Vector3(0,-.035,-.39-i*.03),Vector3(.139,.125,.011),polymer)
		piece(root,Vector3(0,.095,-.20),Vector3(.055,.035,.08),polymer)
	barrel(root,Vector3(0,.025,-.90),.038,.11,polymer)
	for z in [-.16,-.30]:
		barrel(root,Vector3(.052,.025,z),.012,.008,edge)
	piece(root,Vector3(.052,.03,-.23),Vector3(.008,.035,.085),polymer)
	piece(root,Vector3(.062,.01,-.23),Vector3(.018,.018,.06),edge)
	piece(root,Vector3(0,.075,-.79),Vector3(.065,.07,.028),alloy)
	piece(root,Vector3(0,.12,-.79),Vector3(.022,.025,.025),edge)
	for i in range(4):piece(root,Vector3(0,-.09-i*.035,-.11),Vector3(.084,.009,.10),tan)
	piece(root,Vector3(-.052,.02,-.20),Vector3(.006,.015,.085),tan)
	return -.965

# Minigun, rocket launcher, beam laser, plasma blaster.
static func exotic(root: Node3D,index: int) -> float:
	var alloy=metal(Color("2f3a3e"))
	var edge=metal(Color("8a9290"),.25)
	var polymer=metal(Color("14191c"),.75);polymer.metallic=.02
	if index==3:
		piece(root,Vector3(0,-.01,-.12),Vector3(.16,.17,.36),alloy)
		piece(root,Vector3(0,-.15,-.06),Vector3(.075,.2,.09),polymer,Vector3(-.25,0,0))
		piece(root,Vector3(-.15,-.06,-.14),Vector3(.13,.16,.24),metal(Color("4a4630"),.6))
		piece(root,Vector3(0,.13,-.12),Vector3(.035,.06,.24),polymer)
		barrel(root,Vector3(0,0,-.34),.085,.06,edge)
		barrel(root,Vector3(0,0,-.86),.082,.05,edge)
		var spin=Node3D.new();spin.name="Spin";spin.position=Vector3(0,0,-.6);root.add_child(spin)
		for i in range(6):
			var a=TAU*i/6.0
			barrel(spin,Vector3(cos(a)*.052,sin(a)*.052,0),.017,.62,edge)
		barrel(spin,Vector3.ZERO,.03,.6,polymer)
		load("res://scripts/mesh_batch.gd").merge(spin)
		return -.92
	if index==4:
		var olive=metal(Color("3d4436"),.62);olive.metallic=.1
		barrel(root,Vector3(0,.04,-.28),.088,1.15,olive)
		cone(root,Vector3(0,.04,-.9),.115,.088,.12,olive)
		cone(root,Vector3(0,.04,.33),.088,.11,.08,olive)
		ring(root,Vector3(0,.04,-.62),.094,.012,edge)
		ring(root,Vector3(0,.04,.05),.094,.012,edge)
		cone(root,Vector3(0,.04,-.83),.0,.06,.12,glow(Color("ff5a2a"),3.0))
		piece(root,Vector3(0,-.12,-.12),Vector3(.07,.2,.09),polymer,Vector3(-.25,0,0))
		piece(root,Vector3(0,-.09,-.42),Vector3(.06,.15,.08),polymer,Vector3(-.15,0,0))
		piece(root,Vector3(-.11,.13,-.3),Vector3(.05,.08,.16),polymer)
		piece(root,Vector3(-.11,.13,-.39),Vector3(.04,.05,.015),glow(Color("ff3020"),2.0))
		return -.98
	if index==5:
		var ceramic=metal(Color("d9dde0"),.32);ceramic.metallic=.1
		var cyan=glow(Color("6ff4ff"),3.2)
		piece(root,Vector3(0,.01,-.18),Vector3(.1,.13,.42),ceramic)
		piece(root,Vector3(0,-.13,-.07),Vector3(.075,.2,.09),polymer,Vector3(-.25,0,0))
		piece(root,Vector3(0,.0,.12),Vector3(.08,.11,.2),polymer)
		barrel(root,Vector3(0,.02,-.55),.03,.5,edge)
		for i in range(4): ring(root,Vector3(0,.02,-.38-i*.09),.058,.016,cyan)
		piece(root,Vector3(0,.075,-.18),Vector3(.02,.012,.38),cyan)
		cone(root,Vector3(0,.02,-.84),.0,.045,.09,cyan,4)
		piece(root,Vector3(0,.1,-.2),Vector3(.045,.04,.12),polymer)
		return -.86
	# Quad blaster: chunky retro sidearm-carbine with twin barrels.
	var copper=metal(Color("8a4d2c"),.4)
	var orange=glow(Color("ff6a3d"),2.6)
	var body=MeshInstance3D.new();var sphere=SphereMesh.new();sphere.radius=.5;sphere.height=1;sphere.radial_segments=16;sphere.rings=8
	body.mesh=sphere;body.material_override=alloy;body.position=Vector3(0,.02,-.2);body.scale=Vector3(.17,.15,.38);root.add_child(body)
	piece(root,Vector3(0,-.13,-.06),Vector3(.075,.2,.09),polymer,Vector3(-.25,0,0))
	for x in [-.05,.05]:
		barrel(root,Vector3(x,.03,-.48),.024,.36,copper)
		barrel(root,Vector3(x,.03,-.66),.03,.04,orange)
	piece(root,Vector3(0,.11,-.2),Vector3(.13,.02,.26),orange)
	for z in [-.12,-.22,-.32]: piece(root,Vector3(0,.02,z),Vector3(.18,.035,.03),copper)
	piece(root,Vector3(0,.0,.04),Vector3(.09,.12,.1),polymer)
	return -.68

# Two-handed greatsword: grip at the origin, blade along -Z.
static func build_sword(root: Node3D) -> void:
	clear(root)
	var steel=metal(Color("aeb6bb"),.18);steel.metallic=.92
	var dark=metal(Color("1c2226"),.5)
	var leather=metal(Color("2c211b"),.85);leather.metallic=.0
	var rune=glow(Color("8fb8ff"),3.6)
	piece(root,Vector3(0,0,-.78),Vector3(.15,.03,1.26),steel)
	var tip=cone(root,Vector3(0,0,-1.51),0.0,.106,.2,steel,4);tip.scale=Vector3(1,1,.3)
	piece(root,Vector3(0,.0165,-.74),Vector3(.022,.005,1.1),rune)
	piece(root,Vector3(0,-.0165,-.74),Vector3(.022,.005,1.1),rune)
	for side in [-1,1]: piece(root,Vector3(side*.077,0,-.78),Vector3(.006,.012,1.26),rune)
	piece(root,Vector3(0,0,-.13),Vector3(.38,.05,.06),dark)
	for x in [-.19,.19]: piece(root,Vector3(x,0,-.15),Vector3(.04,.07,.1),steel)
	barrel(root,Vector3(0,0,.04),.024,.3,leather)
	var pommel=MeshInstance3D.new();var sphere=SphereMesh.new();sphere.radius=.045;sphere.height=.09;sphere.radial_segments=10;sphere.rings=5
	pommel.mesh=sphere;pommel.material_override=dark;pommel.position=Vector3(0,0,.21);root.add_child(pommel)
