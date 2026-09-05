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

# ⛔ elsarticle o che do `preprint` la MOT COT rong 4.60 in, khong phai 7.0 in nhu ban hai cot.
#    Ve theo 7.0 roi nhet vao 4.60 lam hinh bi thu con he so 0.66 va CHU TUT XUONG 6.0pt.
#    Ve dung be rong SE DUOC DUNG thi he so bang 1.0 va co chu giu nguyen 9pt.
W_TEXT = 4.60                      # \textwidth
W_WIDE = 4.60                      # hinh trai het khung
W_HALF = 2.99                      # hinh dat o 0.65\textwidth
W_COL = 2.85                       # hinh dat o 0.62\textwidth
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


def save(fig, name, target_w=None):
    """Ghi hinh sao cho be rong THAT cua tep PDF dung bang be rong se dung trong bai.

    ⛔ VI SAO PHAI LAP. `bbox_inches="tight"` cat khung theo NOI DUNG, nen be rong tep ra khac
    be rong `figsize` da yeu cau, va khac nhau tung hinh tuy nhan truc dai ngan. Dua tat ca vao
    bai o `\textwidth` thi moi hinh bi co gian MOT HE SO KHAC NHAU, va co chu hieu dung chay tu
    6,8pt den 10,0pt. Do la ly do mot so hinh trong nho han han cac hinh khac.

    ⚠ Cong `check_figure_scale` bao PASS suot, vi no kiem TUNG hinh co nam trong nguong khong,
    khong kiem cac hinh co NHAT QUAN voi nhau khong. Lop loi "cong dung nhung hoi thieu".

    Cach chua: le phai (nhan truc, chu thich) gan nhu co dinh theo inch, nen
    `figw_moi = figw + (dich - do_duoc)` hoi tu sau vai vong.
    """
    target_w = target_w or W_WIDE
    path_pdf = os.path.join(OUTD, "%s.pdf" % name)
    for _ in range(6):
        fig.savefig(path_pdf, bbox_inches="tight")
        with open(path_pdf, "rb") as fh:
            blob = fh.read()
        mm = re.findall(rb"/MediaBox\s*\[([^\]]*)\]", blob)
        if not mm:
            break
        x0, y0, x1, y1 = [float(v) for v in mm[0].split()]
        got = (x1 - x0) / 72.0
        if abs(got - target_w) < 0.005:
            break
        w, h = fig.get_size_inches()
        fig.set_size_inches(w + (target_w - got), h)
    fig.savefig(os.path.join(OUTD, "%s.png" % name), bbox_inches="tight", dpi=200)
    plt.close(fig)
    print("     %-16s %.2f in" % (name, got))


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
    fig, ax = plt.subplots(1, 3, figsize=(W_WIDE, 1.85))
    fig.subplots_adjust(wspace=0.46)
    # ⛔ Nhan phai NGAN: o khung 4,60 in moi bang chi rong ~1,2 in, nhan dai se chong len
    #    bang ben canh va bi cat o bang cuoi. Ten day du chuyen sang chu thich hinh.
    specs = [("doppler_Ka_peak_khz", "Doppler (kHz)", C["verm"], "numDopKa"),
             ("fspl_swing_db", "swing (dB)", C["blue"], "numFspl"),
             ("dur_s", "window (s)", C["green"], "numDur")]
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
def tab_controls(e2b):
    """So cau bo do bat duoc tren toan van THAT: dung cho cau ve doi chung o muc giao thuc."""
    its = [r for r in e2b["items"] if r.get("fulltext")]
    tot = sum(v["n_intro"] + v["n_eval"] for r in its for v in r["evidence"].values())
    M("numCtrlHits", "{:,}".format(tot))
    M("numCtrlDocs", str(len(its)))


def fig_census(e2b, e2a):
    """Hinh 3: bang chung o PHAN DAU so voi PHAN DANH GIA."""
    its = [r for r in e2b["items"] if r.get("fulltext") and r.get("eval_section_found")]
    N = len(its)
    M("numPop", str(e2a["n_population"]))
    M("numFull", str(e2a["n_fulltext"]))
    M("numFullPct", vn(e2a["pct_fulltext"], 1))
    M("numCoded", str(N))
    M("numNotFull", str(e2a["n_population"] - e2a["n_fulltext"]))

    lab = LABEL
    codes = [c["code"] for c in e2b["checklist"]]
    ev = [sum(1 for r in its if r["evidence"][c]["n_eval"] > 0) for c in codes]
    it_ = [sum(1 for r in its if r["evidence"][c]["n_intro"] > 0) for c in codes]
    for c, e, i in zip(codes, ev, it_):
        M("numEv" + c.replace("_", ""), str(e))
        M("numIn" + c.replace("_", ""), str(i))

    order = np.argsort(ev)
    y = np.arange(len(codes))
    fig, ax = plt.subplots(figsize=(W_WIDE, 2.45))
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
    save(fig, "fig5-census")

    with io.open(os.path.join(OUTD, "tab2-census.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{llrr}\n\\toprule\n")
        f.write("Code & NTN effect or channel model & Framing & Evaluation \\\\\n\\midrule\n")
        for i in reversed(order):
            f.write("\\texttt{%s} & %s & %d & %d \\\\\n"
                    % (codes[i].replace("_", "\\_"), lab[codes[i]], it_[i], ev[i]))
        f.write("\\bottomrule\n\\end{tabular}\n")
    print("     tab2-census")



# =====================================================================
#  NGUON NEO cua tung hang muc: bai KHONG duoc tu nghi ra tieu chi.
#  "survey" = rang buoc cau truc do chinh khao sat cua linh vuc neu ra.
#  "3GPP"   = nghien cuu kenh phi mat dat cua 3GPP.
#  "orbit"  = suy truc tiep tu co hoc quy dao.
#  "proto"  = quy uoc danh gia, khong phai hieu ung vat ly.
ANCHOR = {
 "DOPPLER": ("survey", "Large and time-varying Doppler shift"),
 "DOPPLER_RATE": ("survey", "the time-varying component of the same constraint"),
 "DELAY": ("survey", "Long propagation delay"),
 "PATHLOSS_ELEV": ("survey", "Severe and time-varying path loss"),
 "VISIBILITY": ("survey", "Intermittent connectivity, short visibility windows"),
 "ATMOS": ("survey", "Atmospheric and weather attenuation"),
 "ONBOARD": ("survey", "On-board size, weight and power limits"),
 "CH_AWGN": ("proto", "conventional terrestrial reference channel"),
 "CH_FADING": ("proto", "conventional statistical fading channel"),
 "CH_3GPP": ("3GPP", "TR 38.811 / TR 38.821 non-terrestrial channel"),
 "CH_TRACE": ("orbit", "channel driven by propagated orbital elements"),
 "SNR_SWEEP": ("proto", "operating range rather than operating point"),
}
LABEL = {"DOPPLER": "Doppler shift", "DOPPLER_RATE": "Time-varying Doppler",
         "DELAY": "Propagation delay", "PATHLOSS_ELEV": "Elevation-dependent loss",
         "VISIBILITY": "Finite visibility window", "ATMOS": "Atmospheric attenuation",
         "ONBOARD": "On-board compute limit", "CH_AWGN": "AWGN channel",
         "CH_FADING": "Statistical fading", "CH_3GPP": "Standardised NTN model",
         "CH_TRACE": "Real orbital trace", "SNR_SWEEP": "SNR sweep / mismatch"}


def fig_pass(tl):
    """Hinh 3: dien bien TRONG mot luot bay that. Day la hinh giai thich co che cua bai."""
    if not tl:
        return
    t = np.array(tl["t_s"])
    fig, ax = plt.subplots(3, 1, figsize=(W_WIDE, 3.20), sharex=True)
    ax[0].plot(t, tl["elev_deg"], color=C["green"])
    ax[0].set_ylabel("elevation ($^\\circ$)")
    ax[1].plot(t, tl["doppler_Ka_khz"], color=C["verm"], label="Ka, 20 GHz")
    ax[1].plot(t, tl["doppler_S_khz"], color=C["blue"], ls="--", label="S, 2 GHz")
    ax[1].axhline(0, color="k", lw=0.5)
    ax[1].set_ylabel("Doppler (kHz)")
    ax[1].legend(fontsize=7, loc="upper right")
    ax[2].plot(t, tl["fspl_rel_db"], color=C["gray"])
    ax[2].set_ylabel("path loss (dB)")
    ax[2].set_xlabel("time within pass (s)")
    # khoi truyen 1 s: chieu rong that cua no tren truc nay la co y, no gan nhu mot duong ke
    for a in ax:
        a.axvspan(t[len(t) // 2], t[len(t) // 2] + 1.0, color=C["orange"], alpha=0.85, lw=0)
    # ⛔ Dat chu thich theo toa do DU LIEU thi no dinh vao truc y. Toa do TRUC thi khong.
    ax[2].text(0.03, 0.88, "vertical band: a 1 s transmission block",
               transform=ax[2].transAxes, fontsize=7, va="top")
    save(fig, "fig3-pass")
    M("numPassSat", tl["sat"].replace("STARLINK-", "Starlink "))
    M("numPassElMax", vn(tl["el_max_deg"], 1))
    M("numPassDur", vn(tl["dur_s"], 1))
    M("numPassDopLo", vn(min(tl["doppler_Ka_khz"]), 1))
    M("numPassDopHi", vn(max(tl["doppler_Ka_khz"]), 1))
    M("numPassDopSpan", vn(max(tl["doppler_Ka_khz"]) - min(tl["doppler_Ka_khz"]), 1))


def fig_elevation(e1):
    """Hinh 4: cac dai luong thay doi the nao theo NGUONG GOC NGANG toi thieu."""
    th = e1["elev_min_deg"]
    keys = [("dur_s", "window (s)", C["green"]),
            ("doppler_Ka_peak_khz", "Doppler (kHz)", C["verm"]),
            ("fspl_swing_db", "swing (dB)", C["blue"])]
    fig, ax = plt.subplots(1, 3, figsize=(W_WIDE, 1.85))
    fig.subplots_adjust(wspace=0.46)
    for a, (k, lab, col) in zip(ax, keys):
        for sn, mk, ls in zip(e1["stations"], ("o", "s", "^", "D"), ("-", "--", "-.", ":")):
            v = [np.median([p[k] for p in e1["stations"][sn]["passes"]["%.0f" % e]])
                 for e in th]
            a.plot(th, v, color=C["gray"] if sn != "Da Nang" else col,
                   marker=mk, ls=ls, label=sn, markersize=3.4,
                   alpha=1.0 if sn == "Da Nang" else 0.55)
        a.set_xlabel("min.\ elevation ($^\\circ$)")
        a.set_ylabel(lab)
        a.set_xticks(th)
    ax[0].legend(fontsize=6.5, loc="upper right")
    save(fig, "fig4-elevation")
    # bang 4: thong ke day du o ba nguong
    with io.open(os.path.join(OUTD, "tab4-orbital.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{lrrrrrr}\n\\toprule\n")
        f.write("& \\multicolumn{2}{c}{$10^\\circ$} & \\multicolumn{2}{c}{$25^\\circ$}"
                " & \\multicolumn{2}{c}{$30^\\circ$} \\\\\n")
        f.write("\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\n")
        f.write("Quantity & median & max & median & max & median & max \\\\\n\\midrule\n")
        spec = [("dur_s", "Visibility window (s)", 1),
                ("owd_max_ms", "One-way delay (ms)", 2),
                ("doppler_S_peak_khz", "Peak Doppler, S-band (kHz)", 1),
                ("doppler_Ka_peak_khz", "Peak Doppler, Ka-band (kHz)", 1),
                ("doppler_rate_Ka_hz_s", "Doppler drift, Ka (kHz/s)", 2),
                ("fspl_swing_db", "Link-budget swing (dB)", 2),
                ("abs_dfspl_dt_max_db_s", "Link-budget slew (dB/s)", 3)]
        P = e1["stations"]["Da Nang"]["passes"]
        for k, lab, d in spec:
            cells = []
            for e in th:
                v = np.array([p[k] for p in P["%.0f" % e]])
                if k == "doppler_rate_Ka_hz_s":
                    v = v / 1e3
                cells += [vn(float(np.median(v)), d), vn(float(v.max()), d)]
            f.write("%s & %s \\\\\n" % (lab, " & ".join(cells)))
        f.write("\\bottomrule\n\\end{tabular}\n")
    print("     tab4-orbital")
    n10 = len(e1["stations"]["Da Nang"]["passes"]["10"])
    n30 = len(e1["stations"]["Da Nang"]["passes"]["30"])
    M("numPassTen", "{:,}".format(n10))
    M("numPassThirty", "{:,}".format(n30))


def fig_matrix(e2b):
    """Hinh 6: ma tran cong trinh x hang muc. Cho thay CAU TRUC, khong chi tong so."""
    its = [r for r in e2b["items"] if r.get("fulltext") and r.get("eval_section_found")]
    codes = [c["code"] for c in e2b["checklist"]]
    order = np.argsort([-sum(1 for r in its if r["evidence"][c]["n_eval"] > 0) for c in codes])
    codes = [codes[i] for i in order]
    # 0 = vang mat, 1 = chi o phan dat van de, 2 = co trong phan danh gia
    Mx = np.zeros((len(its), len(codes)))
    for i, r in enumerate(its):
        for j, c in enumerate(codes):
            e = r["evidence"][c]
            Mx[i, j] = 2 if e["n_eval"] > 0 else (1 if e["n_intro"] > 0 else 0)
    rowsum = Mx.sum(1)
    idx = np.argsort(-rowsum)
    Mx = Mx[idx]
    from matplotlib.colors import ListedColormap
    cm = ListedColormap(["#EEEEEE", C["gray"], C["verm"]])
    fig, ax = plt.subplots(figsize=(W_WIDE, 3.30))
    ax.imshow(Mx.T, cmap=cm, aspect="auto", vmin=0, vmax=2, interpolation="nearest")
    ax.set_yticks(range(len(codes)))
    ax.set_yticklabels([LABEL[c] for c in codes], fontsize=7)
    ax.set_xticks(range(len(its)))
    ax.set_xticklabels([str(its[i]["ref"]) for i in idx], fontsize=5.6, rotation=90)
    ax.set_xlabel("work, as numbered in the source survey, ordered by coverage")
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks(np.arange(-.5, len(its), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(codes), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.8)
    ax.tick_params(which="minor", length=0)
    import matplotlib.patches as mp
    ax.legend(handles=[mp.Patch(color="#EEEEEE", label="absent"),
                       mp.Patch(color=C["gray"], label="framing only"),
                       mp.Patch(color=C["verm"], label="in evaluation")],
              loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=3, fontsize=7.5)
    save(fig, "fig6-matrix")
    M("numMaxCover", str(int(rowsum.max() // 2)))
    M("numZeroCover", str(int(sum(1 for r in rowsum if r == 0))))


def tab_checklist(e2b):
    """Bang 1: danh muc kem NGUON NEO cua tung hang muc."""
    src = {"survey": "Survey", "3GPP": "3GPP", "orbit": "Orbit", "proto": "Protocol"}
    with io.open(os.path.join(OUTD, "tab1-checklist.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{llp{62mm}}\n\\toprule\n")
        f.write("Item & Anchor & What the item asks the evaluation to instantiate "
                "\\\\\n\\midrule\n")
        for c in e2b["checklist"]:
            a, d = ANCHOR[c["code"]]
            f.write("%s & %s & %s \\\\\n" % (LABEL[c["code"]], src[a], d))
        f.write("\\bottomrule\n\\end{tabular}\n")
    print("     tab1-checklist")
    M("numChecklist", str(len(e2b["checklist"])))
    M("numFromSurvey", str(sum(1 for c in e2b["checklist"]
                               if ANCHOR[c["code"]][0] == "survey")))


def tab_agreement(e2b, e2a):
    """Bang 5: cot cua KHAO SAT so voi noi dung PHAN DANH GIA cua bai goc.

    ⛔ Day la phep so HAI NGUON noi ve cung mot doi tuong, dung tinh than cong
    `check_source_agreement` cua pipeline nhung nang thanh noi dung nghien cuu.

    ⚠ Ban dau toi chi so rieng Doppler va bang ra DUNG MOT DONG, vi cot cua khao sat chi nhac
    Doppler o 2/23 o va chi 1 trong hai lay duoc toan van. Mot dong khong phai mot bang. Nen
    phep so duoc mo rong ra CA DANH MUC.

    ⚠ Va phai doc cho dung: o cot cua khao sat dai chua toi 30 ky tu, nen no KHONG THE liet ke
    het. Tap cua khao sat nam trong tap cua bai goc la binh thuong. Ca DANG CHU Y la chieu
    NGUOC: cot khao sat khang dinh mot hieu ung ma phan danh gia cua bai goc khong co.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "e2b", os.path.join(ROOT, "code", "e2b_extract_evidence.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    RX = {c: re.compile(pat, re.I) for c, _, pat in mod.CHECKLIST}

    ev = {r["ref"]: r for r in e2b["items"] if r.get("fulltext") and r.get("eval_section_found")}
    rows, n_sub, n_extra = [], 0, 0
    for it in e2a["items"]:
        col = (it.get("survey_channel_col") or "").strip()
        if not col or it["ref"] not in ev:
            continue
        r = ev[it["ref"]]
        A = {c for c in RX if RX[c].search(col)}                    # khao sat NOI gi
        B = {c for c in RX if r["evidence"][c]["n_eval"] > 0}       # bai goc CO gi
        extra = sorted(A - B)
        if extra:
            n_extra += 1
        else:
            n_sub += 1
        rows.append((it["ref"], col, sorted(A), sorted(B), extra))
    rows.sort(key=lambda x: (-len(x[4]), x[0]))
    with io.open(os.path.join(OUTD, "tab5-agreement.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{rlccl}\n\\toprule\n")
        f.write("Work & Survey's channel entry & Named & In eval. & Named but absent "
                "\\\\\n\\midrule\n")
        for ref, col, A, B, extra in rows:
            # ⛔ O dau dong KHONG duoc bat dau bang "[": TeX doc `\\` cua dong truoc cong
            #    `[95]` thanh `\\[95]`, tuc xuong dong kem 95 don vi doc, va "95]" khong phai
            #    don vi hop le. Boc trong ngoac nhon de chan.
            f.write("{[%d]} & %s & %d & %d & %s \\\\\n"
                    % (ref, col.replace("&", "\\&")[:34], len(A), len(B),
                       ", ".join(LABEL[c] for c in extra) if extra else "---"))
        f.write("\\bottomrule\n\\end{tabular}\n")
    print("     tab5-agreement")
    M("numAgrN", str(len(rows)))
    M("numAgrSub", str(n_sub))
    M("numAgrExtra", str(n_extra))
    M("numAgrNamedTot", str(sum(len(r[2]) for r in rows)))
    M("numAgrEvalTot", str(sum(len(r[3]) for r in rows)))


# =====================================================================
def fig_e3(e3):
    """Hinh 4: mo hinh huan luyen o mot SNR, danh gia tren dai SNR va duoi lech tan du."""
    if not e3:
        print("     (chua co e3, bo qua hinh 4)")
        return
    fig, ax = plt.subplots(1, 2, figsize=(W_WIDE, 2.05))
    fig.subplots_adjust(wspace=0.34)
    # ⛔ Nhan chu giai DAI thi hop chu giai tran sang ca bang ben canh. Rut ngan, giai thich
    #    day du chuyen sang chu thich hinh.
    styles = {"fixed": (C["verm"], "o", "-", "single SNR"),
              "aug": (C["blue"], "s", "--", "randomised")}
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
    ax[0].text(0.52, 0.04, "training SNR", transform=ax[0].transAxes, fontsize=7)
    ax[0].set_xlabel("test SNR (dB)")
    ax[0].set_ylabel("PSNR (dB)")
    ax[0].legend(loc="upper left", fontsize=7, handlelength=1.6, borderpad=0.2)
    ax[1].set_xscale("log")
    ax[1].set_xlabel(r"residual CFO $\varepsilon$")
    ax[1].set_ylabel("PSNR (dB)")
    save(fig, "fig7-mismatch")

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
    ag = e3["runs"]["aug"]
    M("numPsnrAugLo", vn(at(ag, lo), 2))
    # ⚠ Ten cu la numAugGain, nhung gia tri AM: ngau nhien hoa KHONG giup o truc SNR.
    #    Doi ten cho khoi doc nham thanh mot loi ich.
    M("numAugSnrDelta", vn(at(ag, lo) - at(fx, lo), 2))
    M("numPsnrAugTrain", vn(at(ag, e3["snr_train_db"]), 2))
    M("numAugCost", vn(at(fx, e3["snr_train_db"]) - at(ag, e3["snr_train_db"]), 2))
    M("numAugGainCfo", vn(ce(ag, 1e-3) - ce(fx, 1e-3), 2))
    M("numPsnrAugCfoEb", vn(ce(ag, 1e-3), 2))
    M("numPsnrAugCfoEc", vn(ce(ag, 1e-2), 2))
    # ⭐ Vi tri vach da du doan tu (13): dat 2*pi*eps*(k-1) = pi
    k = int(e3["c_channels"] * 8 * 8 / 2)
    M("numK", "{:,}".format(k))
    M("numCliffPred", "%.1f" % (1.0 / (2 * (k - 1)) * 1e4))     # don vi 1e-4
    # ---- bang 6: so doc duoc, kem do trai giua cac seed ----
    with io.open(os.path.join(OUTD, "tab6-mismatch.tex"), "w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{lrrrr}\n\\toprule\n")
        f.write("& \\multicolumn{2}{c}{trained at one SNR} & "
                "\\multicolumn{2}{c}{randomised training} \\\\\n")
        f.write("\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\n")
        f.write("Evaluation condition & median & range & median & range "
                "\\\\\n\\midrule\n")

        def cell(runs, kind, key):
            v = [r[kind][key] for r in runs]
            return vn(float(np.median(v)), 2), "%s--%s" % (vn(min(v), 2), vn(max(v), 2))

        fx, ag = e3["runs"]["fixed"], e3["runs"]["aug"]
        rows = [("SNR $=$ %s dB (training point)" % vn(e3["snr_train_db"], 0),
                 "snr_curve", "%.1f" % e3["snr_train_db"]),
                ("SNR $=$ %s dB (low end of pass)" % vn(lo, 0), "snr_curve", "%.1f" % lo),
                ("SNR $=$ %s dB (high end of pass)" % vn(hi, 0), "snr_curve", "%.1f" % hi)]
        for e in (1e-4, 1e-3, 1e-2):
            rows.append(("residual CFO $\\varepsilon = %s$" % ("10^{-%d}" % int(round(-np.log10(e)))),
                         "cfo_curve", "%.0e" % e))
        for lab, kind, key in rows:
            a1, a2 = cell(fx, kind, key)
            b1, b2 = cell(ag, kind, key)
            f.write("%s & %s & %s & %s & %s \\\\\n" % (lab, a1, a2, b1, b2))
        f.write("\\bottomrule\n\\end{tabular}\n")
    print("     tab6-mismatch")
    M("numEpochs", str(e3["epochs"]))
    M("numSeeds", str(len(e3["seeds"])))
    M("numBwRatio", vn(e3["bandwidth_ratio"], 3))


# =====================================================================
def main():
    e1, e2a = load("e1_orbital_reality.json"), load("e2_fetch_population.json")
    e2b, e3 = load("e2b_evidence.json"), load("e3_train_eval.json")
    tl = load("e1b_pass_timeline.json")
    print("  sinh hien vat:")
    if e1:
        fig_orbital(e1)
        fig_elevation(e1)
    if tl:
        fig_pass(tl)
    if e2b and e2a:
        tab_controls(e2b)
        fig_census(e2b, e2a)
        fig_matrix(e2b)
        tab_checklist(e2b)
        tab_agreement(e2b, e2a)
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
