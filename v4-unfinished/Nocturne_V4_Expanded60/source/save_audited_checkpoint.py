"""Preserve all prior delivered bytes; add read-only audit and matched topology views."""
from pathlib import Path
import json,hashlib,zipfile,shutil,html,subprocess
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[2];P=W/'Nocturne_V4_Visual_Revision'
audit=json.loads((P/'audit/Repetition_Audit.json').read_text());catalog=json.loads((P/'asset_manifest.json').read_text())['characters']
mapping=json.loads((P/'audit/Wireframe_Preview_Mapping.json').read_text());assert len(mapping)==30
check=json.loads((P/'audit/Completion_Checklist.json').read_text());check['scope_complete']=False
check['latest_checkpoint_work']={'model_changes_this_pass':False,'duplicate_audit':'audit/Repetition_Audit.json','wireframe_mapping':'audit/Wireframe_Preview_Mapping.json','all_previous_improvements_preserved':True,'next_task':'Redesign Crypt_Arachnarch / Hundredleg / Crypt_Skitter as distinct anatomy and motion; approve one genuinely stronger asset before repeating across roster. Dedicated 3D generation is not connected; do not rerun decorative procedural passes as cinematic upgrades.'}
for c in check['characters']:
    c['repetition_audit_path']='audit/Repetition_Audit.json';c['wireframe_preview']='previews/wireframes/'+c['asset']+'.jpg'
    c['repetition_candidates']=[x for x in audit['near_preview_candidates'] if c['asset'] in x['assets']]
(P/'audit/Completion_Checklist.json').write_text(json.dumps(check,indent=2))
report='''# Repetition audit checkpoint — requested cinematic V4 is NOT complete

All 30 canonical creature GLBs were parsed. Current FBX/GLB and preview files were SHA-256 checked outside historical provenance. No exact whole-character position-cloud duplicates or uniform-scale-only whole-position duplicates were found. This does not establish distinct designs: local-space point fingerprints do not prove world-space silhouette or topology differences.

36 exact creature animation-data groups remain shared. 18 perceptual-preview pairs are similarity candidates, not proofs of incorrect source images. Four exact-file groups are repeated neutral/constant texture maps; they are retained to preserve texture paths. No models, useful animations or LODs were blindly deleted.

Visually repetitive families remain: Crypt Arachnarch / Hundredleg / Crypt Skitter, Abyss Maw / Razorfin, Horned Regent / Crimson Imp, Root Matriarch / Sporeling, and the mechanical humanoid family. They require underlying design work, not recolouring. No new character redesign or animation choreography is claimed in this checkpoint.

New wireframe images were rendered by reimporting each of the 30 canonical GLBs. The catalogue maps every view to its actual source. Cinder's default catalogue uses the retained previous V4 image; the earlier After/Motion comparisons show its explicitly labelled rejected Experimental export. No byte-identical wrongly repeated current previews were found by the exact-byte audit. Perceptual image matching alone cannot certify semantic correspondence; source maps and these fresh imports provide separate evidence.

## Structural validation

Prior FBX/GLB reimports, sampled deformation and texture-path checks are preserved under audit/. This pass adds GLB parsing, byte/geometry/motion fingerprints, canonical GLB reimports for topology renders, and fresh archive integrity/extraction checks. No all-frame clipping, hit-window, paired-alignment or LOD visual approval is inferred.

## Visual review

Prior neutral comparisons still show procedural toy-like anatomy and mechanical forms. These assets do not meet the cinematic/Meshy-ambition target. Topology is visibly dense in reconstructed skins; production retopology and local texture painting remain unfinished. All 30 characters remain below requested visual approval. Player choreography, contact, firearm grip, melee coverage, flight and swimming polish remain unfinished. Audio remains synthesized; FX remain procedural flipbooks, not cinematic volumetrics.

## Engine/device testing

Not performed. No destination game project, engine runtime or iPhone device execution is supplied here. Damage, stamina, invulnerability, lock-on, projectiles, boss phases, particle materials and audio playback require game integration.

## Exact capability gap and resume

Blender and scripted mesh editing/rendering are available. No dedicated Meshy-class 3D generation or motion-capture service is connected in the available tools. The available procedural pipeline has demonstrably not produced the requested mature anatomy, bespoke sculpting/retopology, realistic local textures or character-specific motion. Further cosmetic automation is not a completion path. A connected dedicated 3D asset service or production-quality artist-authored sculpt/rig/motion sources is needed to establish a stronger baseline, followed by per-character refinement and actual visual approval. A new chat alone does not add that capability.

Resume from this archive, audit/Completion_Checklist.json, audit/Repetition_Audit.json and editable .blend sources; never restart from V3. First redesign the arthropod family into genuinely different bodies, faces, limb arrangements and attack motion. Preserve existing compatibility; validate before replacing canonical files. Then cover each flagged family and remaining characters, player handling/combat, audio and FX. Do not mark unfinished work complete.
'''
(P/'audit/Repetition_Review.md').write_text(report)
(P/'RESUME_V4.md').write_text(report)
cards=[]
for c in catalog:
    name=c['asset'];view='Before' if name=='Cinder_Crown' else 'After'
    images=''.join(f'<figure><img loading="lazy" src="previews/roster/{name}/{view}_{v}.jpg"><figcaption>{v}</figcaption></figure>' for v in ['Threequarter','Front','Side','Back','Closeup'])
    cards.append(f'<section><h2>{html.escape(name)} — {c["category"]}</h2><p>Canonical: {html.escape(c["canonical_glb"])}. Status: {html.escape(c["status"])}; cinematic approval unfinished.</p><div>{images}<figure><img loading="lazy" src="previews/wireframes/{name}.jpg"><figcaption>Canonical GLB exported triangle wireframe</figcaption></figure></div></section>')
(P/'Character_Catalogue.html').write_text('<!doctype html><meta charset="utf-8"><title>Nocturne current canonical catalogue</title><style>body{background:#171b20;color:#eef;font:15px system-ui;margin:24px}div{display:flex;flex-wrap:wrap}figure{margin:8px;width:280px}img{width:100%}section{border-top:1px solid #566}</style><h1>30 canonical creatures — unfinished cinematic quality</h1><p>Actual saved model views. Cinder uses its retained canonical model, not the rejected experimental revision. Animation previews and prior before/after comparisons remain under previews/roster; those Cinder motion/After previews explicitly show Experimental.</p>'+''.join(cards))
sheet=Image.new('RGB',(1500,1800),(24,28,34));draw=ImageDraw.Draw(sheet)
for i,c in enumerate(catalog):
    im=Image.open(P/'previews/wireframes'/(c['asset']+'.jpg'));im.thumbnail((290,270));x=(i%5)*300;y=(i//5)*300
    sheet.paste(im,(x,y+25));draw.text((x+8,y+6),c['asset'],fill='white')
sheet.save(P/'previews/All30_Export_Wireframes.jpg',quality=90)
extra=[P/'audit/Completion_Checklist.json',P/'audit/Repetition_Audit.json',P/'audit/Repetition_Review.md',P/'audit/Wireframe_Preview_Mapping.json',P/'Character_Catalogue.html',P/'RESUME_V4.md',P/'previews/All30_Export_Wireframes.jpg']+list((P/'previews/wireframes').glob('*.jpg'))+[P/'source'/f for f in ['repetition_audit.py','render_export_wireframes.py','save_audited_checkpoint.py']]
integrity=json.loads((P/'audit/File_Integrity.json').read_text());byname={f['path']:f for f in integrity['files']}
for f in extra:
    rel=str(f.relative_to(P));byname[rel]={'path':rel,'size_bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
integrity['files']=sorted(byname.values(),key=lambda x:x['path']);integrity['scope_complete']=False
(P/'audit/File_Integrity.json').write_text(json.dumps(integrity,indent=2));extra.append(P/'audit/File_Integrity.json')
new={str(Path('Nocturne_V4_Full_Pack')/f.relative_to(P)):f for f in extra};out=W/'Nocturne_V4_Audited_Checkpoint.zip'
with zipfile.ZipFile(W/'Nocturne_V4_Full_Pack.zip') as original,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as target:
    for entry in original.infolist():
        if entry.filename not in new:
            with original.open(entry) as src,target.open(entry.filename,'w',force_zip64=True) as dst:shutil.copyfileobj(src,dst,4*1024*1024)
    for rel,f in new.items():target.write(f,rel)
with zipfile.ZipFile(out) as z:assert z.testzip() is None;entries=len(z.infolist())
extract=W/'work/audited_checkpoint_clean';extract.mkdir(parents=True,exist_ok=True)
subprocess.run(['unzip','-q',str(out),'-d',str(extract)],check=True)
root=extract/'Nocturne_V4_Full_Pack'
for item in integrity['files']:
    f=root/item['path'];assert f.stat().st_size==item['size_bytes'];assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256']
sha=hashlib.sha256(out.read_bytes()).hexdigest()
(W/'Nocturne_V4_Audited_Checkpoint.sha256').write_text(sha+'  '+out.name+'\n')
validation={'scope_complete':False,'size_bytes':out.stat().st_size,'sha256':sha,'entries_crc_passed':entries,'normal_unzip_passed':True,'file_sha256_passed':len(integrity['files']),'previous_models_preserved':True,'new_model_changes':False,'wireframe_count':len(mapping),'engine_testing':False,'iphone_testing':False}
(W/'Nocturne_V4_Audited_Checkpoint_Validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation),flush=True)
