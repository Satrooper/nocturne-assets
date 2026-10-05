extends SkeletonModifier3D
var actor: Node
var spine: int=-1
func _ready() -> void:
	var skeleton=get_skeleton()
	for i in range(skeleton.get_bone_count()):
		if skeleton.get_bone_name(i).ends_with("UpperChest"):spine=i
func _process_modification() -> void:
	if not is_instance_valid(actor) or actor.dead or spine<0:return
	var skeleton=get_skeleton()
	var pitch: float=actor.aim_pitch
	var local_axis=skeleton.get_bone_global_pose(spine).basis.inverse()*Vector3.RIGHT
	var q=skeleton.get_bone_pose_rotation(spine)
	var twist: float=actor.get("melee_twist") if "melee_twist" in actor else 0.0
	# Faction stance: hunched runners, low shinobi, swaying cultists.
	pitch += float(actor.get_meta("posture", 0.0)) / .35
	var sway: float = float(actor.get_meta("sway", 0.0))
	if sway > 0: twist += sin(Time.get_ticks_msec() * .0021 + actor.get_instance_id()) * sway
	var up_axis=skeleton.get_bone_global_pose(spine).basis.inverse()*Vector3.UP
	skeleton.set_bone_pose_rotation(spine,q*Quaternion(local_axis.normalized(),pitch*.35-actor.weapon_kick*.35)*Quaternion(up_axis.normalized(),twist))
