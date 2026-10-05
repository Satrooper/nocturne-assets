shader_type spatial;
uniform vec4 tint : source_color = vec4(.5,.5,.5,1.0);
uniform int style=0;
varying vec3 p;
float hash(vec2 q){return fract(sin(dot(q,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 q){vec2 i=floor(q),f=fract(q);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}
void vertex(){p=(MODEL_MATRIX*vec4(VERTEX,1.)).xyz;}
void fragment(){
 float n=noise(p.xz*2.0)+.3*noise(p.xz*13.);
 ALBEDO=tint.rgb*(.76+.25*n); ROUGHNESS=.8;
 if(style==0){
  float vein=pow(abs(sin(p.x*.8+p.z*.35+noise(p.xz*.4)*4.0+noise(p.xz*3.)*.6)),18.);
  ALBEDO=mix(tint.rgb,tint.rgb*.36,vein*.7);
  vec2 f=fract(p.xz*.5); float seam=step(.012,min(min(f.x,1.-f.x),min(f.y,1.-f.y)));
  ALBEDO*=mix(.50,1.,seam); ROUGHNESS=.22; METALLIC=.12;
 }else if(style==1){
  float path=1.-smoothstep(3.,5.5,abs(p.x-1.7*sin(p.z*.18)));
  vec3 earth=vec3(.19,.13,.065);vec3 moss=vec3(.11,.17,.055);
  ALBEDO=mix(moss,earth,path)*(.65+.5*n); ROUGHNESS=.96;
 }else if(style==2){
  float rust=smoothstep(.48,.82,n);
  ALBEDO=mix(tint.rgb,vec3(.32,.13,.047),rust); METALLIC=mix(.7,.03,rust);ROUGHNESS=mix(.4,.93,rust);
 }else if(style==3){
  ALBEDO=tint.rgb*(.75+.22*n); ROUGHNESS=.86;
  vec2 f=fract(p.xz*.6);float seam=step(.026,min(min(f.x,1.-f.x),min(f.y,1.-f.y)));
  ALBEDO*=mix(.38,1.,seam);
 }else if(style==5){
  ALBEDO=tint.rgb*(.68+.32*n);ROUGHNESS=.97;
 }else if(style==4){
  ALBEDO=mix(vec3(.53,.59,.65),vec3(.80,.84,.87),smoothstep(.1,1.,n));ROUGHNESS=.6;
 }
}
