shader_type spatial;
uniform vec4 tint : source_color=vec4(.025,.16,.17,1);
varying vec3 p;
void vertex(){p=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){ALBEDO=tint.rgb;ROUGHNESS=.13;METALLIC=.5;NORMAL=normalize(NORMAL+vec3(sin(p.x*9.+TIME)*.018,0.,cos(p.z*11.+TIME*.7)*.018));}
