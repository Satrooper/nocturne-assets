extends SkeletonModifier3D
# Replaces the soldier's helmeted head with a sculpted head: the original head bone
# is collapsed, and the new head follows that bone's animated rotation.
var head_node: Node3D
var head_bone: int = -1
var correction: Basis = Basis.IDENTITY
var scale_factor: float = 1.0
var offset: Vector3 = Vector3(0, .045, -.008)

func setup(skeleton: Skeleton3D, node: Node3D, model_size: float, facing: Basis) -> void:
	head_node = node
	for i in range(skeleton.get_bone_count()):
		if skeleton.get_bone_name(i).ends_with("Head"): head_bone = i
	if head_bone < 0: return
	# Orientation that makes the sculpted head face the model's forward at rest.
	var rest: Transform3D = skeleton.get_bone_global_rest(head_bone)
	var skel_basis = skeleton.global_basis.orthonormalized()
	correction = rest.basis.orthonormalized().inverse() * skel_basis.inverse() * facing.orthonormalized()
	scale_factor = model_size

func _process_modification() -> void:
	if head_bone < 0 or not is_instance_valid(head_node): return
	var skeleton = get_skeleton()
	var pose: Transform3D = skeleton.get_bone_global_pose(head_bone)
	var basis = skeleton.global_basis.orthonormalized() * pose.basis.orthonormalized() * correction
	var origin = skeleton.global_transform * pose.origin
	head_node.global_transform = Transform3D(basis.scaled_local(Vector3.ONE * scale_factor), origin + basis * offset * scale_factor)
	skeleton.set_bone_pose_scale(head_bone, Vector3.ONE * .001)
