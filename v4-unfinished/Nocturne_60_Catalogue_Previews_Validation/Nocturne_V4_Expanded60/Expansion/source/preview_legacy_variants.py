from pathlib import Path
W=Path(__file__).resolve().parents[1];code=(P/'source/validate_render_expansion.py').read_text().split('for row in rows:')[0];exec(compile(code,'studio_helpers','exec'))
BASE=W;old={x['asset']:x for x in json.loads((BASE/'asset_manifest.json').read_text())['characters']};items=json.loads((P/'audit/Legacy_Distinct_Variants.json').read_text());receipts=[]
for item in items:
    name=item['asset'];folder=P/'previews/legacy_variants'/name;folder.mkdir(parents=True,exist_ok=True)
    r,m,lo,hi=load(BASE/old[name]['canonical_glb']);r,m,lo2,hi2=load(P/item['candidate_glb']);boundslo=Vector(tuple(min(lo[i],lo2[i]) for i in range(3)));boundshi=Vector(tuple(max(hi[i],hi2[i]) for i in range(3)))
    rec={'asset':name,'before_source':old[name]['canonical_glb'],'after_source':item['candidate_glb'],'visual_status':'prototype body-plan variation; motion quality not approved','canonical_replaced':False}
    for label,f in [('Before',BASE/old[name]['canonical_glb']),('After',P/item['candidate_glb'])]:
        r,meshes,lo,hi=load(f);rec[label+'_bones']=len(r.data.bones);rec[label+'_clips']=len(bpy.data.actions);sc,cam,_,_=studio(boundslo,boundshi);center=(boundslo+boundshi)/2;extent=max(boundshi-boundslo);pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
        # Identical neutral setup, camera and union framing for both delivered GLBs.
        for view,direction in [('Threequarter',(1,-1,.35)),('Front',(0,-1,.14))]:
            cam.location=center+Vector(direction).normalized()*extent*3;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=extent*1.2;sc.render.filepath=str(folder/(label+'_'+view+'.jpg'));bpy.ops.render.render(write_still=True)
    r,meshes,lo,hi=load(P/item['candidate_fbx']);rec['fbx_reimport_passed']=True;rec['fbx_clips']=len(bpy.data.actions);receipts.append(rec);(P/'audit/Legacy_Variant_Validation.json').write_text(json.dumps(receipts,indent=2));print('LEGACY_PREVIEW',name,flush=True)
