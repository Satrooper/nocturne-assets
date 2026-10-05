shader_type spatial;
uniform sampler2D color_map : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_map : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_map : filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float meters_per_tile = 2.0;
uniform float roughness_scale = 1.0;
uniform float metalness = 0.0;
uniform float normal_strength = 0.7;
uniform float wetness = 0.0;
varying vec3 world_pos;
varying vec3 world_normal;
void vertex(){world_pos=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;world_normal=normalize(MODEL_NORMAL_MATRIX*NORMAL);}
void fragment(){
 vec3 n=normalize(world_normal),a=abs(n);
 vec2 uv;vec3 tangent;vec3 bitangent;
 if(a.y>a.x && a.y>a.z){uv=world_pos.xz; tangent=vec3(1,0,0);bitangent=vec3(0,0,-sign(n.y));uv.y*=-sign(n.y);}
 else if(a.x>a.z){uv=world_pos.zy;tangent=vec3(0,0,-sign(n.x));bitangent=vec3(0,1,0);uv.x*=-sign(n.x);}
 else {uv=world_pos.xy;tangent=vec3(sign(n.z),0,0);bitangent=vec3(0,1,0);uv.x*=sign(n.z);}
 uv/=meters_per_tile;
 vec3 albedo=texture(color_map,uv).rgb;
 float macro=.94+.06*sin(world_pos.x*.39+sin(world_pos.z*.21));
 ALBEDO=albedo*tint.rgb*macro*mix(1.,.62,wetness);
 ROUGHNESS=clamp(texture(rough_map,uv).r*roughness_scale-wetness*.16,.12,.97);METALLIC=metalness;
 vec3 detail=texture(normal_map,uv).xyz*2.-1.;detail.xy*=normal_strength;
 vec3 world_detail=normalize(tangent*detail.x+bitangent*detail.y+n*max(detail.z,.1));
 NORMAL=normalize((VIEW_MATRIX*vec4(world_detail,0.)).xyz);
 SPECULAR=.5;
}
