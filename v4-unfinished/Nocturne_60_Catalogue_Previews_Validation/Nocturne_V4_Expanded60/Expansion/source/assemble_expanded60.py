from pathlib import Path
import json,hashlib,collections,io,struct,subprocess,zipfile,html
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];W=P.parent;B=W/'Nocturne_V4_Visual_Revision';D=W/'work/expanded60_documentation';D.mkdir(exist_ok=True)
old=json.loads((B/'asset_manifest.json').read_text())['characters'];new=json.loads((P/'audit/Build_Progress.json').read_text());assert len(old)==len(new)==30
code=(B/'source/repetition_audit.py').read_text().split('manifest=json.loads')[0];env={'__file__':str(B/'source/repetition_audit.py')};exec(code,env);glb=env['glb'];pointkey=env['pointkey'];digest=env['digest'];geo=collections.defaultdict(list);normal=collections.defaultdict(list);motions=collections.defaultdict(list);bytesets=collections.defaultdict(list);inventory=[];previewhash=[];texturechecks=[]
validation={x['asset']:x for x in json.loads((P/'audit/Export_Validation.json').read_text())}
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for added,rows,base,prefix in [(False,old,B,''),(True,new,P,'Expansion/')]:
 for c in rows:
  name=c['asset'];f=base/c['canonical_glb'];doc,arr=glb(f);points=np.concatenate([arr(pr['attributes']['POSITION']) for m in doc['meshes'] for pr in m['primitives']]);geo[pointkey(points)].append(name);normal[pointkey(points,True)].append(name)
  for suffix in ['.glb','.fbx']:
   ff=f.with_suffix(suffix);bytesets[digest(ff.read_bytes())].append(prefix+str(ff.relative_to(base)))
  for a in doc.get('animations',[]):
   channels=[]
   for ch in a['channels']:
    s=a['samplers'][ch['sampler']];target=ch['target'];node=doc['nodes'][target['node']].get('name','unnamed');channels.append((node,target['path'],s.get('interpolation','LINEAR'),digest(arr(s['input']).tobytes()),digest(arr(s['output']).tobytes())))
   motions[digest(json.dumps(sorted(channels)).encode())].append({'asset':name,'clip':a.get('name')})
  preview=('previews/characters/'+name+'/Threequarter.jpg') if added else ('previews/roster/'+name+('/Before_Threequarter.jpg' if name=='Cinder_Crown' else '/After_Threequarter.jpg'))
  im=Image.open(base/preview);im.load();gray=np.asarray(im.convert('L').resize((9,8)));previewhash.append((name,gray[:,1:]>gray[:,:-1]));bytesets[digest((base/preview).read_bytes())].append(prefix+preview)
  status='new_prototype_visual_target_unmet' if added else 'retained_saved_revision_visual_target_unmet'
  inv={'asset':name,'category':c['category'],'status':status,'canonical_glb':prefix+c['canonical_glb'],'canonical_fbx':prefix+c.get('canonical_fbx',str(Path(c['canonical_glb']).with_suffix('.fbx'))),'editable_source':prefix+c.get('editable_source',str(Path(c['canonical_glb']).with_suffix('.blend'))),'preview':prefix+preview,'vertices':len(points),'clips':len(doc.get('animations',[])),'changes':c.get('design','Preserved previous saved revisions; not counted as a new upgrade.'),'structural_validation':'new GLB/FBX reimports and source opens' if added else 'previous saved validation retained','visual_approved':False,'contact_clipping_approved':False,'engine_tested':False,'iphone_tested':False,'remaining':['Cinematic sculpted anatomy/construction and texture painting','Character-specific combat choreography and all-frame contact/clipping review','Runtime integration and device testing']}
  if added:
   rec=validation[name];m=rec['motion_preview'];clip=next(x for x in c['clips'] if x['purpose'] in m['action']);m['duration_s']=clip['duration_s'];m['timing_note']='Normalized sample frames from a GLB import at 24 fps; playback duration corrected to authored seconds.'
   frames=[Image.open(P/x).convert('RGB') for x in m['frames']];gif=P/'previews/characters'/name/'Motion.gif';frames[0].save(gif,save_all=True,append_images=frames[1:],duration=round(clip['duration_s']*1000/8),loop=0);inv['motion_preview']='Expansion/'+str(gif.relative_to(P));inv['motion_preview_clip']=m['action']
  else:inv['motion_preview_note']='Use retained preview mapping; Cinder experimental motion is explicitly rejected and is not the canonical model.'
  inventory.append(inv)
(P/'audit/Export_Validation.json').write_text(json.dumps(list(validation.values()),indent=2))
# Decode every new external texture and each embedded GLB image (including players and props).
for f in sorted((P/'textures').rglob('*.png')):
 im=Image.open(f);im.load();texturechecks.append({'file':str(f.relative_to(P)),'decoded':True,'size':list(im.size)})
embedded=[]
for f in sorted([P/c['canonical_glb'] for c in new]+list((P/'player_animation').glob('*.glb'))+list((P/'player_handling').glob('*.glb'))+list((P/'weapons').glob('*/*.glb'))):
 data=f.read_bytes();pos=12;doc=None;binary=None
 while pos<len(data):
  n,t=struct.unpack_from('<II',data,pos);ch=data[pos+8:pos+8+n];pos+=8+n
  if t==0x4e4f534a:doc=json.loads(ch)
  elif t==0x004e4942:binary=ch
 imgs=[]
 for im in doc.get('images',[]):
  if 'bufferView' in im:
   v=doc['bufferViews'][im['bufferView']];b=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];pic=Image.open(io.BytesIO(b));pic.load();imgs.append({'decoded':True,'size':list(pic.size)})
  else:raise AssertionError((f,im))
 embedded.append({'file':str(f.relative_to(P)),'embedded_images':imgs,'external_texture_dependency':False})
(P/'audit/Final_Texture_Decode.json').write_text(json.dumps({'external':texturechecks,'glb':embedded},indent=2))
report={'canonical_characters':60,'exact_model_or_catalogue_preview_byte_groups':[v for v in bytesets.values() if len(v)>1],'exact_position_cloud_groups':[v for v in geo.values() if len(v)>1],'uniform_scale_position_cloud_groups':[v for v in normal.values() if len(v)>1],'exact_shared_motion_groups':[v for v in motions.values() if len(v)>1],'near_preview_candidates':[{'assets':[a,b],'hash_distance':int(np.count_nonzero(x!=y))} for i,(a,x) in enumerate(previewhash) for b,y in previewhash[i+1:] if np.count_nonzero(x!=y)<=5],'known_legacy_repetition':json.loads((B/'audit/Repetition_Audit.json').read_text())['known_visual_repetition_review'],'method':'Mesh-local material-free position fingerprints and exact channel samplers. Preview difference hash candidates require review. These checks do not prove visual identity, anatomy or motion quality.','deletions':[],'changes':'30 original procedural body plans added. Seven optional legacy alternate variants supplied; canonical old assets retained. No cinematic or all-60 visual distinctness approval.','shared_animation_policy':'Reusable primitive frameworks and useful shared clips retained and labelled; instance count is not unique choreography count.'}
(P/'audit/Expanded60_Duplicate_Audit.json').write_text(json.dumps(report,indent=2))
counts={'creatures':60,'dragons':20,'bosses':20,'smaller_enemies':20,'weapons':6,'sounds':140,'effect_atlases':24,'creature_clip_instances':sum(c['clips'] for c in inventory),'player_body_and_handling_clip_instances':128,'weapon_mechanism_clip_instances':8,'logical_clip_instances':1456,'new_texture_sets':30,'new_texture_maps':120,'optional_legacy_variants':7}
assert counts['creature_clip_instances']==1320
master={'title':'Nocturne Expanded 60 Prototype Collection','requested_cinematic_scope_complete':False,'quantity_expansion_complete':True,'counts':counts,'characters':inventory,'testing':{'structural':'See Expansion/audit final reimport/root/source/texture checks and retained base audit','visual':'Actual export renders supplied; cinematic quality and contact approval unmet','engine':'Not performed; no destination project/runtime supplied','iphone':'Not performed'},'audio':'70 retained plus 70 new original synthesized 48 kHz PCM16 WAV; no recorded or licensed external material added','effects':'12 retained plus 12 procedural RGBA flipbooks, playback metadata supplied; engine particle/material wiring required','original_design_provenance':'Procedural original geometry; franchise references are quality goals, not copied assets.'}
(D/'Expanded60_Inventory.json').write_text(json.dumps(master,indent=2));(D/'Completion_Checklist.json').write_text(json.dumps({'scope_complete':False,'characters':inventory,'additional_requirements':[{'requirement':x,'status':'unfinished','remaining':r} for x,r in [('Cinematic quality','Dedicated anatomical sculpting, retopology, texture painting and individual art review across the roster'),('Player handling polish','Body and prop clips exist; grip, clothing intersection, fingers, recoil, reload and switching require final all-frame polish'),('Creature motion polish','All-frame foot/wing contact, anticipation, impact, recovery and loop review'),('Paired finishers','Prototype attacker/victim alignment metadata requires runtime paired playback validation'),('Audio realism','Synthesized assets supplied; realistic recorded foley and creature vocal performance remain'),('Effects integration','Flipbooks supplied; volumetric particles, lights, decals and engine playback remain'),('Gameplay integration','Damage, hit windows, stamina, invulnerability, lock-on, projectiles and boss AI remain code requirements'),('iPhone','No measured device performance')]]},indent=2))
# Actual model contact sheets.
for category in ['dragons','bosses','enemies']:
 items=[c for c in inventory if c['category']==category and c['canonical_glb'].startswith('Expansion/')];canvas=Image.new('RGB',(1600,700),(22,24,27));draw=ImageDraw.Draw(canvas)
 for i,c in enumerate(items):
  im=Image.open(P/c['preview'].removeprefix('Expansion/'));im.thumbnail((310,300));x=(i%5)*320;y=(i//5)*350;canvas.paste(im,(x+(320-im.width)//2,y));draw.text((x+10,y+305),c['asset'].replace('_',' '),font=font,fill='white')
 canvas.save(D/f'New_{category.title()}_Catalogue.jpg',quality=94)
legacy=json.loads((P/'audit/Legacy_Distinct_Variants.json').read_text());canvas=Image.new('RGB',(1024,7*280),(22,24,27));draw=ImageDraw.Draw(canvas)
for i,c in enumerate(legacy):
 for j,label in enumerate(['Before','After']):
  im=Image.open(P/'previews/legacy_variants'/c['asset']/(label+'_Threequarter.jpg'));im.thumbnail((500,250));canvas.paste(im,(j*512,i*280));draw.text((j*512+10,i*280+250),c['asset']+' '+label+' (prototype)',font=font,fill='white')
canvas.save(D/'Legacy_Alternates_Before_After.jpg',quality=94)
# Actual player previews, timed to their delivered clip metadata.
manifest=json.loads((P/'player_handling/handling_manifest.json').read_text());duration={c['name']:c['duration_s'] for c in manifest['clips']}
for folder in sorted((P/'previews/player').glob('frames_*')):
 name=folder.name.removeprefix('frames_');frames=sorted(folder.glob('*.png'));assert len(frames)==16
 ims=[Image.open(f).convert('RGB') for f in frames];out=folder.parent/(name+'.gif');ims[0].save(out,save_all=True,append_images=ims[1:],duration=max(20,round(duration[name]*1000/16)),loop=0)
# Offline catalogue links only corresponding delivered files.
cards=[]
for c in inventory:
 n=html.escape(c['asset']);p=html.escape(c['preview']);model=html.escape(c['canonical_glb']);extra=''
 if c.get('motion_preview'):extra=f'<a href="{html.escape(c["motion_preview"])}">Motion preview</a>'
 cards.append(f'<article><h2>{n}</h2><img src="{p}" alt="{n} delivered GLB render"><p>{html.escape(c["status"])}</p><a href="{model}">GLB</a> · <a href="{html.escape(c["canonical_fbx"])}">FBX</a> · {extra}<p>{html.escape(c["changes"])}</p></article>')
(D/'Character_Catalogue.html').write_text('<!doctype html><meta charset="utf-8"><title>Nocturne 60 actual model catalogue</title><style>body{background:#16191d;color:#eee;font:16px sans-serif;margin:30px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}article{background:#252a31;padding:15px}img{width:100%}a{color:#9dd7ff}h2{font-size:20px}</style><h1>Nocturne Expanded 60 — prototype assets</h1><p>30 retained + 30 new. Actual model renders. Cinematic realism and all-frame motion quality remain unfinished. Cinder canonical view uses its retained model; rejected experimental previews remain separately documented.</p><main>'+''.join(cards)+'</main>')
readme='''# Nocturne Expanded 60 — quantity expansion, prototype quality

This delivery preserves the latest saved original 30 creatures and adds 30 new procedural body plans. It doubles sounds, effect atlases, player clip instances and weapon count. It does not meet the requested cinematic CGI/VFX art or animation polish target. Version and file size do not imply that quality.

Extract all ZIP components into the SAME destination, in the order listed in Nocturne_60_Downloads.json, with Catalogue_Previews_Validation last. All components share Nocturne_V4_Expanded60/. They are ordinary ZIPs; do not concatenate them. Components stay below the per-file upload ceiling. Source texture maps, FBX, GLB and editable Blender sources account for the size; no filler added.

Open Character_Catalogue.html for 60 correctly mapped neutral model views. Expanded60_Inventory.json is authoritative; the retained asset_manifest.json describes the original 30 only. Expansion/previews/characters contains neutral front/side/back/threequarter/close-up/wireframe views and representative motion GIFs from actual GLB reimports. Expansion/previews/player contains actual body/prop previews. The seven legacy before/after alternates use identical neutral setup and framing. They are optional, not counted as seven additional characters or silently substituted into the canonical inventory.

## What's included
60 creatures (20 dragons, 20 bosses, 20 smaller enemies), 6 weapons, 140 WAV sounds, 24 effect atlases. 1456 logical animation instances: 1320 creature, 128 player body/handling, 8 mechanism. These are not 1456 distinct animation types or unique choreographies. Shared procedural frameworks are documented. New textures: 30 original procedural 2048 sets of BaseColor, Normal, Roughness and 16-bit authoring Height.

## Quality and validation
New GLB and FBX exports are reimported, sources opened and packed images decoded. Root translation/yaw and clip counts have separate final checks. Representative neutral renders and sampled finite deformation checks are evidence of file usability; they do not establish anatomical realism, no clipping, clean foot contact or cinematic movement. Near-duplicate original design families remain flagged. All 60 are not visually approved as distinct cinematic designs.

Player handling clips animate the actual mannequin and attached weapons, not merely weapon mechanisms. The mannequin is still prototype artwork. New handling includes high/low aim, side peeks, crouched fire/reload, hip fire, rifle bursts and low-ready drawing/holstering. Body combos, directional dodges and finishers are procedural prototypes. Source contact-target measurements are authored targets; they are not validated runtime damage windows. Preserve full action names in GLB/sources; FBX_Action_Name_Map.json documents shorter export names to avoid import truncation.

## Remaining capability/work gap
The available modelling path is Blender procedural Python, not an accessible dedicated 3D-generation service or automatic cinematic anatomical sculptor. Achieving the stated target needs substantial asset-by-asset sculpting, retopology, texture painting and animation direction. Primitive assemblies and generated texture detail remain visibly simple. High-resolution height textures are authoring data, not proof of realistic anatomy. No external licensed models, recorded sounds, motion capture or hidden Meshy generation are claimed.

Audio additions are synthesized 48 kHz mono PCM16. Effect additions are procedural RGBA 24-frame flipbooks with playback metadata, not finished volumetric effects. Engine implementation remains required for materials/particles, hit detection, damage, stamina, invulnerability, lock-on, projectiles, paired finisher playback and boss phases. No destination-engine or iPhone testing performed.

## Resume
Read Completion_Checklist.json and Expansion/audit/Expanded60_Duplicate_Audit.json. Preserve all canonical assets. Next task: manually art-direct and sculpt a reviewed mechanical and organic asset beyond prototype forms, then use that approved standard across the original and expanded roster. Polish all-frame motion/contact and runtime integration afterward. Optional legacy variants require review before promotion.
'''
(D/'README_Expanded60.md').write_text(readme);(D/'Resume_Instructions.md').write_text(readme.split('## Resume')[1]);print('DOCUMENTATION_AND_AUDIT_COMPLETE',len(inventory),len(texturechecks),len(embedded),counts,flush=True)
