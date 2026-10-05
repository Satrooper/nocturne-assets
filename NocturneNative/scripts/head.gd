extends RefCounted
# Procedurally sculpted human head. Units: metres. Origin = top of neck (Mixamo Head
# bone), +Y up, face toward -Z. Built from a deformed ellipsoid with sculpted
# features, separate eyes/ears/brows, and extruded beard and hair shells.
#
# style keys: skin, hair, beard (Color), hair_style ("curly","buzz","slick","none"),
# beard_style ("full","stubble","none"), detail (1 = player quality, 0 = enemy LOD),
# jaw (width 0.8-1.2), nose (size 0.8-1.3), seed.

const PLAYER = {"skin":Color("7a5646"),"hair":Color("1a1412"),"beard":Color("2a1e19"),"lips":Color("634038"),
	"hair_style":"curly","beard_style":"full","detail":1,"jaw":1.1,"nose":1.2,"cheek":1.1,"seed":7}

static var noise_cache: Dictionary = {}
static var head_cache: Dictionary = {}
static var flat_cache: Dictionary = {}

static func g(x: float, y: float, x0: float, y0: float, sx: float, sy: float) -> float:
	return exp(-((x-x0)*(x-x0))/(2.0*sx*sx) - ((y-y0)*(y-y0))/(2.0*sy*sy))

# Signed forward displacement (negative z = toward the viewer) of facial features.
static func features(x: float, y: float, st: Dictionary) -> float:
	var ax = absf(x)
	var nose = st.get("nose",1.0)
	var d = 0.0
	# Nose: bridge -> tip -> nostrils.
	var ridge = exp(-(x*x)/(2.0*pow(.0085*nose,2))) * smoothstep(.104, .05, y) * smoothstep(.028, .046, y)
	d -= ridge * .021 * nose
	d -= g(x,y,0,.047,.0105*nose,.0085) * .011 * nose
	d -= g(ax,y,.0125*nose,.039,.007,.005) * .006
	# Eye sockets, brow ridge, cheekbones.
	d += g(ax,y,.033,.083,.014,.0085) * .0095
	d -= g(ax,y,.031,.099,.024,.0065) * .0055
	d -= g(ax,y,.052,.058,.016,.016) * .0065 * st.get("cheek",1.0)
	# Philtrum, lips and the line between them; chin.
	d -= g(x,y,0,.034,.006,.006) * .002
	d -= g(x,y,0,.0265,.019,.0055) * .0068
	d -= g(x,y,0,.0145,.016,.005) * .0058
	d += g(x,y,0,.0205,.021,.0013) * .0032
	d += g(ax,y,.024,.02,.004,.006) * .002
	d -= g(x,y,0,-.006,.019,.014) * .0085
	return d

static func lip_weight(x: float, y: float) -> float:
	return clampf(g(x,y,0,.0265,.017,.0042) + g(x,y,0,.0148,.015,.004), 0, 1)

static func head_point(d: Vector3, st: Dictionary) -> Vector3:
	var c = Vector3(0,.075,0)
	var p = c + Vector3(d.x*.0765, d.y*.113, d.z*.099)
	# Jaw taper below the cheekbones; thin the back of the jaw into the neck.
	var k = smoothstep(.055, -.045, p.y)
	var jaw = st.get("jaw",1.0)
	p.x *= 1.0 - .34*k/jaw
	if p.z > 0: p.z *= 1.0 - .6*k
	else: p.z *= 1.0 - .06*k
	# Slightly flatter cheeks/temples so the face reads as a plane, rounder crown.
	var front = clampf(-d.z, 0, 1)
	p.x *= 1.0 - .05*front*smoothstep(.04,.12,p.y)
	p.z += features(p.x, p.y, st) * front * front
	return p

static func noise3(seed_value: int, freq: float) -> FastNoiseLite:
	var key = str(seed_value)+":"+str(freq)
	if noise_cache.has(key): return noise_cache[key]
	var n = FastNoiseLite.new()
	n.seed = seed_value; n.frequency = freq; n.fractal_octaves = 3
	noise_cache[key] = n
	return n

static func material(color: Color, rough: float, normal_noise: float, normal_strength: float, rim: float = 0.0) -> StandardMaterial3D:
	var m = StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = rough
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	if normal_noise > 0:
		var tex = NoiseTexture2D.new()
		tex.width = 256; tex.height = 256; tex.seamless = true; tex.as_normal_map = true
		tex.bump_strength = 6.0
		var fn = FastNoiseLite.new(); fn.frequency = normal_noise; fn.noise_type = FastNoiseLite.TYPE_CELLULAR if normal_noise > .05 else FastNoiseLite.TYPE_SIMPLEX
		tex.noise = fn
		m.normal_enabled = true; m.normal_texture = tex; m.normal_scale = normal_strength
		m.uv1_triplanar = true; m.uv1_scale = Vector3.ONE * 18.0
	if rim > 0:
		m.rim_enabled = true; m.rim = rim; m.rim_tint = .6
	return m

static func build(st: Dictionary) -> Node3D:
	var key = str(st)
	if not head_cache.has(key):
		var made = _build(st)
		var batch = load("res://scripts/mesh_batch.gd")
		for child in made.get_children():
			if child.get_child_count() > 0:
				batch.merge(child)
		batch.merge(made)
		head_cache[key] = made
	return head_cache[key].duplicate()

static func _build(st: Dictionary) -> Node3D:
	var root = Node3D.new()
	root.name = "SculptedHead"
	var hi = int(st.get("detail",1)) >= 1
	var rings = 46 if hi else 22
	var segs = 64 if hi else 30
	var skin_col: Color = st.skin
	var lips_col: Color = st.get("lips", skin_col.darkened(.25))
	# --- skin ------------------------------------------------------------
	var grid = []
	for i in range(rings+1):
		var row = []
		var th = PI * i / rings
		for j in range(segs+1):
			var ph = TAU * j / segs
			var d = Vector3(sin(th)*sin(ph), cos(th), -sin(th)*cos(ph))
			row.append([d, head_point(d, st)])
		grid.append(row)
	var st_skin = SurfaceTool.new()
	st_skin.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(rings):
		for j in range(segs):
			for q in [[i,j],[i+1,j],[i+1,j+1],[i,j],[i+1,j+1],[i,j+1]]:
				var v = grid[q[0]][q[1]]
				var p: Vector3 = v[1]
				var lip = lip_weight(p.x, p.y) * clampf(-v[0].z*2.0,0,1)
				var blush = g(absf(p.x),p.y,.045,.055,.02,.02)*clampf(-v[0].z,0,1)*.12
				var c = skin_col.lerp(lips_col, lip)
				c = c.lerp(Color(c.r*1.08,c.g*.9,c.b*.88), blush)
				if st.get("beard_style","none") != "none":
					var shadow = beard_mask(p, v[0]) * (.45 if st.beard_style == "stubble" else .3)
					c = c.lerp(st.get("beard",Color.BLACK), shadow)
				st_skin.set_color(c)
				st_skin.set_uv(Vector2(float(q[1])/segs, float(q[0])/rings))
				st_skin.add_vertex(p)
	st_skin.generate_normals()
	var skin_mesh = st_skin.commit()
	var skin_mat = material(Color.WHITE, .5, .09 if hi else 0.0, .25, .18)
	skin_mat.backlight_enabled = hi
	skin_mat.backlight = Color(.45,.15,.1)
	add_mesh(root, skin_mesh, skin_mat)
	# Neck and ears.
	var neck = MeshInstance3D.new()
	var cyl = CylinderMesh.new(); cyl.top_radius = .047; cyl.bottom_radius = .056; cyl.height = .13; cyl.radial_segments = 20 if hi else 10
	neck.mesh = cyl; neck.position = Vector3(0,-.03,.016)
	neck.material_override = flat(skin_col.darkened(.06), .55)
	root.add_child(neck)
	for side in [-1,1]:
		var ear = MeshInstance3D.new()
		var s = SphereMesh.new(); s.radius = .5; s.height = 1.0; s.radial_segments = 14 if hi else 8; s.rings = 8 if hi else 4
		ear.mesh = s; ear.scale = Vector3(.024,.06,.04)
		ear.position = Vector3(side*.0745,.074,.012); ear.rotation = Vector3(0, side*.35, side*-.12)
		ear.material_override = flat(skin_col.darkened(.04), .55)
		root.add_child(ear)
	# --- eyes, lids, brows ----------------------------------------------
	for side in ([-1,1] if st.get("eyes",true) else []):
		var eye_c = Vector3(side*.0325, .0835, 0)
		eye_c.z = head_point(dir_toward(Vector3(side*.0325,.0835,-.2)), st).z + .0085
		sphere(root, eye_c, Vector3.ONE*.0122, flat(Color("e9e1d6"), .12))
		sphere(root, eye_c+Vector3(side*-.0008,0,-.0105), Vector3(.0062,.0062,.0026), flat(Color("2b1a12"), .1))
		sphere(root, eye_c+Vector3(side*-.0008,0,-.0127), Vector3(.0027,.0027,.0008), flat(Color("050404"), .05))
		var lid = sphere(root, eye_c+Vector3(0,.0098,-.0025), Vector3(.0152,.0052,.0122), flat(skin_col.darkened(.15), .55))
		lid.rotation.z = side*.08
		sphere(root, eye_c+Vector3(0,-.0098,-.0025), Vector3(.0142,.0038,.0115), flat(skin_col.darkened(.06), .55))
		# Eyebrow: a thick arc of short slanted strands.
		var brow_mat = flat(st.get("beard", st.hair).darkened(.1), .8)
		var brow = Node3D.new(); root.add_child(brow)
		for k in range(9 if hi else 4):
			var t = float(k)/(8 if hi else 3)
			var bx = side*lerpf(.019,.053,t)
			var by = .0975 + sin(t*PI*.9)*.0045 - t*.004
			var bp = head_point(dir_toward(Vector3(bx,by,-.2)), st) + Vector3(0,0,-.0025)
			var hair_strip = sphere(brow, bp, Vector3(.0075,.0032 + (1.0-t)*.0016,.0028), brow_mat)
			hair_strip.rotation.z = side*(-.25 + t*.35)
	# --- beard -----------------------------------------------------------
	if st.get("beard_style","none") == "full":
		add_mesh(root, shell(grid, rings, segs, st, "beard"), hair_material(st.beard, hi))
	# --- hair ------------------------------------------------------------
	if st.get("hair_style","none") != "none":
		add_mesh(root, shell(grid, rings, segs, st, "hair"), hair_material(st.hair, hi))
		if st.hair_style == "curly" and hi:
			# Frizzy outer layer breaks up the silhouette like loose curls.
			var outer = st.duplicate(); outer["seed"] = int(st.get("seed",1)) + 40
			var fz = shell(grid, rings, segs, outer, "fuzz")
			add_mesh(root, fz, hair_material(st.hair.lightened(.04), hi))
	for child in root.get_children():
		if child is GeometryInstance3D: child.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return root

static func dir_toward(p: Vector3) -> Vector3:
	return ((p - Vector3(0,.075,0)) / Vector3(.0765,.113,.099)).normalized()

static func beard_mask(p: Vector3, d: Vector3) -> float:
	var ax = absf(p.x)
	var line = .033 + clampf((ax-.026)/.046, 0, 1) * .03    # cheek line rising to sideburns
	var m = smoothstep(line + .004, line - .006, p.y)
	m *= smoothstep(.05, .015, p.z)                              # not the back of the neck
	m *= 1.0 - smoothstep(-.06, -.075, p.y) * 0.0
	# Keep lips clear, but connect moustache to beard at the corners.
	var lips = g(p.x, p.y, 0, .0205, .018, .0075)
	m *= 1.0 - clampf(lips*1.4, 0, 1)
	m *= 1.0 - smoothstep(.034, .046, p.y) * (1.0 - smoothstep(.014, .02, ax))  # below the nose only
	return clampf(m, 0, 1)

static func hair_mask(p: Vector3, d: Vector3, st: Dictionary) -> float:
	var front = clampf(-d.z, -1, 1)
	var line = lerpf(.03, .128, clampf(front*.6 + .5, 0, 1)) + .006*smoothstep(.02,.05,absf(p.x))*clampf(front,0,1)
	var ears = g(absf(p.x), p.y, .075, .068, .02, .028)
	var m = smoothstep(line - .006, line + .006, p.y) * (1.0 - clampf(ears*1.6, 0, 1))
	if st.hair_style == "buzz" or st.hair_style == "slick": m *= smoothstep(line, line + .01, p.y)
	return m

static func shell(grid: Array, rings: int, segs: int, st: Dictionary, kind: String) -> ArrayMesh:
	var n = noise3(int(st.get("seed",1)) + (5 if kind == "hair" else 9), 38.0 if kind == "hair" else 70.0)
	var verts = []
	for i in range(rings+1):
		var row = []
		for j in range(segs+1):
			var d: Vector3 = grid[i][j][0]
			var p: Vector3 = grid[i][j][1]
			var normal = (p - Vector3(0,.075,0)).normalized()
			var m: float
			var off: float
			if kind == "fuzz":
				m = hair_mask(p, d, st) * smoothstep(.05, .12, p.y)
				var top2 = smoothstep(.09, .19, p.y)
				off = (.02 + .038*top2 + absf(noise3(int(st.get("seed",1)), 18.0).get_noise_3dv(p))*.03) * m
				m *= .55 + noise3(int(st.get("seed",1)) + 2, 60.0).get_noise_3dv(p)*.9
			elif kind == "beard":
				m = beard_mask(p, d)
				off = (.0035 + .0075*m) + n.get_noise_3dv(p*1.0)*.0018
				off += g(absf(p.x),p.y,.0,-.03,.03,.02)*.004   # fuller at the chin
			else:
				m = hair_mask(p, d, st)
				var top = smoothstep(.09, .19, p.y)
				var vol = {"curly":.03,"buzz":.003,"slick":.008}[st.hair_style]
				var clumps = 0.0
				if st.hair_style == "curly":
					clumps = absf(noise3(int(st.get("seed",1)) + 3, 22.0).get_noise_3dv(p))*.022 + n.get_noise_3dv(p)*.006
				off = (.007 + vol*top + .006*clampf(-d.z,0,1)*top + clumps*(.4 + .6*top)) * m
			# Alpha for the cut-out edge: mask broken up with fine noise so edges look hairy.
			var fuzz = noise3(int(st.get("seed",1)) + 21, 160.0).get_noise_3dv(p)
			row.append([p + normal*off, m, m*1.25 + fuzz*.45 - .1])
		verts.append(row)
	var s = SurfaceTool.new()
	s.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(rings):
		for j in range(segs):
			var quad = [[i,j],[i+1,j],[i+1,j+1],[i,j],[i+1,j+1],[i,j+1]]
			var keep = false
			for q in quad:
				if verts[q[0]][q[1]][1] > .03: keep = true
			if not keep: continue
			for q in quad:
				var v = verts[q[0]][q[1]]
				s.set_color(Color(1,1,1,clampf(v[2], 0, 1)))
				s.add_vertex(v[0])
	s.generate_normals()
	return s.commit()

static func curls(grid: Array, rings: int, segs: int, st: Dictionary, count: int) -> ArrayMesh:
	var rng = RandomNumberGenerator.new(); rng.seed = int(st.get("seed",1))
	var s = SurfaceTool.new()
	s.begin(Mesh.PRIMITIVE_TRIANGLES)
	var ball = SphereMesh.new(); ball.radius = .5; ball.height = 1.0; ball.radial_segments = 8; ball.rings = 4
	var n = noise3(int(st.get("seed",1)) + 5, 38.0)
	var placed = 0
	var guard = 0
	while placed < count and guard < count * 30:
		guard += 1
		var i = rng.randi_range(0, rings/2)
		var j = rng.randi_range(0, segs)
		var d: Vector3 = grid[i][j][0]
		var p: Vector3 = grid[i][j][1]
		var m = hair_mask(p, d, st)
		if m < .7: continue
		var normal = (p - Vector3(0,.075,0)).normalized()
		var top = smoothstep(.09, .19, p.y)
		var off = (.006 + .036*top + .004*clampf(-d.z,0,1)*top) + n.get_noise_3dv(p)*.008
		var r = rng.randf_range(.0055, .0105) * (.75 + .45*top)
		# Flattened, elongated clumps lying along the scalp read as curls, not beads.
		var basis = Basis(Quaternion(Vector3.UP, normal)).rotated(normal, rng.randf()*TAU).scaled_local(Vector3(r*3.2, r*.9, r*1.6))
		s.append_from(ball, 0, Transform3D(basis, p + normal*(off - r*.55)))
		placed += 1
	s.generate_normals()
	var mesh = s.commit()
	return mesh

static func hair_material(color: Color, hi: bool) -> StandardMaterial3D:
	var m = material(color, .62, .55 if hi else 0.0, .9)
	m.vertex_color_use_as_albedo = true
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = .5
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.specular_mode = BaseMaterial3D.SPECULAR_SCHLICK_GGX
	return m

static func flat(color: Color, rough: float) -> StandardMaterial3D:
	var key = color.to_html() + str(rough)
	if flat_cache.has(key): return flat_cache[key]
	var m = StandardMaterial3D.new(); m.albedo_color = color; m.roughness = rough
	flat_cache[key] = m
	return m

static func sphere(parent: Node3D, p: Vector3, scale: Vector3, m: Material) -> MeshInstance3D:
	var node = MeshInstance3D.new()
	var s = SphereMesh.new(); s.radius = .5; s.height = 1.0; s.radial_segments = 12; s.rings = 6
	node.mesh = s; node.material_override = m; node.position = p; node.scale = scale * 2.0
	parent.add_child(node)
	return node

static func add_mesh(parent: Node3D, mesh: Mesh, m: Material) -> MeshInstance3D:
	var node = MeshInstance3D.new()
	node.mesh = mesh; node.material_override = m
	parent.add_child(node)
	return node
