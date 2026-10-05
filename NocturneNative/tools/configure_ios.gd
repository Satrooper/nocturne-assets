@tool
extends SceneTree
func _init() -> void:
	var team = OS.get_environment("APPLE_TEAM_ID")
	var pattern = RegEx.new()
	pattern.compile("^[A-Z0-9]{10}$")
	if not pattern.search(team):
		push_error("Set APPLE_TEAM_ID to your real 10-character Apple developer team identifier.")
		quit(1)
		return
	var config = ConfigFile.new()
	if config.load("res://export_presets.cfg") != OK:
		quit(1)
		return
	config.set_value("preset.1.options","application/app_store_team_id",team)
	config.set_value("preset.1.options","application/export_project_only",true)
	config.save("res://export_presets.cfg")
	quit()
