"""Sinh MOI hinh, MOI bang va MOI macro so cua bai, tu tep ket qua.

⛔ LUAT MOT NGUON: khong con so nao duoc go tay vao `paper/main.tex`. Bai chi duoc doc so qua
macro trong `figures/out/numbers.tex`, va tep do sinh ra o day tu `results/*.json`. Chay lai thi
nghiem la cap nhat het ca hinh, bang lan van xuoi.

Bo style lay tu `paper-lab/transaction-figure-kit/results/make_results.py`: serif khop than bai,
palette Okabe-Ito an toan cho nguoi mu mau, phan biet series bang MAU + MARKER + KIEU NET de doc
duoc khi in den trang, vien manh, khong luoi dam, khong 3D.

Chay:  python3 figures/make_figures.py
"""

import io
import json
import os
import re
import sys

import numpy as np
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
OUTD = os.path.join(HERE, "out")
os.makedirs(OUTD, exist_ok=True)

mpl.rcParams.update({
    "font.family": "serif", "font.serif": ["DejaVu Serif"],
    "mathtext.fontset": "dejavuserif", "font.size": 9,
    "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "lines.linewidth": 1.1, "lines.markersize": 4.0, "legend.frameon": False,
    "figure.dpi": 130, "pdf.fonttype": 42, "ps.fonttype": 42,
})
C = {"blue": "#0072B2", "verm": "#D55E00", "green": "#009E73",
     "gray": "#555555", "orange": "#E69F00"}

# Elsevier elsarticle hai cot: cot 3.35 in, khung 7.0 in
W_COL, W_TEXT = 3.35, 7.0
NUM = {}


def M(name, value):
    # ⛔ Ten lenh LaTeX CHI duoc gom chu cai. `\numEvCH3GPP` bi TeX doc thanh `\numEvCH` roi
    #    `3GPP` la van ban, sinh ra "Missing number, treated as zero" va lam hong ca ban thao
    #    lan tep hinh. Loai bo moi ky tu khong phai chu cai ngay tai day de khong tai pham.
    key = re.sub(r"[^A-Za-z]", "", name)
    if key != name:
        print("     (ten macro %s -> %s: bo ky tu khong phai chu cai)" % (name, key))
    assert key not in NUM or NUM[key] == value, "macro %s bi dat hai lan khac gia tri" % key
    NUM[key] = value
    return value


def load(fn):
    p = os.path.join(RES, fn)
    return json.load(io.open(p, encoding="utf-8")) if os.path.exists(p) else None


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUTD, "%s.%s" % (name, ext)), bbox_inches="tight")
    plt.close(fig)
    print("     %s" % name)


def vn(x, d=2):
    """So cho van ban tieng Anh: dau phay ngan nghin, dau cham thap phan."""
    return ("{:,.%df}" % d).format(x)


# =====================================================================
def fig_orbital(e1):
    """Hinh 2: phan bo vat ly quy dao, ba bang."""
    st = "Da Nang"
    P = e1["stations"][st]["passes"]["25"]
    g = lambda k: np.array([p[k] for p in P])                      # noqa: E731

    M("numPasses", "{:,}".format(sum(len(v) for s in e1["stations"].values()
                                     for v in s["passes"].values())))
    M("numSats", "{:,}".format(e1["n_sat"]))
    M("numPassesStation", "{:,}".format(len(P)))

    # ⛔ wspace phai rong: nhan truc x cua bang trai tung dam vao nhan truc y cua bang phai,
    #    va chu thich "median" dat theo toa do DU LIEU thi tran ra ngoai khung o bang thu ba.
    #    Ca hai chi lo ra khi NHIN anh, khong cong nao bat duoc.
    fig, ax = plt.subplots(1, 3, figsize=(W_TEXT, 2.05))
    fig.subplots_adjust(wspace=0.42)
    specs = [("doppler_Ka_peak_khz", "Peak Doppler, Ka-band (kHz)", C["verm"], "numDopKa"),
             ("fspl_swing_db", "Link-budget swing (dB)", C["blue"], "numFspl"),
             ("dur_s", "Visibility window (s)", C["green"], "numDur")]
    for a, (key, lab, col, mac) in zip(ax, specs):
        v = g(key)
        a.hist(v, bins=42, color=col, alpha=0.80, edgecolor="none")
        med = float(np.median(v))
        a.axvline(med, color="k", lw=0.9, ls="--")
        a.set_xlabel(lab)
        a.set_ylabel("passes" if a is ax[0] else "")
        a.margins(y=0.20)
        # toa do TRUC (0..1) chu khong phai toa do du lieu: khong bao gio tran khung
        a.text(0.04, 0.94, "median %s" % vn(med, 1 if med > 20 else 2),
               transform=a.transAxes, fontsize=7.5, va="top", ha="left")
        M(mac + "Med", vn(med, 1 if med > 20 else 2))
        M(mac + "Max", vn(float(v.max()), 1 if med > 20 else 2))
    save(fig, "fig2-orbital")

    # so dung trong van xuoi
    M("numDopS", vn(float(np.median(g("doppler_S_peak_khz"))), 1))
    M("numDopRate", "{:,.1f}".format(float(np.median(g("doppler_rate_Ka_hz_s"))) / 1e3))
    M("numDopRateMax", "{:,.1f}".format(float(np.max(g("doppler_rate_Ka_hz_s"))) / 1e3))
    M("numSlew", vn(float(np.median(g("abs_dfspl_dt_max_db_s"))), 3))
    M("numSlewTen", vn(float(np.median(g("abs_dfspl_dt_max_db_s"))) * 10, 2))
    M("numOwd", vn(float(np.median(g("owd_max_ms"))), 2))

    # bang 3: tom tat theo tram, chung minh so la tinh chat cua VO QUY DAO
    rows = []
    for sn, s in e1["stations"].items():
        Q = s["passes"]["25"]
        h = lambda k: np.median([p[k] for p in Q])                 # noqa: E731
        rows.append((sn, s["lat"], len(Q), h("dur_s"), h("fspl_swing_db"),
                     h("doppler_Ka_peak_khz")))
    with io.open(os.path.join(OUTD, "tab3-stations.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{lrrrrr}\n\\toprule\n")
        f.write("Ground station & Lat. ($^\\circ$) & Passes & Window (s) & "
                "Swing (dB) & Doppler (kHz) \\\\\n\\midrule\n")
        for r in rows:
            f.write("%s & %.1f & %s & %s & %s & %s \\\\\n"
                    % (r[0], r[1], "{:,}".format(r[2]), vn(r[3], 1), vn(r[4], 2), vn(r[5], 1)))
        f.write("\\bottomrule\n\\end{tabular}\n")
    print("     tab3-stations")
    sp = [r[5] for r in rows]
    M("numDopSpread", vn(max(sp) - min(sp), 1))


# =====================================================================
def fig_census(e2b, e2a):
    """Hinh 3: bang chung o PHAN DAU so voi PHAN DANH GIA."""
    its = [r for r in e2b["items"] if r.get("fulltext") and r.get("eval_section_found")]
    N = len(its)
    M("numPop", str(e2a["n_population"]))
    M("numFull", str(e2a["n_fulltext"]))
    M("numFullPct", vn(e2a["pct_fulltext"], 1))
    M("numCoded", str(N))
    M("numNotFull", str(e2a["n_population"] - e2a["n_fulltext"]))

    lab = {"DOPPLER": "Doppler shift", "DOPPLER_RATE": "Time-varying Doppler",
           "DELAY": "Propagation delay", "PATHLOSS_ELEV": "Elevation-dependent loss",
           "VISIBILITY": "Finite visibility window", "ATMOS": "Atmospheric attenuation",
           "ONBOARD": "On-board compute limit", "CH_AWGN": "AWGN channel",
           "CH_FADING": "Statistical fading", "CH_3GPP": "Standardised NTN model",
           "CH_TRACE": "Real orbital trace", "SNR_SWEEP": "SNR sweep / mismatch"}
    codes = [c["code"] for c in e2b["checklist"]]
    ev = [sum(1 for r in its if r["evidence"][c]["n_eval"] > 0) for c in codes]
    it_ = [sum(1 for r in its if r["evidence"][c]["n_intro"] > 0) for c in codes]
    for c, e, i in zip(codes, ev, it_):
        M("numEv" + c.replace("_", ""), str(e))
        M("numIn" + c.replace("_", ""), str(i))

    order = np.argsort(ev)
    y = np.arange(len(codes))
    fig, ax = plt.subplots(figsize=(W_COL, 2.9))
    ax.barh(y - 0.19, [it_[i] for i in order], 0.36, color=C["gray"], alpha=0.55,
            label="mentioned in framing")
    ax.barh(y + 0.19, [ev[i] for i in order], 0.36, color=C["verm"],
            label="present in evaluation")
    ax.set_yticks(y)
    ax.set_yticklabels([lab[codes[i]] for i in order], fontsize=7.5)
    ax.set_xlabel("works out of %d" % N)
    ax.set_xlim(0, N)
    ax.axvline(N, color="k", lw=0.6, ls=":")
    # ⛔ Mot thanh dai 0 trong y het mot o THIEU DU LIEU. Hai hang duoi cung la so 0 DO DUOC,
    #    da qua doi chung duong va am o e2c, nen phai ghi ro chu khong de trong.
    for j, i in enumerate(order):
        if ev[i] == 0:
            ax.text(0.35, j + 0.19, "0", va="center", ha="left",
                    fontsize=7.5, color=C["verm"], fontweight="bold")
        if it_[i] == 0:
            ax.text(0.35, j - 0.19, "0", va="center", ha="left",
                    fontsize=7.5, color=C["gray"])
    ax.legend(loc="lower right", fontsize=7.5)
    save(fig, "fig3-census")

    with io.open(os.path.join(OUTD, "tab2-census.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{llrr}\n\\toprule\n")
        f.write("Code & NTN effect or channel model & Framing & Evaluation \\\\\n\\midrule\n")
        for i in reversed(order):
            f.write("\\texttt{%s} & %s & %d & %d \\\\\n"
                    % (codes[i].replace("_", "\\_"), lab[codes[i]], it_[i], ev[i]))
        f.write("\\bottomrule\n\\end{tabular}\n")
    print("     tab2-census")


# =====================================================================
def fig_e3(e3):
    """Hinh 4: mo hinh huan luyen o mot SNR, danh gia tren dai SNR va duoi lech tan du."""
    if not e3:
        print("     (chua co e3, bo qua hinh 4)")
        return
    fig, ax = plt.subplots(1, 2, figsize=(W_TEXT, 2.35))
    styles = {"fixed": (C["verm"], "o", "-", "trained at a single SNR"),
              "aug": (C["blue"], "s", "--", "trained with randomised SNR and CFO")}
    for mode, runs in e3["runs"].items():
        col, mk, ls, lb = styles[mode]
        xs = np.array([float(k) for k in e3["snr_eval_db"]])
        Y = np.array([[r["snr_curve"]["%.1f" % s] for s in xs] for r in runs])
        ax[0].plot(xs, np.median(Y, 0), color=col, marker=mk, ls=ls, label=lb)
        ax[0].fill_between(xs, Y.min(0), Y.max(0), color=col, alpha=0.16, lw=0)
        ex = np.array([float(k) for k in e3["eps_eval"]])
        Z = np.array([[r["cfo_curve"]["%.0e" % e] for e in ex] for r in runs])
        xp = np.where(ex == 0, 1e-6, ex)
        ax[1].plot(xp, np.median(Z, 0), color=col, marker=mk, ls=ls)
        ax[1].fill_between(xp, Z.min(0), Z.max(0), color=col, alpha=0.16, lw=0)
    ax[0].axvline(e3["snr_train_db"], color="k", lw=0.8, ls=":")
    ax[0].annotate("training SNR", xy=(e3["snr_train_db"], ax[0].get_ylim()[0]),
                   xytext=(3, 3), textcoords="offset points", fontsize=7.5)
    ax[0].set_xlabel("test SNR (dB)")
    ax[0].set_ylabel("PSNR (dB)")
    ax[0].legend(loc="lower right", fontsize=7.5)
    ax[1].set_xscale("log")
    ax[1].set_xlabel(r"residual normalised CFO $\varepsilon = f_{\rm res}/R_s$")
    ax[1].set_ylabel("PSNR (dB)")
    save(fig, "fig4-mismatch")

    fx = e3["runs"]["fixed"]
    lo, hi = e3["snr_eval_db"][0], e3["snr_eval_db"][-1]
    at = lambda runs, s: float(np.median([r["snr_curve"]["%.1f" % s] for r in runs]))  # noqa: E731
    M("numPsnrTrain", vn(at(fx, e3["snr_train_db"]), 2))
    M("numPsnrLo", vn(at(fx, lo), 2))
    M("numPsnrDrop", vn(at(fx, e3["snr_train_db"]) - at(fx, lo), 2))
    M("numSnrLo", vn(lo, 1))
    M("numSnrHi", vn(hi, 1))
    ce = lambda runs, e: float(np.median([r["cfo_curve"]["%.0e" % e] for r in runs]))  # noqa: E731
    M("numPsnrCfoClean", vn(ce(fx, 0.0), 2))
    for e, tag in ((1e-4, "Ea"), (1e-3, "Eb"), (1e-2, "Ec")):
        M("numPsnrCfo" + tag, vn(ce(fx, e), 2))
        M("numDropCfo" + tag, vn(ce(fx, 0.0) - ce(fx, e), 2))
    M("numPsnrAugLo", vn(at(e3["runs"]["aug"], lo), 2))
    M("numAugGain", vn(at(e3["runs"]["aug"], lo) - at(fx, lo), 2))
    M("numEpochs", str(e3["epochs"]))
    M("numSeeds", str(len(e3["seeds"])))
    M("numBwRatio", vn(e3["bandwidth_ratio"], 3))


# =====================================================================
def main():
    e1, e2a = load("e1_orbital_reality.json"), load("e2_fetch_population.json")
    e2b, e3 = load("e2b_evidence.json"), load("e3_train_eval.json")
    print("  sinh hien vat:")
    if e1:
        fig_orbital(e1)
    if e2b and e2a:
        fig_census(e2b, e2a)
    fig_e3(e3)

    with io.open(os.path.join(OUTD, "numbers.tex"), "w", encoding="utf-8") as f:
        f.write("%% SINH TU DONG boi figures/make_figures.py. KHONG SUA TAY.\n"
                "%% Chi ASCII: tep nay duoc nap boi ca main.tex lan cac tep hinh\n"
                "%% standalone, va mot so tep hinh khong nap inputenc.\n")
        for k in sorted(NUM):
            f.write("\\newcommand{\\%s}{%s}\n" % (k, NUM[k]))
    print("     numbers.tex (%d macro)" % len(NUM))
    return 0


if __name__ == "__main__":
    sys.exit(main())
