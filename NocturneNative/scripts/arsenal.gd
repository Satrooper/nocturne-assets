extends RefCounted
# All player firearms. mode: hitscan (instant rays), rocket (explosive projectile),
# bolt (visible plasma projectile), beam (continuous laser; capacity = charge %).
const WEAPONS: Array[Dictionary] = [
	{"id":"pistol","name":"V-9 / SIDEARM","model":0,"mode":"hitscan","capacity":12,"damage":35.0,"delay":.22,"pellets":1,"spread":.007,"reload":1.1,"recoil":.65,"sound":"pistol","color":Color("ffd295"),"grip":-.15,"push":.6,"move":1.0,
		"desc":"Precise semi-auto. Fast reload."},
	{"id":"rifle","name":"R-41 / ASSAULT","model":1,"mode":"hitscan","capacity":30,"damage":19.0,"delay":.10,"pellets":1,"spread":.018,"reload":1.25,"recoil":.32,"sound":"rifle","color":Color("ffd295"),"grip":-.44,"push":.6,"move":1.0,
		"desc":"Reliable full-auto rifle."},
	{"id":"shotgun","name":"BREACH / SHOTGUN","model":2,"mode":"hitscan","capacity":6,"damage":20.0,"delay":.72,"pellets":7,"spread":.07,"reload":1.8,"recoil":1.35,"sound":"shotgun","color":Color("ffc07a"),"grip":-.44,"push":2.8,"move":1.0,
		"desc":"Seven pellets. Devastating up close."},
	{"id":"mg","name":"RAVAGER / MINIGUN","model":3,"mode":"hitscan","capacity":150,"damage":13.0,"delay":.05,"pellets":1,"spread":.03,"reload":2.6,"recoil":.16,"sound":"mg","color":Color("ffe0a0"),"grip":-.50,"push":.45,"move":.68,
		"desc":"Rotary cannon. 20 rounds a second, slows you down."},
	{"id":"launcher","name":"HELLFIRE / LAUNCHER","model":4,"mode":"rocket","capacity":4,"damage":160.0,"delay":.85,"pellets":1,"spread":.0,"reload":2.2,"recoil":1.8,"sound":"rocket","color":Color("ff9a4a"),"grip":-.42,"push":6.0,"move":.9,
		"radius":4.0,"speed":34.0,"desc":"Explosive rockets. Area damage clears crowds."},
	{"id":"laser","name":"ARC / BEAM LASER","model":5,"mode":"beam","capacity":100,"damage":105.0,"delay":0.0,"pellets":1,"spread":.0,"reload":1.6,"recoil":.0,"sound":"laser_loop","color":Color("6ff4ff"),"grip":-.40,"push":.12,"move":.85,
		"drain":26.0,"desc":"Continuous beam. Melts targets; vents when empty."},
	{"id":"blaster","name":"QUAD / STAR BLASTER","model":6,"mode":"bolt","capacity":40,"damage":24.0,"delay":.095,"pellets":1,"spread":.008,"reload":1.3,"recoil":.38,"sound":"blaster","color":Color("ff6a3d"),"grip":-.30,"push":.9,"move":1.0,
		"speed":70.0,"homing":5.0,"desc":"Twin-barrel plasma bolts that curve onto targets."},
]
const DEFAULT_LOADOUT: Array[String] = ["pistol","rifle","launcher"]
const MAX_LOADOUT := 3

static func find(id: String) -> Dictionary:
	for w in WEAPONS:
		if w.id == id: return w
	return WEAPONS[0]

static func loadout(ids: Array) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for id in ids:
		out.append(find(id))
	if out.is_empty():
		for id in DEFAULT_LOADOUT: out.append(find(id))
	return out
