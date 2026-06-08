# ============================================================
# Figure 3 — Identification of category-defining and category-changing information
# Regenerate: python3 fig3.py   (reads results.json)
# ============================================================
import json
from pathlib import Path
import numpy as np, matplotlib as mpl, matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
mpl.rcParams.update({"font.family":"DejaVu Sans","font.size":9.5,
 "axes.spines.top":False,"axes.spines.right":False,"axes.linewidth":0.9,
 "axes.edgecolor":"#5b6470","xtick.color":"#5b6470","ytick.color":"#5b6470",
 "xtick.major.size":0,"ytick.major.size":3,"figure.dpi":200,"savefig.dpi":340})
HERE = Path(__file__).resolve().parent
R=json.load(open(HERE / "results.json"))
INK="#2b2f36"; NAVY="#1f4e79"; LBLUE="#7fb0d6"; GRID="#e6e9ee"
def wil(k,n):
    lo,hi=proportion_confint(k,n,method="wilson"); return k/n*100, lo*100, hi*100

ab=R["ablation"]; cc=ab["bytype"]["category_changing"]; cd=ab["bytype"]["category_defining"]
asked=[(ab["asked"],ab["n_ok"]),(cc["asked"],cc["n"]),(cd["asked"],cd["n"])]
recall=[(ab["n_covered"],ab["n_details"]),(cc["n_covered"],cc["n_details"]),(cd["n_covered"],cd["n_details"])]
groups=["Overall","Category-\nchanging","Category-\ndefining"]

fig,ax=plt.subplots(figsize=(6.6,4.4))
ax.set_axisbelow(True); ax.yaxis.grid(True,color=GRID,lw=0.9)
xg=np.arange(3); w=0.38
av=[wil(k,n) for k,n in asked]; rv=[wil(k,n) for k,n in recall]
a_val=[v[0] for v in av]; a_err=[[v[0]-v[1] for v in av],[v[2]-v[0] for v in av]]
r_val=[v[0] for v in rv]; r_err=[[v[0]-v[1] for v in rv],[v[2]-v[0] for v in rv]]
ax.bar(xg-w/2,a_val,width=w,color=NAVY,zorder=3,label="Asked for missing detail")
ax.bar(xg+w/2,r_val,width=w,color=LBLUE,zorder=3,label="Detail recall")
ax.errorbar(xg-w/2,a_val,yerr=a_err,fmt="none",ecolor=INK,elinewidth=1.1,capsize=4,capthick=1.1,zorder=4)
ax.errorbar(xg+w/2,r_val,yerr=r_err,fmt="none",ecolor=INK,elinewidth=1.1,capsize=4,capthick=1.1,zorder=4)
for xi,(k,n) in zip(xg-w/2,asked): ax.text(xi,4,f"{k}/{n}",ha="center",va="bottom",fontsize=8,color="white",fontweight="bold")
for xi,(k,n) in zip(xg+w/2,recall): ax.text(xi,4,f"{k}/{n}",ha="center",va="bottom",fontsize=8,color=INK,fontweight="bold")
ax.set_xticks(xg); ax.set_xticklabels(groups)
ax.set_ylim(0,114); ax.set_yticks([0,25,50,75,100]); ax.set_ylabel("Percentage (%)")
ax.tick_params(axis="x",length=0)
ax.legend(loc="lower center",ncol=2,fontsize=8.5,frameon=False,bbox_to_anchor=(0.5,-0.26))
ax.set_title("Identification of category-defining and category-changing information",
             fontsize=10.5,fontweight="bold",loc="left",pad=12)
fig.savefig(HERE / "fig3_information.png",bbox_inches="tight",facecolor="white",pad_inches=0.16)
print("saved fig3_information.png")
