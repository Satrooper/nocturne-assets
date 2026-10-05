shader_type spatial;
uniform sampler2D asphalt : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_tex : filter_linear_mipmap, repeat_enable;
varying vec3 wp;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.0),f.x),f.y);}
void vertex(){wp=(MODEL_MATRIX*vec4(VERTEX,1)).xyz;}
void fragment(){
 vec2 uv=wp.xz*.34;
 float puddle=smoothstep(.44,.62,noise(wp.xz*.30)+noise(wp.xz*1.1)*.12);
 ALBEDO=texture(asphalt,uv).rgb*mix(.60,.25,puddle);
 ROUGHNESS=mix(clamp(texture(rough_tex,uv).r,.5,.9),.15,puddle); METALLIC=0.0;
 NORMAL_MAP=texture(normal_tex,uv).rgb;
 NORMAL_MAP_DEPTH=mix(.45,.045,puddle);
 SPECULAR=.5;
}
