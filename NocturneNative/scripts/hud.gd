class_name NRHud
extends Control

var game: Node
var panel: Control
var hit_time: float = 0
var hurt_time: float = 0
var message: String = ""
var message_time: float = 0
var movement_finger: int = -1
var look_finger: int = -1
var fire_finger: int = -1
var stick_vector: Vector2 = Vector2.ZERO
var finger_actions: Dictionary = {}
var font: Font
var swap_finger: int = -1
var swap_pressed_at: int = 0
var wheel_open: bool = false
var wheel_hover: int = -1
const ARSENAL = preload("res://scripts/arsenal.gd")
var accent = Color("d1ff80")

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	font = ThemeDB.fallback_font
	process_mode = Node.PROCESS_MODE_ALWAYS

func wheel_points() -> Array:
	var out = []
	var centre = size * .5
	var n = ARSENAL.WEAPONS.size()
	for i in range(n):
		var a = -PI * .5 + TAU * i / n
		out.append(centre + Vector2(cos(a), sin(a)) * minf(220, size.y * .33))
	return out

func wheel_index_at(pos: Vector2) -> int:
	var points = wheel_points()
	for i in range(points.size()):
		if pos.distance_to(points[i]) < 62: return i
	return -1

func open_wheel() -> void:
	if wheel_open or not game or game.mode != "playing": return
	wheel_open = true
	wheel_hover = -1
	Engine.time_scale = .2
	if game.sound: game.sound.play_effect("ui", 1.2)

func close_wheel(choice: int = -1) -> void:
	if not wheel_open: return
	wheel_open = false
	Engine.time_scale = 1.0
	if choice >= 0 and game and is_instance_valid(game.player):
		game.player.equip_weapon(ARSENAL.WEAPONS[choice].id)
		game.announce(ARSENAL.WEAPONS[choice].name)

func _process(delta: float) -> void:
	if swap_finger >= 0 and not wheel_open and Time.get_ticks_msec() - swap_pressed_at > 320:
		open_wheel()
	hit_time = maxf(0, hit_time-delta)
	hurt_time = maxf(0, hurt_time-delta)
	message_time = maxf(0, message_time-delta)
	queue_redraw()

func safe_margins() -> Vector2:
	# Keeps controls clear of the Dynamic Island / rounded corners in landscape.
	var window = Vector2(DisplayServer.window_get_size())
	if window.x <= 0: return Vector2.ZERO
	var safe = DisplayServer.get_display_safe_area()
	var ratio = size.x / window.x
	var left = maxf(0, safe.position.x) * ratio
	var right = maxf(0, window.x - safe.end.x) * ratio
	return Vector2(minf(left, 90), minf(right, 90))

func controls() -> Dictionary:
	var m = safe_margins()
	var w = size.x - m.y
	var h = size.y
	var l = m.x
	return {"move":Vector2(l+120,h-185),"fire":Vector2(w-108,h-190),"blade":Vector2(w-248,h-247),"dodge":Vector2(w-253,h-135),"reload":Vector2(w-112,h-325),"swap":Vector2(w-170,h-37),"pause":Vector2(w-45,42),"jump":Vector2(w-385,h-160),"radio":Vector2(w-102,42),"interact":Vector2(size.x*.5,h-90),"heal":Vector2(l+262,h-92)}

func _draw() -> void:
	if not game or not is_instance_valid(game.player) or game.mode == "menu":
		return
	var p: NRPlayer = game.player
	var w = size.x
	var h = size.y
	draw_rect(Rect2(0,0,w,83),Color(0.025,.05,.08,.48))
	write("N /",Vector2(30,44),32,accent)
	write("0%d  ·  %s" % [game.stage+1,game.stage_names[game.stage]],Vector2(108,42),20)
	write("WAVE %d / %d     •     %d HOSTILES" % [game.wave,game.wave_counts[game.stage],game.enemies.size()],Vector2(31,73),15,Color("b3c6d1"))
	write(game.objectives[game.stage],Vector2(30,112),18,Color("d4dedf"))
	draw_rect(Rect2(30,h-50,180,7),Color("263740"))
	draw_rect(Rect2(30,h-50,180*maxf(0,p.health/p.max_health),7),accent)
	write("VITALS  %03d" % int(maxf(p.health,0)),Vector2(30,h-65),16)
	write("%d ELIMINATED" % game.kills,Vector2(30,h-20),13,Color("afbdc7"))
	var cw = p.current()
	var ammo_text = ("VENTING" if cw.mode == "beam" else "RELOADING") if p.reload_time > 0 else ("CHARGE %d%%" % p.ammo if cw.mode == "beam" else "%02d / ∞" % p.ammo)
	var m = safe_margins()
	write(cw.name,Vector2(w-260-m.y,h-66),16,Color("cdd8db"))
	if p.weapons.size() > 1:
		write("NEXT: "+p.weapons[(p.weapon_index+1)%p.weapons.size()].name.split(" / ")[1],Vector2(w-260-m.y,h-88),11,Color("8195a0"))
	var center = size/2
	var cross_color = accent if is_instance_valid(p.aim_target) else Color("ecf1f2")
	draw_line(center+Vector2(-11,0),center+Vector2(-4,0),cross_color,1.5)
	draw_line(center+Vector2(4,0),center+Vector2(11,0),cross_color,1.5)
	draw_line(center+Vector2(0,-11),center+Vector2(0,-4),cross_color,1.5)
	draw_line(center+Vector2(0,4),center+Vector2(0,11),cross_color,1.5)
	if hit_time > 0:
		for x in [-1,1]:
			for y in [-1,1]:
				draw_line(center+Vector2(x*13,y*13),center+Vector2(x*20,y*20),accent,2)
	if game.graphics.diagnostics:
		write("%.0f FPS  |  3D %d%%  |  %s" % [game.graphics.measured_fps,int(game.graphics.scale*100),game.graphics.NAMES[game.graphics.profile]],Vector2(w*.5-170,h-18),13,accent)
	var c = controls()
	if game.objective_pending:
		circle_button(c.interact,34,"USE")
		center_write(game.objective_actions[game.stage],Vector2(w*.5,h-145),17,accent)
		var meters=int(p.global_position.distance_to(game.world.objective_position))
		center_write(str(meters)+" m / F or USE",Vector2(w*.5,h-121),13,accent)

	draw_circle(c.move,66,Color(.04,.08,.11,.4))
	draw_arc(c.move,66,0,TAU,48,Color(.7,.85,.9,.3),1.5)
	draw_circle(c.move+stick_vector*44,25,Color(.7,.85,.9,.25))
	write("MOVE",c.move+Vector2(-25,91),13,Color("9cb2bf"))
	circle_button(c.fire,52,"FIRE",true,p.reload_time<=0)
	circle_button(c.blade,37,"SWORD" if p.melee_step == 0 else "COMBO %d" % p.melee_step,p.melee_step > 0,p.blade_cooldown<=0)
	circle_button(c.dodge,37,"ROLL" if p.is_on_floor() else "DASH",false,p.dodge_cooldown<=0)
	circle_button(c.heal,30,"FLASK %d" % p.flasks,p.drinking > 0,p.flasks > 0)
	circle_button(c.reload,30,"RELOAD",false,p.reload_time<=0)
	write(ammo_text,c.swap+Vector2(-70,6),20,accent)
	write("⇄",c.swap+Vector2(94,6),25)
	circle_button(c.pause,22,"Ⅱ")
	circle_button(c.radio,22,"♫")
	circle_button(c.jump,37,"JUMP",false,true)
	write("HOLD ⇄ FOR WEAPON WHEEL",c.swap+Vector2(-90,-108),10,Color(.7,.8,.85,.35))
	if message_time > 0:
		center_write(message,Vector2(w*.5,h*.24),23,accent)
	for e in game.enemies:
		if e.kind == "boss":
			center_write(game.boss_names[game.stage] + (" / OVERDRIVE" if e.phase_two else ""),Vector2(w*.5,35),16,Color("ff9d84"))
			draw_rect(Rect2(w*.33,47,w*.34,6),Color("2b3239"))
			draw_rect(Rect2(w*.33,47,w*.34*maxf(0,e.health/e.max_health),6),Color("f47f6c"))
	if hurt_time > 0:
		draw_rect(Rect2(Vector2.ZERO,size),Color(.7,.08,.06,hurt_time*.48))
	if game.mode == "playing":
		write("SWIPE TO LOOK",Vector2(w*.57,h*.76),12,Color(.7,.8,.85,.4))
	if wheel_open:
		draw_rect(Rect2(Vector2.ZERO,size),Color(0,0,0,.45))
		var points = wheel_points()
		center_write("SELECT WEAPON",size*.5+Vector2(0,-6),20,accent)
		center_write("tap outside to cancel",size*.5+Vector2(0,20),12,Color(.75,.82,.86,.7))
		for i in range(points.size()):
			var wdef = ARSENAL.WEAPONS[i]
			var carried = false
			for owned in p.weapons: if owned.id == wdef.id: carried = true
			var active = p.current().id == wdef.id
			var r = 58.0 if i == wheel_hover else 52.0
			draw_circle(points[i],r,Color(.12,.2,.17,.92) if active else Color(.03,.06,.09,.88))
			draw_arc(points[i],r,0,TAU,40,accent if (active or i == wheel_hover) else (Color(.7,.85,.9,.7) if carried else Color(.5,.6,.65,.35)),2.0)
			draw_circle(points[i]+Vector2(0,-22),5,wdef.color)
			var label = wdef.name.split(" / ")[1]
			center_write(label,points[i]+Vector2(0,4),13,Color.WHITE)
			center_write(wdef.name.split(" / ")[0],points[i]+Vector2(0,22),10,Color(.7,.8,.85,.8))

func write(text: String, pos: Vector2, point_size: int = 18, color: Color = Color.WHITE) -> void:
	draw_string(font,pos,text,HORIZONTAL_ALIGNMENT_LEFT,-1,point_size,color)

func center_write(text: String, pos: Vector2, point_size: int, color: Color) -> void:
	var width = font.get_string_size(text,HORIZONTAL_ALIGNMENT_LEFT,-1,point_size).x
	write(text,pos-Vector2(width*.5,0),point_size,color)

func circle_button(pos: Vector2, radius: float, text: String, main: bool = false, ready: bool = true) -> void:
	draw_circle(pos,radius,Color(.15,.23,.2,.65) if main else Color(.04,.075,.105,.65))
	draw_arc(pos,radius,0,TAU,40,accent if main else Color(.7,.82,.88,.45 if ready else .15),1.5)
	center_write(text,pos+Vector2(0,5),17 if main else 13,Color.WHITE if ready else Color("61707b"))

func reset_controls() -> void:
	swap_finger = -1
	if wheel_open:
		wheel_open = false
		Engine.time_scale = 1.0
	movement_finger = -1
	look_finger = -1
	fire_finger = -1
	finger_actions.clear()
	stick_vector = Vector2.ZERO
	if game and is_instance_valid(game.player):
		game.player.move_input = Vector2.ZERO
		game.player.fire_input = false
	for action in ["fire","forward","back","left","right"]:
		Input.action_release(action)

func _input(event: InputEvent) -> void:
	if not game or game.mode != "playing":
		return
	var p: NRPlayer = game.player
	if wheel_open:
		if event is InputEventScreenDrag and event.index == swap_finger:
			wheel_hover = wheel_index_at(event.position)
		elif event is InputEventScreenTouch:
			var index = wheel_index_at(event.position)
			if not event.pressed and event.index == swap_finger:
				swap_finger = -1
				finger_actions.erase(event.index)
				if index >= 0: close_wheel(index)
			elif event.pressed:
				close_wheel(index)
		elif event is InputEventKey and event.pressed and event.keycode == KEY_TAB:
			close_wheel()
		get_viewport().set_input_as_handled()
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_TAB:
			open_wheel()
		elif event.keycode >= KEY_1 and event.keycode <= KEY_7:
			p.equip_weapon(ARSENAL.WEAPONS[event.keycode - KEY_1].id)
	if event is InputEventMouseMotion and event.button_mask & MOUSE_BUTTON_MASK_RIGHT:
		p.look(event.relative)
		get_viewport().set_input_as_handled()
	if event is InputEventScreenTouch:
		if not event.pressed:
			if event.index == movement_finger:
				movement_finger = -1
				stick_vector = Vector2.ZERO
				p.move_input = Vector2.ZERO
			if event.index == look_finger:
				look_finger = -1
			if event.index == fire_finger:
				fire_finger = -1
				p.fire_input = false
			if event.index == swap_finger:
				swap_finger = -1
				p.swap_weapon()
			finger_actions.erase(event.index)
			return
		var c = controls()
		for action in ["fire","blade","dodge","jump","reload","swap","pause","radio","interact","heal"]:
			if action=="interact" and not game.objective_pending:continue
			var radius: float = 66 if action == "fire" else (100 if action == "swap" else (32 if action in ["pause","radio"] else 45))
			if event.position.distance_to(c[action]) < radius:
				finger_actions[event.index] = action
				if action == "fire":
					fire_finger = event.index
					p.fire_input = true
				elif action == "blade": p.blade()
				elif action == "dodge": p.dodge()
				elif action == "heal": p.drink_flask()
				elif action == "reload": p.reload_weapon()
				elif action == "swap":
					swap_finger = event.index
					swap_pressed_at = Time.get_ticks_msec()
				elif action == "jump": p.jump()
				elif action == "radio": game.sound.radio_next(); game.announce("♫  " + game.sound.now_playing_title())
				elif action == "pause": game.pause_game()
				elif action == "interact": game.interact_objective()
				get_viewport().set_input_as_handled()
				return
		if event.position.x < size.x*.4 and event.position.y > size.y*.45 and movement_finger == -1:
			movement_finger = event.index
			stick_vector = ((event.position-c.move)/60).limit_length()
			p.move_input = stick_vector
		elif look_finger == -1:
			look_finger = event.index
	elif event is InputEventScreenDrag:
		if event.index == movement_finger:
			stick_vector = ((event.position-controls().move)/60).limit_length()
			p.move_input = stick_vector
		elif event.index == look_finger or event.index == fire_finger:
			p.look(event.relative)

func close_panel() -> void:
	if is_instance_valid(panel):
		panel.queue_free()
		panel = null

func show_panel(kicker: String, title: String, body: String, buttons: Array, columns: int = 1) -> void:
	close_panel()
	reset_controls()
	if game and game.sound: game.sound.play_effect("ui")
	var centre = CenterContainer.new()
	centre.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(centre)
	centre.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	panel = centre
	var box = PanelContainer.new()
	centre.add_child(box)
	box.custom_minimum_size = Vector2(620 if columns > 1 else 560,0)
	if columns == 3: box.custom_minimum_size.x = 520
	var style = StyleBoxFlat.new()
	style.bg_color = Color(.035,.065,.09,.97)
	style.border_color = Color("435962")
	style.set_border_width_all(1)
	style.content_margin_left = 30
	style.content_margin_right = 30
	style.content_margin_top = 26
	style.content_margin_bottom = 26
	box.add_theme_stylebox_override("panel",style)
	var column = VBoxContainer.new()
	column.add_theme_constant_override("separation",12)
	box.add_child(column)
	var sub = Label.new()
	sub.text = kicker
	sub.add_theme_color_override("font_color",accent)
	sub.add_theme_font_size_override("font_size",15)
	column.add_child(sub)
	var heading = Label.new()
	heading.text = title
	heading.add_theme_font_size_override("font_size",34)
	column.add_child(heading)
	var desc = Label.new()
	desc.text = body
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	desc.custom_minimum_size = Vector2(500 if columns == 1 else 560,40)
	desc.add_theme_color_override("font_color",Color("b7cbd5"))
	desc.add_theme_font_size_override("font_size",17)
	column.add_child(desc)
	var holder: Container = column
	if columns > 1:
		var grid = GridContainer.new()
		grid.columns = columns
		grid.add_theme_constant_override("h_separation",10)
		grid.add_theme_constant_override("v_separation",10)
		column.add_child(grid)
		holder = grid
	for entry in buttons:
		var button = Button.new()
		button.text = entry[0]
		button.custom_minimum_size = Vector2([0,275,270][clampi(columns-1,0,2)] if entry[0].length() > 2 else 70, 46 if columns < 3 else 40)
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.clip_text = true
		button.add_theme_font_size_override("font_size",16 if columns > 1 else 18)
		var button_style = StyleBoxFlat.new()
		button_style.bg_color = accent
		button.add_theme_stylebox_override("normal",button_style)
		button.add_theme_color_override("font_color",Color("0b1c1a"))
		var pressed_style = button_style.duplicate()
		pressed_style.bg_color = accent.darkened(.25)
		button.add_theme_stylebox_override("pressed",pressed_style)
		button.add_theme_stylebox_override("hover",button_style)
		button.add_theme_stylebox_override("focus",StyleBoxEmpty.new())
		button.pressed.connect(entry[1])
		holder.add_child(button)
