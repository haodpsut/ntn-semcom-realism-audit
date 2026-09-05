"""E1 — DO VAT LY QUY DAO THAT, tu TLE Starlink cong khai.

⛔ VI SAO TEP NAY DOC LAP VOI PHAN CON LAI CUA BAI. Day la dong gop [independent] so 2 trong
`claim-structure.md`: no do VAT LY, khong do VAN LIEU. Du phan kiem ke van lieu ra ket qua nao,
cac con so o day van dung va van co gia tri rieng cho nguoi thiet ke he thong.

⚠ KHONG DUNG LINK BUDGET TU NGHI RA. Bai nay chi tinh **suy hao khong gian tu do (FSPL)**, la
ham thuan hinh hoc cua cu ly nghieng:

    FSPL(dB) = 20 log10(d) + 20 log10(f) + 92.45      (d: km, f: GHz)

Moi thu khac anh huong SNR (gian do bup song, suy hao khi quyen, mua, nhiet tap am may thu) deu
CONG THEM bien thien chu khong tru bot trong mot luot bay dien hinh: bup song quet qua bien lam
do loi thay doi, va suy hao khi quyen tang khi goc ngang thap. Vi vay bien thien FSPL la mot
**CAN DUOI** cua bien thien SNR. Bao can duoi thi khong ai cai duoc ve mo hinh, va lap luan cua
bai chi can can duoi: "ngay ca khi BO QUA moi thu khac, hinh hoc mot minh da lam ngan sach duong
truyen dich X dB trong T giay".

Tham chieu chuan: 3GPP TR 38.821 dung S-band 2 GHz va Ka-band 20 GHz (xuong), goc ngang toi
thieu 10 do (mot so ca 30 do). Ta bao ca ba nguong.

Chay:  python3 code/e1_orbital_reality.py
"""

import io
import json
import os
import sys

import numpy as np
from sgp4.api import SatrecArray, Satrec, jday

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TLE = os.path.join(ROOT, "data", "starlink.tle")
OUT = os.path.join(ROOT, "results", "e1_orbital_reality.json")

C = 299792.458                      # km/s
RE = 6378.137                       # km, WGS-84 ban kinh xich dao
BANDS = {"S": 2.0, "Ka": 20.0}      # GHz, theo TR 38.821
ELEV_MIN = [10.0, 25.0, 30.0]       # do
# ⚠ MAU: lay bao nhieu ve tinh. Khai ra chu khong giau, va co seed co dinh.
N_SAT = int(os.environ.get("NTN_NSAT", "1200"))
SEED = 20260905
HOURS = 24
DT_COARSE = 10.0                    # s, quet tho de tim luot bay
DT_FINE = 0.5                       # s, do lai trong luot bay

# Tram mat dat: bon vi do khac nhau de thay phu thuoc vi do.
# Da Nang la noi cua nhom tac gia; ba diem con lai de trai vi do.
STATIONS = [("Da Nang", 16.047, 108.206), ("Equator", 0.0, 0.0),
            ("Mid-lat", 45.0, 10.0), ("High-lat", 65.0, 20.0)]


def load_tles(path, n, rng):
    lines = [l.rstrip("\n") for l in io.open(path, encoding="utf-8", errors="replace")]
    recs, names = [], []
    for i in range(0, len(lines) - 2, 3):
        l1, l2 = lines[i + 1], lines[i + 2]
        if not (l1.startswith("1 ") and l2.startswith("2 ")):
            continue
        try:
            recs.append(Satrec.twoline2rv(l1, l2))
            names.append(lines[i].strip())
        except Exception:
            continue
    idx = rng.choice(len(recs), size=min(n, len(recs)), replace=False)
    return [recs[i] for i in idx], [names[i] for i in idx]


def gmst(jd, fr):
    """Goc sao Greenwich, cong thuc IAU 1982, du chinh xac cho muc dich nay."""
    t = (jd - 2451545.0 + fr) / 36525.0
    g = 67310.54841 + (876600.0 * 3600 + 8640184.812866) * t + 0.093104 * t * t - 6.2e-6 * t ** 3
    return np.radians((g % 86400.0) / 240.0)


def station_eci(lat_deg, lon_deg, theta):
    """Vi tri tram trong ECI (Trai Dat cau, du cho bai toan hinh hoc muc nay)."""
    lat = np.radians(lat_deg)
    lon_side = theta + np.radians(lon_deg)
    return np.stack([RE * np.cos(lat) * np.cos(lon_side),
                     RE * np.cos(lat) * np.sin(lon_side),
                     np.full_like(lon_side, RE * np.sin(lat))], axis=-1)


def geometry(sat_r, st_r, lat_deg, lon_deg, theta):
    """Tra ve (cu ly nghieng km, goc ngang do) cho mang thoi gian."""
    d = sat_r - st_r
    rng_km = np.linalg.norm(d, axis=-1)
    up = st_r / np.linalg.norm(st_r, axis=-1, keepdims=True)
    sin_el = np.sum(d * up, axis=-1) / np.maximum(rng_km, 1e-9)
    return rng_km, np.degrees(np.arcsin(np.clip(sin_el, -1, 1)))


def propagate(recs, jd, fr):
    arr = SatrecArray(recs)
    e, r, _ = arr.sgp4(jd, fr)
    r = np.asarray(r)
    r[np.asarray(e) != 0] = np.nan
    return r                                    # (n_sat, n_t, 3) km, TEME


def main():
    rng = np.random.default_rng(SEED)
    recs, names = load_tles(TLE, N_SAT, rng)
    print("  E1 — %d ve tinh Starlink, %d gio, quet %.0fs / tinh lai %.1fs"
          % (len(recs), HOURS, DT_COARSE, DT_FINE))

    jd0, fr0 = jday(2026, 9, 5, 0, 0, 0.0)
    n_c = int(HOURS * 3600 / DT_COARSE)
    fr_c = fr0 + np.arange(n_c) * DT_COARSE / 86400.0
    jd_c = np.full(n_c, jd0)
    r_c = propagate(recs, jd_c, fr_c)
    th_c = gmst(jd_c, fr_c)
    print("     quet tho xong: %d mau x %d ve tinh" % (n_c, len(recs)))

    doc = {"n_sat": len(recs), "hours": HOURS, "dt_coarse_s": DT_COARSE,
           "dt_fine_s": DT_FINE, "seed": SEED, "tle_file": os.path.basename(TLE),
           "bands_ghz": BANDS, "elev_min_deg": ELEV_MIN,
           "note": "chi tinh FSPL thuan hinh hoc; day la CAN DUOI cua bien thien SNR",
           "stations": {}}

    for sname, lat, lon in STATIONS:
        st_c = station_eci(lat, lon, th_c)
        _, el_c = geometry(r_c, st_c[None, :, :], lat, lon, th_c)

        per_thresh = {}
        for emin in ELEV_MIN:
            vis = el_c >= emin
            passes = []
            for si in range(vis.shape[0]):
                v = vis[si]
                if not v.any():
                    continue
                edges = np.diff(v.astype(np.int8))
                starts = list(np.where(edges == 1)[0] + 1)
                ends = list(np.where(edges == -1)[0] + 1)
                if v[0]:
                    starts = [0] + starts
                if v[-1]:
                    ends = ends + [len(v)]
                for a, b in zip(starts, ends):
                    if b - a < 2:
                        continue
                    # ---- do lai trong luot bay o buoc min ----
                    t0 = (a - 1) * DT_COARSE
                    t1 = min((b + 1) * DT_COARSE, HOURS * 3600)
                    n_f = max(int((t1 - t0) / DT_FINE), 3)
                    fr_f = fr0 + (t0 + np.arange(n_f) * DT_FINE) / 86400.0
                    jd_f = np.full(n_f, jd0)
                    r_f = propagate([recs[si]], jd_f, fr_f)[0]
                    th_f = gmst(jd_f, fr_f)
                    st_f = station_eci(lat, lon, th_f)
                    rk, el = geometry(r_f[None, :, :], st_f[None, :, :], lat, lon, th_f)
                    rk, el = rk[0], el[0]
                    m = el >= emin
                    if m.sum() < 3 or not np.isfinite(rk[m]).all():
                        continue
                    rk_v, el_v = rk[m], el[m]
                    dur = (m.sum() - 1) * DT_FINE

                    # toc do bien thien cu ly -> Doppler
                    rdot = np.gradient(rk_v, DT_FINE)                  # km/s
                    # FSPL: chi phan phu thuoc cu ly, phan phu thuoc tan so trieu tieu khi lay hieu
                    fspl = 20.0 * np.log10(np.maximum(rk_v, 1e-9))
                    dfspl_dt = np.gradient(fspl, DT_FINE)              # dB/s

                    p = {"sat": names[si], "dur_s": float(dur),
                         "el_max_deg": float(el_v.max()),
                         "range_min_km": float(rk_v.min()),
                         "range_max_km": float(rk_v.max()),
                         "owd_min_ms": float(rk_v.min() / C * 1e3),
                         "owd_max_ms": float(rk_v.max() / C * 1e3),
                         "fspl_swing_db": float(fspl.max() - fspl.min()),
                         "abs_dfspl_dt_max_db_s": float(np.abs(dfspl_dt).max()),
                         "abs_rdot_max_km_s": float(np.abs(rdot).max())}
                    for bn, fghz in BANDS.items():
                        # f_d = -(rdot/c) * f0 ; lay bien do lon nhat va toc do bien thien
                        fd = -(rdot / C) * (fghz * 1e9)                 # Hz
                        p["doppler_%s_peak_khz" % bn] = float(np.abs(fd).max() / 1e3)
                        p["doppler_rate_%s_hz_s" % bn] = float(
                            np.abs(np.gradient(fd, DT_FINE)).max())
                    passes.append(p)
            per_thresh["%.0f" % emin] = passes
            print("     %-9s el>=%2.0f do: %5d luot bay" % (sname, emin, len(passes)),
                  flush=True)
        doc["stations"][sname] = {"lat": lat, "lon": lon, "passes": per_thresh}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False))
    print("  da ghi %s (%.1f MB)" % (OUT, os.path.getsize(OUT) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
