# ============================================================
# Figure 2B — Direction of error (case-level confusion matrix)
# Regenerate:  python3 fig2b_density.py
# Data hard-coded from case-level counts (75 cases):
#   row = reference category, col = HANDOFF category
#   (1->1)=20  (2->2)=27  (2->3)=1  (3->3)=27   row totals 20,28,27
# ============================================================
from pathlib import Path
import numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
mpl.rcParams.update({"font.family":"DejaVu Sans","font.size":9.5,
 "axes.spines.top":False,"axes.spines.right":False,"axes.linewidth":0.9,
 "axes.edgecolor":"#5b6470","figure.dpi":200,"savefig.dpi":340})
INK="#2b2f36"
HERE = Path(__file__).resolve().parent

C=np.array([[20,0,0],[0,27,1],[0,0,27]],float)   # case-level counts
rowtot=C.sum(1,keepdims=True)
P=C/rowtot*100
cmap=LinearSegmentedColormap.from_list("nv",["#ffffff","#cdddee","#5b8cc0","#1f4e79"])

fig,ax=plt.subplots(figsize=(5.6,4.7))
im=ax.imshow(P,cmap=cmap,vmin=0,vmax=100,aspect="equal",zorder=1)

# error regions: same red fill + hatch for both under- and over-triage
for i in range(3):
    for j in range(3):
        if j!=i:
            ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor="#f7e4df",fill=True,zorder=0))
            ax.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,hatch="///",edgecolor="#eac6bd",lw=0,zorder=2))
# overlay colored cells where count>0
for i in range(3):
    for j in range(3):
        if C[i,j]>0:
            ax.add_patch(Rectangle((j-.5,i-.5),1,1,facecolor=cmap(P[i,j]/100),zorder=1.5))

# cell value annotations
for i in range(3):
    for j in range(3):
        cnt=int(C[i,j]); pct=P[i,j]
        if cnt>0:
            tc="white" if pct>55 else INK
            ax.text(j,i-0.10,f"{pct:.0f}%",ha="center",va="center",fontsize=13,fontweight="bold",color=tc,zorder=4)
            ax.text(j,i+0.22,f"{cnt}/{int(rowtot[i,0])}",ha="center",va="center",fontsize=8,color=tc,zorder=4)

# corner-box labels, black text
boxstyle=dict(boxstyle="round,pad=0.35",fc="white",ec="#cfd5dc",lw=0.8)
ax.text(2.0,0.0,"Over-triage",ha="center",va="center",fontsize=8.6,color=INK,
        fontweight="bold",zorder=5,bbox=boxstyle)                 # empty top-right cell
ax.text(0.0,2.0,"Under-triage",ha="center",va="center",fontsize=8.6,color=INK,
        fontweight="bold",zorder=5,bbox=boxstyle)                 # empty bottom-left cell

ax.set_xticks([0,1,2]); ax.set_xticklabels(["1","2","3"])
ax.set_yticks([0,1,2]); ax.set_yticklabels(["1","2","3"])
ax.set_xlabel("HANDOFF category",fontsize=10)
ax.set_ylabel("Reference category",fontsize=10)
ax.tick_params(length=0); ax.set_xlim(-.5,2.5); ax.set_ylim(2.5,-.5)
for s in ax.spines.values(): s.set_visible(False)
for k in [0.5,1.5]:
    ax.axhline(k,color="white",lw=2,zorder=3); ax.axvline(k,color="white",lw=2,zorder=3)
ax.set_title("Direction of error",fontsize=11,fontweight="bold",loc="left",pad=12)
cb=fig.colorbar(im,ax=ax,fraction=0.046,pad=0.04,ticks=[0,50,100])
cb.set_label("% of reference-category cases",fontsize=8.5); cb.ax.tick_params(labelsize=8,length=2)
cb.outline.set_visible(False)
fig.savefig(HERE / "fig2_direction_of_error.png",bbox_inches="tight",facecolor="white",pad_inches=0.16)
print("saved fig2_direction_of_error.png")
