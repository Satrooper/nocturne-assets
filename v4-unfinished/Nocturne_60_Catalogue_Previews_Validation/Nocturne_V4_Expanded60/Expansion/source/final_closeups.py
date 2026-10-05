from pathlib import Path
W=Path(__file__).resolve().parents[1];code=(P/'source/validate_render_expansion.py').read_text().split('for row in rows:')[0];exec(compile(code,'studio_helpers','exec'))
for row in rows:
    r,meshes,lo,hi=load(P/row['canonical_glb']);sc,cam,center,extent=studio(lo,hi);pts=[o.matrix_world@v.co for o in meshes for v in o.data.vertices];target=r.matrix_world@r.data.bones['head'].head_local;aim(cam,target,extent,(1,-1,.20),pts,True);sc.render.filepath=str(P/'previews/characters'/row['asset']/'Closeup.jpg');bpy.ops.render.render(write_still=True);print('CLOSEUP_FIXED',row['asset'],flush=True)
