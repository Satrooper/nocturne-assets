shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled;
uniform sampler2D atlas : source_color, filter_linear, repeat_disable;
uniform vec2 grid = vec2(6.0, 4.0);
uniform float frames = 24.0;
uniform float fps = 25.0;
uniform float age_seconds = 0.0;
uniform float brightness = 1.0;
void fragment() {
	float frame = clamp(floor(age_seconds * fps), 0.0, frames - 1.0);
	vec2 cell = vec2(mod(frame, grid.x), floor(frame / grid.x));
	vec4 color = texture(atlas, (UV + cell) / grid);
	ALBEDO = color.rgb * brightness;
	ALPHA = color.a * (1.0 - step(frames / fps, age_seconds));
}
