extends RefCounted
# Merge rigid pieces sharing a material under a single moving mount. Skinned
# meshes are excluded; no skeleton, collision or attachment transforms change.
static func merge(root: Node3D) -> void:
	var groups: Dictionary={}
	for child in root.get_children():
		if not child is MeshInstance3D or child.skin!=null:continue
		for surface in range(child.mesh.get_surface_count()):
			var material=child.get_active_material(surface)
			if not material:continue
			var key=material.get_instance_id()
			if not groups.has(key):groups[key]={"material":material,"parts":[]}
			groups[key].parts.append([child,surface])
	var removed: Dictionary={}
	for entry in groups.values():
		if entry.parts.size()<2:continue
		var st=SurfaceTool.new();st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for part in entry.parts:
			st.append_from(part[0].mesh,part[1],part[0].transform)
			removed[part[0].get_instance_id()]=part[0]
		st.set_material(entry.material)
		var merged=MeshInstance3D.new();merged.mesh=st.commit();merged.name="BatchedDetail";root.add_child(merged)
	for child in removed.values():root.remove_child(child);child.queue_free()
