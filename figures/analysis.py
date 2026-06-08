"""HANDOFF evaluation analysis.
Three components, all on the single augmented_ambiguity condition (GPT-5.5 backbone):
  1. Primary classification accuracy (60 cases x 3 runs)
  2. Gray-zone performance + boundary-case flagging (15 cases x 3 runs)
  3. Ablation / appropriate uncertainty (31 missing-information cases)
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from statsmodels.stats.proportion import proportion_confint

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT
rng = np.random.default_rng(20260608)
RESULTS = {}

def wilson(k, n):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return (k / n, lo, hi)

def majority_vote(s):
    # mode; tie-break toward higher acuity (safer) is unnecessary here (3 runs, odd)
    vals = list(s)
    counts = {v: vals.count(v) for v in set(vals)}
    mx = max(counts.values())
    cand = sorted([v for v, c in counts.items() if c == mx])
    return cand[-1] if len(cand) > 1 else cand[0]  # tie -> higher category (safer)

# ----------------------------------------------------------------------------
# Helper for per-case collapse
# ----------------------------------------------------------------------------
def collapse(df):
    rows = []
    for vid, g in df.groupby("vignette_id"):
        exp = int(g["expected_category"].iloc[0])
        preds = list(g["triage_recommendation"].astype(int))
        mv = majority_vote(pd.Series(preds))
        rows.append(dict(
            vignette_id=vid,
            expected=exp,
            mv_pred=int(mv),
            mv_correct=int(mv == exp),
            frac_correct=np.mean([p == exp for p in preds]),
            unanimous=int(len(set(preds)) == 1),
            any_boundary=int(g["is_boundary_case"].any()),
            n_runs=len(g),
        ))
    return pd.DataFrame(rows).sort_values("vignette_id").reset_index(drop=True)

# ============================================================================
# 1. PRIMARY VALIDATION
# ============================================================================
p_raw = pd.read_csv(DATA / "handoff_primary_validation_results_gpt_5_5.csv")
p = collapse(p_raw)

# Replicate-level accuracy (180 runs)
run_acc, run_lo, run_hi = wilson(int(p_raw["correct"].sum()), len(p_raw))
# Majority-vote accuracy (60 cases)
mv_acc, mv_lo, mv_hi = wilson(int(p["mv_correct"].sum()), len(p))
# Replicate-balanced accuracy
bal_acc = p["frac_correct"].mean()
unanimous = p["unanimous"].mean()

# Agreement
kappa = cohen_kappa_score(p["expected"], p["mv_pred"])
wkappa = cohen_kappa_score(p["expected"], p["mv_pred"], weights="quadratic")

# Confusion matrix
cm = confusion_matrix(p["expected"], p["mv_pred"], labels=[1, 2, 3])

# Per-category sens/spec/PPV
percat = {}
y_true = p["expected"].values
y_pred = p["mv_pred"].values
for c in [1, 2, 3]:
    tp = int(((y_true == c) & (y_pred == c)).sum())
    fn = int(((y_true == c) & (y_pred != c)).sum())
    fp = int(((y_true != c) & (y_pred == c)).sum())
    tn = int(((y_true != c) & (y_pred != c)).sum())
    sens, sl, sh = wilson(tp, tp + fn)
    spec, spl, sph = wilson(tn, tn + fp)
    ppv, pl, ph = wilson(tp, tp + fp) if (tp + fp) > 0 else (np.nan, np.nan, np.nan)
    percat[c] = dict(tp=tp, fn=fn, fp=fp, tn=tn,
                     sens=(sens, sl, sh), spec=(spec, spl, sph), ppv=(ppv, pl, ph))

# Under/over-triage (case-level, majority vote)
# under = true Cat3 classified lower; over = true Cat1 classified higher
n_cat3 = int((y_true == 3).sum())
n_cat1 = int((y_true == 1).sum())
under = int(((y_true == 3) & (y_pred < 3)).sum())
over = int(((y_true == 1) & (y_pred > 1)).sum())
under_rate = wilson(under, n_cat3)
over_rate = wilson(over, n_cat1)

# Replicate-level under/over for sensitivity
yt_r = p_raw["expected_category"].astype(int).values
yp_r = p_raw["triage_recommendation"].astype(int).values
under_r = int(((yt_r == 3) & (yp_r < 3)).sum())
over_r = int(((yt_r == 1) & (yp_r > 1)).sum())

RESULTS["primary"] = dict(
    n_cases=len(p), n_runs=len(p_raw),
    run_acc=(run_acc, run_lo, run_hi),
    mv_acc=(mv_acc, mv_lo, mv_hi),
    bal_acc=bal_acc, unanimous=unanimous,
    kappa=kappa, wkappa=wkappa,
    cm=cm.tolist(), percat=percat,
    under=under, n_cat3=n_cat3, under_rate=under_rate, under_runs=under_r,
    over=over, n_cat1=n_cat1, over_rate=over_rate, over_runs=over_r,
)

# ============================================================================
# 2. GRAY ZONE
# ============================================================================
g_raw = pd.read_csv(DATA / "handoff_gray_zone_results_gpt_5_5.csv")
g = collapse(g_raw)
gz_run_acc = wilson(int(g_raw["correct"].sum()), len(g_raw))
gz_mv_acc = wilson(int(g["mv_correct"].sum()), len(g))
gz_bal = g["frac_correct"].mean()
gz_wkappa = cohen_kappa_score(g["expected"], g["mv_pred"], weights="quadratic")

# Boundary flagging: gray zone vs primary (per case, any run)
gz_boundary = int(g["any_boundary"].sum()); gz_n = len(g)
pr_boundary = int(p["any_boundary"].sum()); pr_n = len(p)
# Fisher exact
fisher_tab = [[gz_boundary, gz_n - gz_boundary], [pr_boundary, pr_n - pr_boundary]]
fisher_or, fisher_p = stats.fisher_exact(fisher_tab, alternative="greater")
# run-level boundary rates
gz_b_runs = wilson(int(g_raw["is_boundary_case"].sum()), len(g_raw))
pr_b_runs = wilson(int(p_raw["is_boundary_case"].sum()), len(p_raw))

RESULTS["grayzone"] = dict(
    n_cases=len(g), n_runs=len(g_raw),
    run_acc=gz_run_acc, mv_acc=gz_mv_acc, bal_acc=gz_bal, wkappa=gz_wkappa,
    gz_boundary=gz_boundary, gz_n=gz_n, gz_boundary_rate=wilson(gz_boundary, gz_n),
    pr_boundary=pr_boundary, pr_n=pr_n, pr_boundary_rate=wilson(pr_boundary, pr_n),
    fisher_or=fisher_or, fisher_p=fisher_p,
    gz_b_runs=gz_b_runs, pr_b_runs=pr_b_runs,
)

# ============================================================================
# 3. ABLATION / APPROPRIATE UNCERTAINTY
# ============================================================================
ab = pd.read_csv(DATA / "handoff_ablation_question_scores_gpt_5_5.csv")
ab_ok = ab[ab["status"] == "ok"].copy()
n_total = len(ab); n_ok = len(ab_ok); n_err = int((ab["status"] != "ok").sum())

asked = int(ab_ok["asked_for_missing_information"].sum())
asked_rate = wilson(asked, n_ok)
recall_mean = ab_ok["detail_recall"].mean()
recall_sd = ab_ok["detail_recall"].std()
n_details = int(ab_ok["n_withheld_details"].sum())
n_covered = int(ab_ok["n_details_covered"].sum())
detail_cov = wilson(n_covered, n_details)

bytype = {}
for t, gt in ab_ok.groupby("benchmark_type"):
    a = int(gt["asked_for_missing_information"].sum()); n = len(gt)
    bytype[t] = dict(
        n=n, asked=a, asked_rate=wilson(a, n),
        recall_mean=gt["detail_recall"].mean(),
        n_details=int(gt["n_withheld_details"].sum()),
        n_covered=int(gt["n_details_covered"].sum()),
    )

RESULTS["ablation"] = dict(
    n_total=n_total, n_ok=n_ok, n_err=n_err,
    asked=asked, asked_rate=asked_rate,
    recall_mean=recall_mean, recall_sd=recall_sd,
    n_details=n_details, n_covered=n_covered, detail_cov=detail_cov,
    bytype=bytype,
)

# ============================================================================
# DUMP
# ============================================================================
def fmt(x):
    if isinstance(x, tuple) and len(x) == 3:
        return f"{x[0]*100:.1f}% (95% CI {x[1]*100:.1f}-{x[2]*100:.1f})"
    return x

print("="*70)
print("1. PRIMARY VALIDATION (60 cases, 180 runs)")
print("="*70)
r = RESULTS["primary"]
print(f"Replicate-level accuracy : {fmt(r['run_acc'])}")
print(f"Majority-vote accuracy   : {fmt(r['mv_acc'])}")
print(f"Replicate-balanced acc   : {r['bal_acc']*100:.1f}%")
print(f"Unanimous across 3 runs  : {r['unanimous']*100:.1f}% of cases")
print(f"Cohen's kappa            : {r['kappa']:.3f}")
print(f"Quadratic-weighted kappa : {r['wkappa']:.3f}")
print(f"Confusion matrix (rows=true 1/2/3, cols=pred 1/2/3):")
for row in r['cm']:
    print("   ", row)
for c in [1,2,3]:
    pc = r['percat'][c]
    print(f"  Cat{c}: sens {fmt(pc['sens'])} | spec {fmt(pc['spec'])} | PPV {fmt(pc['ppv'])}")
print(f"Under-triage (true Cat3 -> lower), cases: {r['under']}/{r['n_cat3']} = {fmt(r['under_rate'])}; runs: {r['under_runs']}/{(np.array(p_raw['expected_category'])==3).sum()}")
print(f"Over-triage  (true Cat1 -> higher), cases: {r['over']}/{r['n_cat1']} = {fmt(r['over_rate'])}; runs: {r['over_runs']}/{(np.array(p_raw['expected_category'])==1).sum()}")

print("\n"+"="*70)
print("2. GRAY ZONE (15 cases, 45 runs)")
print("="*70)
r = RESULTS["grayzone"]
print(f"Replicate-level accuracy : {fmt(r['run_acc'])}")
print(f"Majority-vote accuracy   : {fmt(r['mv_acc'])}")
print(f"Replicate-balanced acc   : {r['bal_acc']*100:.1f}%")
print(f"Quadratic-weighted kappa : {r['wkappa']:.3f}")
print(f"Boundary-flagged cases   : gray {r['gz_boundary']}/{r['gz_n']} ({fmt(r['gz_boundary_rate'])}) vs primary {r['pr_boundary']}/{r['pr_n']} ({fmt(r['pr_boundary_rate'])})")
print(f"Boundary-flag runs       : gray {fmt(r['gz_b_runs'])} vs primary {fmt(r['pr_b_runs'])}")
print(f"Fisher exact (gray>primary): OR={r['fisher_or']:.2f}, p={r['fisher_p']:.4g}")

print("\n"+"="*70)
print("3. ABLATION / APPROPRIATE UNCERTAINTY")
print("="*70)
r = RESULTS["ablation"]
print(f"Cases: {r['n_total']} total, {r['n_ok']} evaluable ({r['n_err']} API error excluded)")
print(f"Asked for missing info   : {r['asked']}/{r['n_ok']} = {fmt(r['asked_rate'])}")
print(f"Withheld-detail recall   : mean {r['recall_mean']:.3f} (SD {r['recall_sd']:.3f})")
print(f"Detail coverage          : {r['n_covered']}/{r['n_details']} = {fmt(r['detail_cov'])}")
for t, b in r['bytype'].items():
    print(f"  {t}: asked {b['asked']}/{b['n']} = {fmt(b['asked_rate'])}; recall {b['recall_mean']:.3f}; details {b['n_covered']}/{b['n_details']}")

# save
with open(HERE / "results.json", "w") as f:
    json.dump(RESULTS, f, default=lambda o: o.tolist() if hasattr(o,'tolist') else float(o), indent=2)
print("\n[saved results.json]")
