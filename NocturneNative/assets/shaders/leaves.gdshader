shader_type spatial;
render_mode cull_disabled;
uniform vec4 tint : source_color = vec4(.20,.35,.08,1.0);
varying float shade;
void vertex(){
 vec3 p=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;
 VERTEX.x+=sin(TIME*1.2+p.x*.9+p.z*.65)*.06*UV.y;
 shade=.7+.3*UV.y;
}
void fragment(){float vein=1.-smoothstep(.012,.06,abs(UV.x-.5));ALBEDO=tint.rgb*shade*(.82+.18*sin(UV.y*3.14159))+tint.rgb*vein*.15;ROUGHNESS=.87;BACKLIGHT=tint.rgb*.12;}
