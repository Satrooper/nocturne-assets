extends SceneTree
var output_dir = "user://"
func _initialize():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output_dir = arg.trim_prefix("--output=").trim_suffix("/")+"/"
	run.call_deferred()
func snap(path: String):
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)
func run():
	var scene=load("res://scenes/Main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	scene.start_stage(0)
	await create_timer(3).timeout
	await snap(output_dir+"Northline-Upgrade.png")
	scene.player.position=Vector3(3,.05,12)
	scene.player.yaw=.35
	scene.player.weapon_index=1
	scene.player.equip_model(1)
	scene.player.ammo=30
	await create_timer(.65).timeout
	await snap(output_dir+"Northline-Street.png")
	scene.player.position=Vector3(7,.05,2)
	scene.player.yaw=-.65
	await create_timer(.5).timeout
	await snap(output_dir+"Northline-Rifle.png")
	scene.queue_free()
	await process_frame
	await process_frame
	NRWorld.materials.clear()
	quit()
