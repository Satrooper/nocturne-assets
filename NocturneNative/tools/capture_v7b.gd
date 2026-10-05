extends SceneTree
var out="user://"; var game
func _initialize():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):out=arg.trim_prefix("--output=").trim_suffix("/")+"/"
	run.call_deferred()
func cap(name):
	game.hud.message_time=0
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out+name+".png"); print("CAPTURED ",name)
func wait(t): await create_timer(t).timeout
func run():
	game=load("res://scenes/Main.tscn").instantiate(); root.add_child(game)
	await process_frame
	game.graphics.adaptive=false; game.graphics.choose(2)
	game.start_stage(0)
	var p=game.player; p.invulnerability=999
	await wait(1.2)
	for e in game.enemies: e.set_physics_process(false)
	p.yaw=p.visual.rotation.y+1.3; p.pitch=-.1
	p.health=35; await wait(.2)
	p.drink_flask(); await wait(.72); await cap("v7-07-drink")
	await wait(1.0)
	p.dodge_cooldown=0; p.move_input=Vector2.ZERO; p.velocity=Vector3.ZERO; p.dodge(); await wait(.14); await cap("v7-08-backstep")
	quit()
