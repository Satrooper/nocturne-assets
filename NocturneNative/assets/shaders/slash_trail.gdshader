shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, shadows_disabled;
uniform vec4 tint : source_color = vec4(.66,.78,1.0,1.0);
uniform float fade = 1.0;
void fragment(){
 // UV.x: progress along the swing (leading edge = 1). UV.y: inner (0) to blade tip (1).
 float along = pow(UV.x, 2.2);
 float band = smoothstep(.45, .8, UV.y) * (1.0 - smoothstep(.96, 1.0, UV.y));
 float core = smoothstep(.86, .96, UV.y) * (1.0 - smoothstep(.96, 1.0, UV.y));
 float a = along * (band * .16 + core * .75) * fade;
 ALBEDO = tint.rgb * a + vec3(core * along * fade * .25);
}
