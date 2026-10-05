extends Node3D
## Untested template. Assign your imported GLB scene and an actual animation name.
@export var actor_scene: PackedScene
@export var focus_height := 1.5
@export var animation_name := ""
@export var camera_distance := 5.0
@export var introduction_seconds := 3.0
var elapsed := 0.0
var actor: Node
@onready var camera: Camera3D = $Camera

func _ready() -> void:
	if actor_scene:
		actor = actor_scene.instantiate()
		$ActorAnchor.add_child(actor)
		var player := _animation_player(actor)
		if player and player.has_animation(animation_name):
			player.play(animation_name)

func _process(delta: float) -> void:
	elapsed += delta
	var phase := clampf(elapsed / maxf(introduction_seconds, 0.01), 0.0, 1.0)
	var ease := phase * phase * (3.0 - 2.0 * phase)
	var target := Vector3(0, focus_height, 0)
	camera.position = target + Vector3(0.65, 0.12, 1.0).normalized() * camera_distance * lerpf(1.0, 0.91, ease)
	camera.look_at(target, Vector3.UP)

func _animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node as AnimationPlayer
	for child in node.get_children():
		var found := _animation_player(child)
		if found:
			return found
	return null
