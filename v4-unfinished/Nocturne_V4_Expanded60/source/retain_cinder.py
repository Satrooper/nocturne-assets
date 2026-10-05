from pathlib import Path
import shutil,json,hashlib,os
P=Path('Nocturne_V4_Visual_Revision');BASE=Path('Nocturne_V4_Full_Pack');folder=P/'dragons/Cinder_Crown';mapping={};records=[]
for suffix in ['.blend','_Authoring.blend','.fbx','.glb','_LOD1.fbx','_LOD2.fbx']:
 name='Cinder_Crown'+suffix;f=folder/name;dest=folder/('Cinder_Crown_Experimental'+suffix);shutil.copy2(f,dest);mapping[str(f.relative_to(P))]=str(dest.relative_to(P));shutil.copyfile(BASE/'dragons/Cinder_Crown'/name,f);assert hashlib.sha256(f.read_bytes()).digest()==hashlib.sha256((BASE/'dragons/Cinder_Crown'/name).read_bytes()).digest();records.append({'file':str(f.relative_to(P)),'identical_to_previous_validated_delivery':True})
meta=json.loads((folder/'asset.json').read_text());(folder/'experimental_asset.json').write_text(json.dumps(meta,indent=2));old=json.loads((BASE/'dragons/Cinder_Crown/asset.json').read_text());old.update(revision='retained_previous_v4_stronger_face',visual_changes=['Retained the previous V4 benchmark because the new orbital/skin treatment regressed visual quality. Experimental files are supplied separately and are not approved upgrades.'],quality_status='Previous partial V4 model retained; cinematic target still unfinished',experimental_files=list(mapping.values()),retention_reason='The neutral close-up shows stronger orbital, pupil and nostril definition in the saved prior V4 version.');(folder/'asset.json').write_text(json.dumps(old,indent=2))
for filename in ['Export_Reimport_Validation.json','Editable_Source_Texture_Checks.json']:
 f=P/'audit'/filename;rows=json.loads(f.read_text())
 for r in rows:
  if r['file'] in mapping:r['file']=mapping[r['file']]
 f.write_text(json.dumps(rows,indent=2))
(P/'audit/Cinder_Retention_Byte_Check.json').write_text(json.dumps(records,indent=2));print('CINDER_BASELINE_RETAINED',len(records))
