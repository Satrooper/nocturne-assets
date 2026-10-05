shader_type spatial;
uniform vec4 base_color : source_color = vec4(0.24,0.20,0.17,1.0);
uniform float brick = 1.0;
varying vec3 wp;
varying vec3 wn;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void vertex(){wp=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;wn=normalize((MODEL_MATRIX*vec4(NORMAL,0.0)).xyz);}
void fragment(){
 vec2 uv=abs(wn.x)>0.5?wp.zy:wp.xy;
 vec2 q=uv*vec2(2.6,6.2); q.x+=mod(floor(q.y),2.0)*0.5;
 vec2 cell=floor(q); vec2 f=fract(q);
 float mortar=(1.0-smoothstep(0.015,0.055,min(min(f.x,1.0-f.x),min(f.y,1.0-f.y))))*brick;
 float grain=hash(floor(uv*180.0));
 float variation=0.72+hash(cell)*0.45;
 float stain=0.85+0.15*sin(wp.x*1.7+sin(wp.z*3.2))*sin(wp.y*.7);
 ALBEDO=mix(base_color.rgb*variation,base_color.rgb*.37,mortar)*stain*(.88+grain*.18);
 ROUGHNESS=.78; METALLIC=.05;
}
