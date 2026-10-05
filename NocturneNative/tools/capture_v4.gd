extends SceneTree
var out="user://"
func _initialize():
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):out=arg.trim_prefix("--output=").trim_suffix("/")+"/"
	run.call_deferred()
func capture(name: String):
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out+name+".png")
	print("CAPTURED ",name," | draws ",Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME)," primitives ",Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
func run():
	var game=load("res://scenes/Main.tscn").instantiate()
	root.add_child(game)
	await process_frame
	game.graphics.adaptive=false
	game.graphics.choose(2)
	var names=["01-Neon-Underworld","02-Glass-Palace","03-Hollow-Bamboo","04-Ashworks","05-Black-Cathedral"]
	for index in range(5):
		game.start_stage(index)
		game.player.invulnerability=100
		game.player.weapon_index=1
		game.player.equip_model(1)
		game.player.ammo=30
		await create_timer(1.7).timeout
		game.hud.message_time=0
		await process_frame
		await process_frame
		await capture(names[index])
		for enemy in game.enemies:enemy.queue_free()
		game.enemies.clear()
		for bullet in game.projectiles:bullet.node.queue_free()
		game.projectiles.clear()
		await process_frame
		game.wave=game.wave_counts[index]
		game.player.position=Vector3(1,.1,3)
		game.player.yaw=.12
		var boss=game.spawn_enemy("boss",game.world.safe_spawn(Vector3(0,.1,-4)))
		boss.cooldown=10
		await create_timer(.8).timeout
		await capture("Boss-"+names[index])
	game.queue_free()
	await process_frame
	await process_frame
	NRWorld.materials.clear()
	quit()
