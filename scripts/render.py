import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Rectangle
from kiutils.board import Board
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
b=Board.from_file('2G4_RF_Receiver_FrontEnd.kicad_pcb'); nn={n.number:n.name for n in b.nets}
BW,BH=40,24
pads=[];trk=[];vs=[];labels=[]
for fp in b.footprints:
    ref=fp.properties['Reference']; labels.append((ref,fp.position.X,fp.position.Y))
    for p in fp.pads:
        cx,cy=fp.position.X+p.position.X,fp.position.Y+p.position.Y
        g=Point(cx,cy).buffer(p.size.X/2,32) if p.shape=='circle' else box(cx-p.size.X/2,cy-p.size.Y/2,cx+p.size.X/2,cy+p.size.Y/2)
        pads.append((g,nn[p.net.number],[l for l in p.layers]+(['F.Cu'] if p.type=='thru_hole' else []),p.type))
for it in b.traceItems:
    c=it.__class__.__name__
    if c=='Segment': trk.append((LineString([(it.start.X,it.start.Y),(it.end.X,it.end.Y)]).buffer(it.width/2,8),nn[it.net]))
    else: vs.append((Point(it.position.X,it.position.Y).buffer(it.size/2,24),Point(it.position.X,it.position.Y).buffer(it.drill/2,16)))
nong=unary_union([g for g,n,l,t in pads if n!='GND' and ('F.Cu' in l)]+[g for g,n in trk if n!='GND'])
pour=box(.3,.3,BW-.3,BH-.3).difference(nong.buffer(.3,24))
def draw(ax,geom,**kw):
    for part in (geom.geoms if hasattr(geom,'geoms') else [geom]):
        ax.add_patch(MP(list(part.exterior.coords),closed=True,**kw))
        for h in part.interiors: ax.add_patch(MP(list(h.coords),closed=True,fc='white',ec='none',zorder=kw.get('zorder',1)+0.01))
fig,ax=plt.subplots(figsize=(16,9.6)); ax.set_facecolor('#0b2a1a')
ax.add_patch(Rectangle((0,0),BW,BH,fc='#0b2a1a',ec='yellow',lw=1.5,zorder=0))
draw(ax,pour,fc='#2f7d4f',ec='none',alpha=.55,zorder=1)
for g,n in trk: draw(ax,g,fc='#e8a33d' if n!='GND' else '#7fd39a',ec='none',zorder=3)
for g,n,l,t in pads:
    if 'F.Cu' in l: draw(ax,g,fc='#f4d35e' if n!='GND' else '#a5e6b8',ec='k',lw=.3,zorder=4)
for g,h in vs: draw(ax,g,fc='#cfcfcf',ec='k',lw=.3,zorder=5); draw(ax,h,fc='#111',ec='none',zorder=6)
for r,x,y in labels: ax.text(x,y-2.0 if r not in('J1','J2') else y+4.6,r,color='white',fontsize=11,ha='center',zorder=9)
ax.set_xlim(-1,BW+1); ax.set_ylim(BH+1,-1); ax.set_aspect('equal')
ax.set_title('2G4 RF front-end - F.Cu view (pour fill is MODELLED here; in KiCad press B to fill). RO4003C 0.813 mm, GCPW W=1.6 / gap=0.3 mm',fontsize=10)
ax.set_xlabel('x (mm)'); ax.set_ylabel('y (mm)')
plt.tight_layout(); plt.savefig('layout_preview.png',dpi=110)
