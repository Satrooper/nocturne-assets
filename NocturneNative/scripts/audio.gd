class_name NRAudio
extends Node
# Mixer: separate buses per category with user volumes, per-stage acoustics on
# weapons/effects, pooled voices, random shot variants, footsteps, and a radio.
# Music override: put your own track at res://assets/music/custom/<id>.ogg (or .mp3).
const BUSES = ["Music","Weapons","Effects","Movement","UI"]
const CATEGORY = {
	"pistol":"Weapons","rifle":"Weapons","shotgun":"Weapons","mg":"Weapons","rocket":"Weapons","blaster":"Weapons",
	"laser_loop":"Weapons","reload":"Weapons","empty":"Weapons","overheat":"Weapons",
	"sword_1":"Weapons","sword_2":"Weapons","sword_heavy":"Weapons",
	"explosion":"Effects","sword_hit":"Effects","slam":"Effects","hurt":"Effects","impact":"Effects","success":"Effects",
	"boost":"Movement","jump":"Movement","land":"Movement","whoosh":"Movement",
	"ui":"UI"}
const VOLUME = {"mg":-11.0,"laser_loop":-12.0,"ui":-14.0,"explosion":-5.0,"slam":-6.0,"hurt":-9.0,"boost":-8.0,"jump":-12.0,"land":-10.0}
# Radio stations: id -> title. The first seven are the stage/menu scores.
const TRACKS = [
	["menu","Night Signal","Dark synthwave · menu"],
	["stage1","Neon Underworld","Cyberpunk darksynth"],
	["stage2","Glass Palace","Spy-house · jazz chords"],
	["stage3","Hollow Bamboo","Koto plucks · taiko"],
	["stage4","Ashworks","Industrial · distorted bass"],
	["stage5","Black Cathedral","Gothic organ · bells"],
	["boss","Final Contract","Boss theme · 148 BPM"],
	["radio1","Rain Chase","Outrun synthwave"],
	["radio2","Chrome Heist","Funk house"],
	["radio3","Lotus Drift","Lo-fi beats"],
	["radio4","Iron Liturgy","Heavy industrial"],
	["radio5","Neon Pulse","Festival EDM"],
]
const ACOUSTICS = [ # room_size, damping, wet, predelay(ms) per stage
	[.38,.55,.13,18.0], [.72,.35,.22,35.0], [.18,.8,.06,8.0], [.6,.45,.17,30.0], [.95,.25,.3,55.0]]
var voices: Array[AudioStreamPlayer] = []
var cursor: int = 0
var effects: Dictionary = {}
var variants: Dictionary = {}
var enabled: bool = true
var music_a: AudioStreamPlayer
var music_b: AudioStreamPlayer
var music_name: String = ""
var context_track: String = ""
var radio_track: String = ""   # "" = AUTO (follows the stage and boss fights)
var beam_voice: AudioStreamPlayer
var last_played: Dictionary = {}
var volumes: Dictionary = {"Master":1.0,"Music":.75,"Weapons":.9,"Effects":.9,"Movement":.8,"UI":.7}
var step_toggle: int = 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	setup_buses()
	load_settings()
	if DisplayServer.get_name() == "headless" or OS.get_cmdline_args().has("Dummy"):
		enabled = false
		return
	var dir = DirAccess.open("res://assets/sfx")
	if dir:
		# Exported builds list "x.wav.import" rather than "x.wav"; handle both.
		for file in dir.get_files():
			var name = file.trim_suffix(".import").trim_suffix(".wav")
			if effects.has(name) or not ResourceLoader.exists("res://assets/sfx/%s.wav" % name): continue
			effects[name] = load("res://assets/sfx/%s.wav" % name)
	for name in ["impact","success","whoosh"]:
		effects[name] = load("res://assets/"+name+".wav")
	# Variants: pistol_2.wav, pistol_3.wav ... are picked at random.
	for name in effects.keys():
		var cut = name.rfind("_")
		var base = name.substr(0, cut) if cut > 0 and name.substr(cut+1).is_valid_int() and not name.begins_with("step_") and not name.begins_with("sword_") else name
		if base != name:
			if not variants.has(base): variants[base] = [base] if effects.has(base) else []
			variants[base].append(name)
	for i in range(20):
		var voice = AudioStreamPlayer.new()
		add_child(voice)
		voices.append(voice)
	beam_voice = AudioStreamPlayer.new()
	beam_voice.bus = "Weapons"
	if effects.has("laser_loop"):
		var loop: AudioStreamWAV = effects.laser_loop.duplicate()
		loop.loop_mode = AudioStreamWAV.LOOP_FORWARD
		loop.loop_end = int(loop.get_length() * loop.mix_rate)
		beam_voice.stream = loop
	beam_voice.volume_db = VOLUME.laser_loop
	add_child(beam_voice)
	music_a = AudioStreamPlayer.new(); music_a.bus = "Music"; add_child(music_a)
	music_b = AudioStreamPlayer.new(); music_b.bus = "Music"; add_child(music_b)
	var ambience = AudioStreamPlayer.new()
	var stream: AudioStreamWAV = load("res://assets/ambience.wav")
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_end = int(stream.get_length()*stream.mix_rate)
	ambience.stream = stream
	ambience.volume_db = -30
	ambience.bus = "Effects"
	add_child(ambience)
	ambience.play()

func setup_buses() -> void:
	for name in BUSES:
		if AudioServer.get_bus_index(name) >= 0: continue
		AudioServer.add_bus()
		var index = AudioServer.bus_count - 1
		AudioServer.set_bus_name(index, name)
		AudioServer.set_bus_send(index, "Master")
	for name in ["Weapons","Effects"]:
		var index = AudioServer.get_bus_index(name)
		if AudioServer.get_bus_effect_count(index) == 0:
			AudioServer.add_bus_effect(index, AudioEffectReverb.new())
	var master = AudioServer.get_bus_index("Master")
	if AudioServer.get_bus_effect_count(master) == 0:
		var limiter = AudioEffectHardLimiter.new()
		limiter.ceiling_db = -.5
		AudioServer.add_bus_effect(master, limiter)

func set_stage_acoustics(stage: int) -> void:
	var a = ACOUSTICS[clampi(stage, 0, ACOUSTICS.size()-1)]
	for name in ["Weapons","Effects"]:
		var reverb: AudioEffectReverb = AudioServer.get_bus_effect(AudioServer.get_bus_index(name), 0)
		reverb.room_size = a[0]; reverb.damping = a[1]; reverb.wet = a[2]; reverb.predelay_msec = a[3]
		reverb.dry = 1.0; reverb.spread = .8; reverb.hipass = .15

func set_volume(bus: String, value: float) -> void:
	volumes[bus] = clampf(value, 0.0, 1.0)
	var index = AudioServer.get_bus_index(bus)
	if index < 0: return
	AudioServer.set_bus_mute(index, volumes[bus] <= .001)
	AudioServer.set_bus_volume_db(index, linear_to_db(maxf(volumes[bus], .001)))
	save_settings()

func load_settings() -> void:
	var cfg = ConfigFile.new()
	if cfg.load("user://audio_v6.cfg") == OK:
		for bus in volumes.keys(): volumes[bus] = float(cfg.get_value("volume", bus, volumes[bus]))
		radio_track = str(cfg.get_value("radio", "track", ""))
	for bus in volumes.keys():
		var index = AudioServer.get_bus_index(bus)
		if index >= 0:
			AudioServer.set_bus_mute(index, volumes[bus] <= .001)
			AudioServer.set_bus_volume_db(index, linear_to_db(maxf(volumes[bus], .001)))

func save_settings() -> void:
	var cfg = ConfigFile.new()
	for bus in volumes.keys(): cfg.set_value("volume", bus, volumes[bus])
	cfg.set_value("radio", "track", radio_track)
	cfg.save("user://audio_v6.cfg")

func play_effect(name: String, pitch: float = 1.0) -> void:
	if not enabled: return
	var chosen = name
	if variants.has(name) and not variants[name].is_empty():
		chosen = variants[name][randi() % variants[name].size()]
	if not effects.has(chosen): return
	var now = Time.get_ticks_msec()
	if last_played.get(name, -1000) > now - 25: return
	last_played[name] = now
	var voice = voices[cursor]
	cursor = (cursor+1)%voices.size()
	voice.stream = effects[chosen]
	voice.bus = CATEGORY.get(name, "Effects")
	voice.pitch_scale = pitch*randf_range(.97,1.03)
	voice.volume_db = VOLUME.get(name, -10.0)
	voice.play()

func footstep(stage: int, intensity: float) -> void:
	if not enabled: return
	var surface = ["hard","hard","soft","metal","hard"][clampi(stage,0,4)]
	step_toggle += 1
	var name = "step_%s_%d" % [surface, 1 + (step_toggle + randi() % 3) % 4]
	if not effects.has(name): return
	var voice = voices[cursor]
	cursor = (cursor+1)%voices.size()
	voice.stream = effects[name]
	voice.bus = "Movement"
	voice.pitch_scale = randf_range(.92, 1.08)
	voice.volume_db = -17.0 + intensity * 5.0
	voice.play()

func beam(on: bool) -> void:
	if not enabled: return
	if on and not beam_voice.playing: beam_voice.play()
	elif not on and beam_voice.playing: beam_voice.stop()

# ------------------------------------------------------------------ music + radio
func track_title(id: String) -> String:
	for t in TRACKS:
		if t[0] == id: return t[1]
	return id

func now_playing_title() -> String:
	return ("AUTO · " if radio_track == "" else "") + track_title(music_name)

func music_stream(id: String) -> AudioStream:
	for path in ["res://assets/music/custom/%s.ogg" % id, "res://assets/music/custom/%s.mp3" % id, "res://assets/music/%s.ogg" % id]:
		if ResourceLoader.exists(path):
			var stream = load(path)
			if stream is AudioStreamOggVorbis or stream is AudioStreamMP3:
				stream = stream.duplicate()
				stream.loop = true
			return stream
	return null

# The game asks for context music (menu, stageN, boss); the radio may override it.
func play_music(id: String, fade: float = 1.2) -> void:
	context_track = id
	_switch(radio_track if radio_track != "" else id, fade)

func set_radio(id: String) -> void:
	radio_track = id
	save_settings()
	_switch(id if id != "" else context_track, .8)

func radio_next(step: int = 1) -> void:
	var ids = [""]
	for t in TRACKS: ids.append(t[0])
	var i = ids.find(radio_track)
	set_radio(ids[posmod(i + step, ids.size())])

func _switch(id: String, fade: float) -> void:
	if id == music_name or id == "": return
	music_name = id
	if not enabled: return
	var stream = music_stream(id)
	var old = music_a if music_a.playing else (music_b if music_b.playing else null)
	var incoming = music_b if old == music_a else music_a
	if old:
		var out = create_tween()
		out.tween_property(old, "volume_db", -60.0, fade)
		out.tween_callback(old.stop)
	if stream == null: return
	incoming.stream = stream
	incoming.volume_db = -50.0
	incoming.play()
	var t = create_tween()
	t.tween_property(incoming, "volume_db", -8.0, fade)

func _exit_tree() -> void:
	for child in get_children():
		if child is AudioStreamPlayer:
			child.stop()
			child.stream = null
	effects.clear()
	voices.clear()
