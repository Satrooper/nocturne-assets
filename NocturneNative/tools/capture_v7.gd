extends SceneTree
# v7 pass 1 gameplay captures: Mixamo motion on the player and enemies.
var out="user://"
var game
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
	game.start_stage(4)
	var p=game.player; p.invulnerability=999
	await wait(1.2)
	for e in game.enemies: e.set_physics_process(false)
	# side-ish camera so the body motion reads
	p.yaw=p.visual.rotation.y+1.1; p.pitch=-.12
	p.move_input=Vector2(0,-1); await wait(.6); await cap("v7-01-run")
	p.move_input=Vector2.ZERO; await wait(.4)
	p.blade_cooldown=0; p.blade(); await wait(.17); await cap("v7-02-slash")
	await wait(.25); p.blade(); await wait(.25); p.blade(); await wait(.36); await cap("v7-03-slam")
	await wait(1.2)
	p.dodge_cooldown=0; p.move_input=Vector2(1,0); p.dodge(); await wait(.2); await cap("v7-04-roll")
	p.move_input=Vector2.ZERO; await wait(1.0)
	p.yaw=p.visual.rotation.y+.6
	p.fire_input=true; p.move_input=Vector2(-1,0); await wait(.5); await cap("v7-05-aim-strafe")
	p.fire_input=false; p.move_input=Vector2.ZERO
	var e=game.enemies[0] if game.enemies.size()>0 else null
	if e:
		p.global_position=e.global_position+Vector3(0,0,4); p.yaw=0; p.pitch=-.1
		await wait(.3); e.take_damage(9999); await wait(.55); await cap("v7-06-enemy-death")
	quit()
