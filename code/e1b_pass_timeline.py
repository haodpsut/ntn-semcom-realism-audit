"""E1b — chuoi thoi gian cua MOT luot bay that, de ve hinh giai thich co che.

⛔ VI SAO CAN RIENG. E1 chi luu TOM TAT moi luot bay (trung vi, cuc dai, do dai). Bai can mot
hinh cho thay dien bien TRONG mot luot bay, vi do la cho lap luan cua bai nam: SNR gan nhu tinh
trong mot KHOI TRUYEN nhung quet manh trong ca LUOT BAY, va Doppler thi doi dau giua len va
xuong. Khong the ve dieu do tu so tom tat.

⚠ CHON LUOT BAY NAO. Khong chon luot dep nhat. Chon luot co goc ngang cuc dai GAN TRUNG VI cua
phan bo, va khai ro tieu chi do trong tep ket qua, de khong ai phai tin rang hinh la dai dien.

Chay:  python3 code/e1b_pass_timeline.py
"""

import io
import json
import os
import sys

import numpy as np
from sgp4.api import Satrec, SatrecArray, jday

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e1_orbital_reality as E1                                        # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "e1b_pass_timeline.json")
SUMM = os.path.join(ROOT, "results", "e1_orbital_reality.json")
STATION = ("Da Nang", 16.047, 108.206)
ELEV_MIN = 25.0
DT = 0.25                                    # s


def main():
    rng = np.random.default_rng(E1.SEED)
    recs, names = E1.load_tles(E1.TLE, E1.N_SAT, rng)

    # tieu chi chon: goc ngang cuc dai gan TRUNG VI cua phan bo do o E1
    summ = json.load(io.open(SUMM, encoding="utf-8"))
    P = summ["stations"][STATION[0]]["passes"]["%.0f" % ELEV_MIN]
    target = float(np.median([p["el_max_deg"] for p in P]))
    pick = min(P, key=lambda p: abs(p["el_max_deg"] - target))
    print("  tieu chi chon: goc ngang cuc dai gan trung vi (%.2f do)" % target)
    print("  luot duoc chon: %s · el_max %.2f do · dai %.1f s"
          % (pick["sat"], pick["el_max_deg"], pick["dur_s"]))

    si = names.index(pick["sat"])
    jd0, fr0 = jday(2026, 9, 5, 0, 0, 0.0)
    # quet tho tim lai dung luot bay do
    n_c = int(E1.HOURS * 3600 / E1.DT_COARSE)
    fr_c = fr0 + np.arange(n_c) * E1.DT_COARSE / 86400.0
    jd_c = np.full(n_c, jd0)
    r_c = E1.propagate([recs[si]], jd_c, fr_c)
    th_c = E1.gmst(jd_c, fr_c)
    st_c = E1.station_eci(STATION[1], STATION[2], th_c)
    _, el_c = E1.geometry(r_c, st_c[None, :, :], STATION[1], STATION[2], th_c)
    el_c = el_c[0]
    vis = el_c >= ELEV_MIN
    edges = np.diff(vis.astype(np.int8))
    starts = list(np.where(edges == 1)[0] + 1)
    ends = list(np.where(edges == -1)[0] + 1)
    if vis[0]:
        starts = [0] + starts
    if vis[-1]:
        ends = ends + [len(vis)]
    best = max(zip(starts, ends), key=lambda ab: el_c[ab[0]:ab[1]].max())

    t0 = (best[0] - 1) * E1.DT_COARSE
    t1 = (best[1] + 1) * E1.DT_COARSE
    n = int((t1 - t0) / DT)
    fr = fr0 + (t0 + np.arange(n) * DT) / 86400.0
    jd = np.full(n, jd0)
    r = E1.propagate([recs[si]], jd, fr)[0]
    th = E1.gmst(jd, fr)
    st = E1.station_eci(STATION[1], STATION[2], th)
    rk, el = E1.geometry(r[None, :, :], st[None, :, :], STATION[1], STATION[2], th)
    rk, el = rk[0], el[0]
    m = el >= ELEV_MIN
    t = (np.arange(n) * DT)[m] - (np.arange(n) * DT)[m][0]
    rk, el = rk[m], el[m]
    rdot = np.gradient(rk, DT)
    fspl = 20.0 * np.log10(rk)

    doc = {"station": STATION[0], "elev_min_deg": ELEV_MIN, "dt_s": DT,
           "selection_rule": "goc ngang cuc dai gan TRUNG VI cua phan bo o E1, "
                             "khong chon luot dep nhat",
           "median_el_max_deg": target, "sat": pick["sat"],
           "el_max_deg": float(el.max()), "dur_s": float(t[-1]),
           "t_s": t.tolist(), "elev_deg": el.tolist(), "range_km": rk.tolist(),
           "owd_ms": (rk / E1.C * 1e3).tolist(),
           "fspl_rel_db": (fspl - fspl.min()).tolist()}
    for bn, f in E1.BANDS.items():
        doc["doppler_%s_khz" % bn] = (-(rdot / E1.C) * (f * 1e9) / 1e3).tolist()
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False))
    print("  %d mau · Doppler Ka tu %.1f den %.1f kHz · FSPL quet %.2f dB"
          % (len(t), min(doc["doppler_Ka_khz"]), max(doc["doppler_Ka_khz"]),
             max(doc["fspl_rel_db"])))
    print("  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
