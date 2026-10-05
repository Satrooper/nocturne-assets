extends SceneTree
func _initialize(): run.call_deferred()
func run():
	var w=Node3D.new(); root.add_child(w)
	var env=WorldEnvironment.new(); env.environment=Environment.new(); env.environment.background_mode=Environment.BG_COLOR; env.environment.background_color=Color(.2,.22,.26); env.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR; env.environment.ambient_light_color=Color(.65,.65,.7); w.add_child(env)
	var sun=DirectionalLight3D.new(); sun.rotation_degrees=Vector3(-35,-60,0); w.add_child(sun)
	var cam=Camera3D.new(); cam.fov=28; cam.look_at_from_position(Vector3(0,1.3,7),Vector3(0,1.05,0)); w.add_child(cam)
	var lib=AnimationLibrary.new(); lib.add_animation("drink",load("res://assets/anim/clips/drink.tres"))
	var x=-2.6
	for tt in [0.0,.30,.52,.95,1.25]:
		var c=load("res://assets/soldier.glb").instantiate(); w.add_child(c); c.position.x=x; x+=1.3; c.rotation.y=-PI*.42
		var ap:AnimationPlayer=c.find_children("*","AnimationPlayer",true,false)[0]; ap.add_animation_library("d",lib); ap.play("d/drink"); ap.seek(tt,true); ap.pause()
	for i in 4: await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/home/claude/v7/drink.png"); quit()
