"""E2b — TRICH BANG CHUNG cho kiem ke. ⛔ TEP NAY KHONG RA PHAN QUYET.

⛔ VI SAO. Cam do la bien mot cong cu tim tu khoa thanh mot cong dinh toi: "bai khong chua chu
'Doppler' ⇒ bai khong mo phong Doppler". Do la SUY SU KIEN TU DAU VET MO, va no sai theo ca hai
chieu. Sai chieu duong: mot bai co the noi "carrier frequency offset" thay vi "Doppler". Sai
chieu am: mot bai co the nhac Doppler trong phan mo dau roi khong bao gio mo phong no, va dem
theo tu khoa se tinh la CO.

⇒ Tep nay chi lam MOT viec: voi moi hang muc trong danh muc, keo ve MOI CAU chua dau hieu cua
hang muc do, kem vi tri trong bai. Phan quyet do NGUOI doc bang chung dua ra va ghi vao phieu ma
hoa. Phieu duoc phat hanh kem bai, nen ai cung kiem lai duoc tung phan quyet tren tung cau trich.

⚠ Chia bai lam hai vung: PHAN DAU (mo dau, dan nhap, cong trinh lien quan) va PHAN DANH GIA
(thiet lap thi nghiem, ket qua). Mot khai bao ve Doppler o PHAN DAU la DONG CO; chi khi no xuat
hien o PHAN DANH GIA thi moi la BANG CHUNG rang phep danh gia hien thuc hoa no. Day chinh la
khac biet ma bai di do.

Danh muc neo vao 3GPP TR 38.821 va bay rang buoc do CHINH khao sat cua linh vuc neu ra, khong
phai do tac gia bai nay tu nghi.

Chay:  python3 code/e2b_extract_evidence.py
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FETCH = os.path.join(ROOT, "results", "e2_fetch_population.json")
OUT = os.path.join(ROOT, "results", "e2b_evidence.json")

# Danh muc: ma -> (mo ta, cac dau hieu regex). Dau hieu la de TIM, khong de KET LUAN.
CHECKLIST = [
 ("DOPPLER", "do dich Doppler",
  r"doppler|carrier frequency offset|\bCFO\b|frequency offset"),
 ("DOPPLER_RATE", "Doppler bien thien theo thoi gian",
  r"doppler (rate|drift|variation|change)|time-varying doppler|doppler.{0,20}per second"),
 ("DELAY", "tre lan truyen",
  r"propagation delay|round[- ]trip (time|delay)|\bRTT\b|one[- ]way delay|latency of the link"),
 ("PATHLOSS_ELEV", "suy hao phu thuoc goc ngang / ngan sach duong truyen theo luot bay",
  r"elevation angle|free[- ]space path loss|\bFSPL\b|link budget|slant range|path loss.{0,40}elevation"),
 ("VISIBILITY", "cua so nhin thay huu han / gian doan",
  r"visibility window|visible time|contact (time|window)|intermitten|pass duration|coverage window"),
 ("ATMOS", "suy hao khi quyen / mua",
  r"rain (fade|attenuation)|atmospheric (loss|attenuation)|scintillation|cloud attenuation"),
 ("ONBOARD", "rang buoc tinh toan tren khoang",
  r"on[- ]board (compute|computation|processing|resource)|\bSWaP\b|payload (power|compute)|"
  r"energy budget.{0,30}satellite"),
 ("CH_AWGN", "kenh AWGN", r"\bAWGN\b|additive white gaussian"),
 ("CH_FADING", "kenh pha-dinh thong ke", r"rayleigh|rician|\bnakagami\b|shadowed[- ]rician"),
 ("CH_3GPP", "mo hinh kenh NTN theo chuan",
  r"38\.?811|38\.?821|3gpp.{0,25}ntn|ntn.{0,25}channel model|tapped delay line|\bTDL\b"),
 ("CH_TRACE", "vet do thuc / bo mo phong quy dao",
  r"\bTLE\b|two[- ]line element|\bSGP4\b|starlink trace|measured trace|ephemeris|\bSTK\b|systems tool kit"),
 ("SNR_SWEEP", "quet SNR / lech SNR giua huan luyen va kiem thu",
  r"snr (range|from|sweep)|range of snr|train(ed|ing)? (at|on).{0,25}snr|snr mismatch|"
  r"different snr|varying snr|test(ed)? (at|on).{0,25}snr"),
]

# Nhan dau PHAN DANH GIA. Mot khai bao truoc diem nay la DONG CO, sau la BANG CHUNG.
EVAL_HEAD = re.compile(
    r"(experimental (setup|results|evaluation)|simulation (setup|settings|results|parameters)"
    r"|performance evaluation|numerical results|experiments?\b|evaluation setup|"
    r"implementation details|dataset and (setup|training))", re.I)


def strip_html(h):
    h = re.sub(r"(?is)<(script|style|math)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    h = (h.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&#x2019;", "'").replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", h)


def sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if 25 < len(s.strip()) < 700]


def main():
    doc = json.load(io.open(FETCH, encoding="utf-8"))
    out = []
    n_eval_found = 0
    for it in doc["items"]:
        if it.get("status") != "toan van OK" or not it.get("path"):
            out.append({"ref": it["ref"], "title": it.get("title"),
                        "fulltext": False, "reason": it.get("status")})
            continue
        raw = io.open(os.path.join(ROOT, it["path"]), encoding="utf-8", errors="replace").read()
        txt = strip_html(raw)
        sents = sentences(txt)
        # xac dinh moc bat dau PHAN DANH GIA theo vi tri cau dau tien khop nhan
        cut = None
        for i, s in enumerate(sents):
            if EVAL_HEAD.search(s):
                cut = i
                break
        if cut is not None:
            n_eval_found += 1
        rec = {"ref": it["ref"], "title": it.get("title"), "fulltext": True,
               "n_sentences": len(sents),
               "eval_section_found": cut is not None,
               "eval_start_sentence": cut, "evidence": {}}
        for code, desc, pat in CHECKLIST:
            rx = re.compile(pat, re.I)
            hits_intro, hits_eval = [], []
            for i, s in enumerate(sents):
                if rx.search(s):
                    (hits_eval if (cut is not None and i >= cut) else hits_intro).append(
                        {"i": i, "s": s[:400]})
            rec["evidence"][code] = {
                "desc": desc,
                "n_intro": len(hits_intro), "n_eval": len(hits_eval),
                # giu toi da 4 cau moi vung: du de phan quyet, khong phinh tep
                "intro": hits_intro[:4], "eval": hits_eval[:4]}
        out.append(rec)

    res = {"n_items": len(out),
           "n_fulltext": sum(1 for r in out if r.get("fulltext")),
           "n_eval_section_located": n_eval_found,
           "checklist": [{"code": c, "desc": d} for c, d, _ in CHECKLIST],
           "note": "TEP NAY KHONG RA PHAN QUYET. Moi truong la SO CAU va CAU TRICH; "
                   "phan quyet ghi rieng o phieu ma hoa.",
           "items": out}
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
    print("  E2b — %d cong trinh · %d co toan van · %d dinh vi duoc PHAN DANH GIA"
          % (res["n_items"], res["n_fulltext"], n_eval_found))
    print("  da ghi %s (%.2f MB)" % (OUT, os.path.getsize(OUT) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
