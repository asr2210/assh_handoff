# ============================================================
# Figure 2A (accuracy) and Figure 3 (flagging + information-seeking)
# Regenerate: python3 fig2a_fig3.py   (reads results.json)
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
INK="#2b2f36"; NAVY="#1f4e79"; CONTEST="#b5651d"; LBLUE="#7fb0d6"; SLATE="#9aa3ad"; GRID="#e6e9ee"
def yg(ax): ax.set_axisbelow(True); ax.yaxis.grid(True,color=GRID,lw=0.9); ax.xaxis.grid(False)
def title(ax,t): ax.set_title(t,fontsize=11,fontweight="bold",loc="left",pad=12)
def wil(k,n):
    lo,hi=proportion_confint(k,n,method="wilson"); return k/n*100, lo*100, hi*100

# ---------------- FIGURE 2A — accuracy by case set ----------------
fig,ax=plt.subplots(figsize=(4.6,4.4)); yg(ax)
acc=[R["primary"]["mv_acc"][0]*100, R["grayzone"]["mv_acc"][0]*100]
lo=[R["primary"]["mv_acc"][1]*100, R["grayzone"]["mv_acc"][1]*100]
hi=[R["primary"]["mv_acc"][2]*100, R["grayzone"]["mv_acc"][2]*100]
x=np.arange(2); err=[np.clip(np.array(acc)-lo,0,None),np.clip(np.array(hi)-np.array(acc),0,None)]
ax.bar(x,acc,width=0.5,color=[NAVY,CONTEST],zorder=3)
ax.errorbar(x,acc,yerr=err,fmt="none",ecolor=INK,elinewidth=1.3,capsize=6,capthick=1.3,zorder=4)
for xi,a,h in zip(x,acc,hi): ax.text(xi,h+1.8,f"{a:.0f}%",ha="center",fontweight="bold",fontsize=11)
ax.axhline(100,ls=(0,(4,3)),lw=0.9,color="#b6bcc6",zorder=1)
ax.set_xticks(x); ax.set_xticklabels(["Well-specified\n(n = 60)","Contested\n(n = 15)"])
ax.set_ylim(0,114); ax.set_yticks([0,25,50,75,100]); ax.set_ylabel("Triage accuracy (%)")
ax.tick_params(axis="x",length=0)
title(ax,"Triage accuracy")
fig.savefig(HERE / "extra_accuracy.png",bbox_inches="tight",facecolor="white",pad_inches=0.16)
plt.close(fig); print("saved fig2a_accuracy.png")

# ---------------- FIGURE 3 — uncertainty behaviors ----------------
fig=plt.figure(figsize=(10.2,4.3))
gs=fig.add_gridspec(1,2,width_ratios=[0.85,1.15],wspace=0.30,left=0.08,right=0.985,top=0.86,bottom=0.16)

# 3A: flagging well-specified vs contested
axA=fig.add_subplot(gs[0]); yg(axA)
fa=[R["grayzone"]["pr_boundary_rate"][0]*100, R["grayzone"]["gz_boundary_rate"][0]*100]
flo=[R["grayzone"]["pr_boundary_rate"][1]*100, R["grayzone"]["gz_boundary_rate"][1]*100]
fhi=[R["grayzone"]["pr_boundary_rate"][2]*100, R["grayzone"]["gz_boundary_rate"][2]*100]
x=np.arange(2); err=[np.clip(np.array(fa)-flo,0,None),np.clip(np.array(fhi)-np.array(fa),0,None)]
axA.bar(x,fa,width=0.5,color=[NAVY,CONTEST],zorder=3)
axA.errorbar(x,fa,yerr=err,fmt="none",ecolor=INK,elinewidth=1.3,capsize=6,capthick=1.3,zorder=4)
axA.text(0,fhi[0]+2,"8%",ha="center",fontweight="bold",fontsize=11)
axA.text(1,fhi[1]+2,"73%",ha="center",fontweight="bold",fontsize=11)
# significance bracket
yb=96
axA.plot([0,0,1,1],[yb-3,yb,yb,yb-3],lw=1.1,color=INK)
axA.text(0.5,yb+1,"Fisher  P < .001",ha="center",va="bottom",fontsize=8.4,color=INK)
axA.set_xticks(x); axA.set_xticklabels(["Well-specified\n(n = 60)","Contested\n(n = 15)"])
axA.set_ylim(0,114); axA.set_yticks([0,25,50,75,100]); axA.set_ylabel("Cases flagged as uncertain (%)")
axA.tick_params(axis="x",length=0)
title(axA,"Identifying uncertain cases")

# 3B: information-seeking — grouped (asked vs detail recall) x (overall, changing, defining)
axB=fig.add_subplot(gs[1]); yg(axB)
ab=R["ablation"]; cc=ab["bytype"]["category_changing"]; cd=ab["bytype"]["category_defining"]
asked=[(ab["asked"],ab["n_ok"]),(cc["asked"],cc["n"]),(cd["asked"],cd["n"])]
recall=[(ab["n_covered"],ab["n_details"]),(cc["n_covered"],cc["n_details"]),(cd["n_covered"],cd["n_details"])]
groups=["Overall","Category-\nchanging","Category-\ndefining"]
xg=np.arange(3); w=0.38
av=[wil(k,n) for k,n in asked]; rv=[wil(k,n) for k,n in recall]
a_val=[v[0] for v in av]; a_err=[[v[0]-v[1] for v in av],[v[2]-v[0] for v in av]]
r_val=[v[0] for v in rv]; r_err=[[v[0]-v[1] for v in rv],[v[2]-v[0] for v in rv]]
b1=axB.bar(xg-w/2,a_val,width=w,color=NAVY,zorder=3,label="Asked for missing detail")
b2=axB.bar(xg+w/2,r_val,width=w,color=LBLUE,zorder=3,label="Detail recall")
axB.errorbar(xg-w/2,a_val,yerr=a_err,fmt="none",ecolor=INK,elinewidth=1.1,capsize=4,capthick=1.1,zorder=4)
axB.errorbar(xg+w/2,r_val,yerr=r_err,fmt="none",ecolor=INK,elinewidth=1.1,capsize=4,capthick=1.1,zorder=4)
for xi,(k,n) in zip(xg-w/2,asked): axB.text(xi,6,f"{k}/{n}",ha="center",fontsize=7.5,color="white",fontweight="bold",rotation=90)
for xi,(k,n) in zip(xg+w/2,recall): axB.text(xi,6,f"{k}/{n}",ha="center",fontsize=7.5,color=INK,fontweight="bold",rotation=90)
axB.set_xticks(xg); axB.set_xticklabels(groups)
axB.set_ylim(0,114); axB.set_yticks([0,25,50,75,100]); axB.set_ylabel("Percentage (%)")
axB.tick_params(axis="x",length=0)
axB.legend(loc="lower center",ncol=2,fontsize=8,frameon=False,bbox_to_anchor=(0.5,-0.30))
title(axB,"Asking when information is missing")

fig.savefig(HERE / "extra_flagging_and_info.png",bbox_inches="tight",facecolor="white",pad_inches=0.16)
plt.close(fig); print("saved fig3_uncertainty.png")
