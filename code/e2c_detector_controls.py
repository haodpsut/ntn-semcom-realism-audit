"""E2c — DOI CHUNG cho bo do bang chung cua E2b. ⛔ PHAI CHAY TRUOC KHI TIN BAT KY SO 0 NAO.

⛔ VI SAO. E2b tra ve HAI so 0: khong bai nao trong quan the nhac toi vet quy dao that (TLE /
SGP4 / ephemeris / STK) va khong bai nao nhac toi Doppler bien thien theo thoi gian. Mot so 0 co
the la PHAT HIEN, ma cung co the la BO DO HONG bi doc thanh ket qua am. Trong so da ghi lop loi
nay xay ra bon lan trong mot dot.

⇒ Ba phep thu, va chi khi ca ba qua thi so 0 moi duoc trich vao bai:
   1. DOI CHUNG DUONG: cau viet dung kieu bai bao that, phai bat duoc.
   2. DOI CHUNG AM: cau gan giong nhung khong phai, phai bo qua. Gom mot ca KHO:
      "The 3GPP standard defines many services" khong duoc tinh la mo hinh kenh NTN.
   3. CO SU SONG: bo do phai bat duoc thu gi do tren toan van THAT, neu khong thi co the
      duong dan hong hoac van ban rong.

Chay:  python3 code/e2c_detector_controls.py
"""
import importlib.util, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("e2b", os.path.join(HERE, "e2b_extract_evidence.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
RX = {c: re.compile(p, re.I) for c, _, p in m.CHECKLIST}

POS = {"CH_TRACE": ["Satellite positions are propagated from public TLE sets using the SGP4 model.",
                    "We use two-line element data and STK to generate the ephemeris.",
                    "Orbits were generated with Systems Tool Kit (STK)."],
       "DOPPLER_RATE": ["The Doppler rate reaches 10 kHz per second during a pass.",
                        "We model the time-varying Doppler across the visibility window.",
                        "Doppler drift is compensated every frame."],
       "CH_3GPP": ["We adopt the 3GPP TR 38.811 NTN channel model.",
                   "A tapped delay line (TDL) profile is used."],
       "DOPPLER": ["The carrier frequency offset is estimated at the receiver."]}
NEG = [("CH_TRACE", "The model is trained on the CIFAR-10 dataset."),
       ("DOPPLER_RATE", "We evaluate the Doppler shift at a fixed value of 100 kHz."),
       ("CH_3GPP", "The 3GPP standard defines many services.")]

def main():
    bad = 0
    for code, ss in POS.items():
        for s in ss:
            ok = bool(RX[code].search(s))
            bad += 0 if ok else 1
            print("  DUONG %-13s %s %s" % (code, "ok " if ok else "⛔ BO SOT", s[:62]))
    for code, s in NEG:
        hit = bool(RX[code].search(s))
        bad += 1 if hit else 0
        print("  AM    %-13s %s %s" % (code, "⛔ BAT NHAM" if hit else "ok ", s[:62]))
    ev = os.path.join(ROOT, "results", "e2b_evidence.json")
    if not os.path.exists(ev):
        print("  ⛔ chua co e2b_evidence.json, chay e2b truoc"); return 2
    d = json.load(io.open(ev, encoding="utf-8"))
    its = [r for r in d["items"] if r.get("fulltext")]
    alive = sum(r["evidence"][c]["n_intro"] + r["evidence"][c]["n_eval"] for r in its for c in RX)
    print("  SONG  tong cau bat duoc tren %d toan van that: %d" % (len(its), alive))
    if alive == 0:
        print("  ⛔ BO DO KHONG BAT GI TREN VAN BAN THAT"); bad += 1
    print("  => %s" % ("✅ BO DO LANH, so 0 duoc phep trich" if bad == 0 else "⛔ HONG %d ca" % bad))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
