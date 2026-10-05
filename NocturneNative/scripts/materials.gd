extends RefCounted
static var cache: Dictionary = {}
static func scanned(asset: String,tint: Color=Color.WHITE,meters: float=2.0,rough: float=1.0,metal: float=0.0,wet: float=0.0) -> ShaderMaterial:
	var key=asset+str(tint)+str(meters)+str(rough)+str(metal)+str(wet)
	if cache.has(key):return cache[key]
	var m=ShaderMaterial.new()
	m.shader=load("res://assets/shaders/scanned_surface.gdshader")
	for pair in [["color_map","color"],["normal_map","normal"],["rough_map","rough"]]:
		m.set_shader_parameter(pair[0],load("res://assets/textures/pbr/"+asset+"_"+pair[1]+".jpg"))
	m.set_shader_parameter("tint",tint);m.set_shader_parameter("meters_per_tile",meters)
	m.set_shader_parameter("roughness_scale",rough);m.set_shader_parameter("metalness",metal);m.set_shader_parameter("wetness",wet)
	cache[key]=m
	return m
