extends SceneTree
# Bakes the healing-flask "drink" clip (v7). Our Mixamo set has no drinking clip, so the
# right arm is posed with a small two-bone IK solve at key moments (relaxed idle as base)
# and saved as a normal humanoid Animation that plays on every retargeted character.
var sk: Skeleton3D
func _initialize(): run.call_deferred()
func gpos(n: String) -> Vector3: return sk.get_bone_global_pose(sk.find_bone(n)).origin
func aim_bone(b: int, child_from: Vector3, child_to: Vector3) -> void:
	var g := sk.get_bone_global_pose(b)
	var d0 := (child_from - g.origin).normalized(); var d1 := (child_to - g.origin).normalized()
	var axis := d0.cross(d1)
	if axis.length() < 1e-5: return
	var q := Quaternion(axis.normalized(), d0.angle_to(d1))
	sk.set_bone_global_pose(b, Transform3D(Basis(q) * g.basis, g.origin))
func two_bone(side: String, target: Vector3, pole: Vector3) -> void:
	var u := sk.find_bone(side+"UpperArm"); var l := sk.find_bone(side+"LowerArm")
	var S := gpos(side+"UpperArm"); var E := gpos(side+"LowerArm"); var H := gpos(side+"Hand")
	var a := S.distance_to(E); var b := E.distance_to(H)
	var to_t := target - S; var d := clampf(to_t.length(), .05, a + b - .001); var dir := to_t.normalized()
	var x := (a*a - b*b + d*d) / (2.0*d); var h := sqrt(maxf(a*a - x*x, 0.0))
	var pdir := (pole - S); pdir = (pdir - dir * pdir.dot(dir)).normalized()
	var E2 := S + dir * x + pdir * h
	aim_bone(u, E, E2)
	var E3 := gpos(side+"LowerArm"); var H3 := gpos(side+"Hand")
	aim_bone(l, H3, S + dir * d)
func run():
	var s=load("res://assets/soldier.glb").instantiate(); root.add_child(s)
	var ap:AnimationPlayer=s.find_children("*","AnimationPlayer",true,false)[0]
	sk=s.find_children("*","Skeleton3D",true,false)[0]
	ap.play("Idle"); ap.seek(.3,true); await process_frame; ap.stop()
	var base={}
	for i in sk.get_bone_count(): base[i]=sk.get_bone_pose_rotation(i)
	var fwd := -Vector3.FORWARD * -1.0  # skeleton space: character faces -Z
	fwd = Vector3(0,0,-1)
	var head := gpos("Head")
	var mouth := head + fwd*.13 + Vector3(0,-.04,0) + Vector3(.02,0,0)
	var chest := gpos("UpperChest") + fwd*.28 + Vector3(.1,-.06,0)
	var pole := gpos("RightUpperArm") + Vector3(.35,-.5,.25)
	# key: [time, right-hand target (null = idle arm), head tilt back (rad)]
	var keys = [[0.0,null,0.0],[.30,chest,.04],[.52,mouth,.30],[.95,mouth,.36],[1.25,chest,.08],[1.5,null,0.0]]
	var bones = ["RightUpperArm","RightLowerArm","RightHand","Neck","Head"]
	var a := Animation.new(); a.length = 1.5
	var tr = {}
	for i in sk.get_bone_count():
		var t := a.add_track(Animation.TYPE_ROTATION_3D); a.track_set_path(t, "%GeneralSkeleton:" + sk.get_bone_name(i)); tr[sk.get_bone_name(i)] = t
		if not sk.get_bone_name(i) in bones: a.rotation_track_insert_key(t, 0, base[i])
	var hips_t := a.add_track(Animation.TYPE_POSITION_3D); a.track_set_path(hips_t, "%GeneralSkeleton:Hips"); a.position_track_insert_key(hips_t, 0, sk.get_bone_pose_position(sk.find_bone("Hips")))
	var err_max := 0.0
	for k in keys:
		for i in sk.get_bone_count(): sk.set_bone_pose_rotation(i, base[i])
		if k[1] != null:
			two_bone("Right", k[1], pole)
			err_max = maxf(err_max, gpos("RightHand").distance_to(k[1]))
			# palm toward the face
			var hb := sk.find_bone("RightHand"); var g := sk.get_bone_global_pose(hb)
			sk.set_bone_global_pose(hb, Transform3D(Basis(Vector3.UP, -.9) * Basis(Vector3.RIGHT, -.5) * g.basis, g.origin))
		for b in ["Neck","Head"]:
			var bi := sk.find_bone(b); var g := sk.get_bone_global_pose(bi)
			sk.set_bone_global_pose(bi, Transform3D(Basis(Vector3.RIGHT, -k[2] * (.4 if b=="Neck" else .6)) * g.basis, g.origin))
		for b in bones: a.rotation_track_insert_key(tr[b], k[0], sk.get_bone_pose_rotation(sk.find_bone(b)))
	print("SAVED ", ResourceSaver.save(a, "res://assets/anim/clips/drink.tres"), " ik_error_m=", snappedf(err_max, .001))
	quit()
