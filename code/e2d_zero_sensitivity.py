"""E2d — hai so 0 co song noi neu quang LUOI RONG HON NHIEU khong?

⛔ SINH RA TU DIEM CHAN SO 5 cua phan bien ngoai: 312 o da ma hoa, hai so 0 la tuyen bo trung
tam, ma khong co so nao ve do tin cay.

⚠ TOI KHONG LAM DUNG CAI HO DE NGHI, va noi ro vi sao. Ho de nghi bao he so Cohen giua hai nguoi
ma hoa. Voi mot o CO bang chung thi he so do co nghia. Voi mot o BANG 0 thi khong: khong co cau
nao de hai nguoi cung doc va bat dong. Do do bai chi la mot nguoi ma hoa thi bao kappa se la mot
con so trang tri.

⇒ Cau hoi dung cho mot so 0 la: **bo do co qua hep khong?** Tep nay quang mot luoi RONG HON HAN
danh muc goc cho dung hai hang muc bang 0, gom ca cach dien dat khong chua tu khoa hien nhien
(vi du "chirp", "frequency drift", "second-order phase" cho Doppler bien thien; "Keplerian",
"Celestrak", "STK", "orbit propagation" cho vet quy dao). Neu luoi rong gap nhieu lan van khong
bat duoc gi, so 0 khong phai do luoi hep.

⚠ Va tep nay VAN khong ra phan quyet: no in ra MOI cau bat duoc de nguoi doc tu xet.

Chay:  python3 code/e2d_zero_sensitivity.py
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import e2b_extract_evidence as E2B                                     # noqa: E402

FETCH = os.path.join(ROOT, "results", "e2_fetch_population.json")
OUT = os.path.join(ROOT, "results", "e2d_zero_sensitivity.json")

# Luoi RONG. Moi hang muc gom ca tu khoa goc lan cac cach noi vong.
WIDE = {
 "DOPPLER_RATE": (
   r"doppler[- ]?(rate|drift|slope|acceleration|derivative|variation|dynamics)"
   r"|(rate|drift|slope|acceleration|derivative)\s+of\s+(the\s+)?doppler"
   r"|time[- ]var(y|ing)\s+(doppler|frequency\s+offset|cfo)"
   r"|frequency\s+(drift|ramp|slope|acceleration)"
   r"|second[- ]order\s+phase|quadratic\s+phase|phase\s+acceleration"
   r"|\bchirp\b|\bLFM\b|linear\s+frequency\s+modulat"
   r"|doppler.{0,40}(per\s+second|/s\b|kHz/s)"
   r"|residual\s+(doppler|cfo).{0,30}(track|vary|change)"),
 "CH_TRACE": (
   r"\bTLE\b|two[- ]line\s+element|\bSGP4\b|\bSDP4\b|ephemerid|ephemeris"
   r"|celestrak|space[- ]track\b|\bSTK\b|systems\s+tool\s+kit"
   r"|orbit\s+(propagat|simulat|generat)|propagat\w*\s+the\s+orbit"
   r"|keplerian|orbital\s+element|walker\s+constellation"
   r"|\bskyfield\b|\bpoliastro\b|\bGMAT\b|\bpyephem\b|\borekit\b"
   r"|starlink\s+(trace|ephemer|data)|real\s+(orbit|constellation)\s+data"
   r"|measured\s+(trace|channel)\s+data"),
}


def main():
    doc = json.load(io.open(FETCH, encoding="utf-8"))
    items = [i for i in doc["items"] if i.get("status") == "toan van OK" and i.get("path")]
    print("  E2d — quang luoi RONG tren %d toan van\n" % len(items))
    res = {"n_docs": len(items), "patterns": {k: v for k, v in WIDE.items()}, "hits": {}}
    for code, pat in WIDE.items():
        rx = re.compile(pat, re.I)
        narrow = dict((c, p) for c, _, p in E2B.CHECKLIST)[code]
        rxn = re.compile(narrow, re.I)
        hits, n_sent = [], 0
        for it in items:
            raw = io.open(os.path.join(ROOT, it["path"]), encoding="utf-8",
                          errors="replace").read()
            sents = E2B.sentences(E2B.strip_html(raw))
            n_sent += len(sents)
            for s in sents:
                if rx.search(s):
                    hits.append({"ref": it["ref"], "sentence": s[:400],
                                 "also_narrow": bool(rxn.search(s))})
        res["hits"][code] = hits
        print("  %-14s luoi RONG: %d cau tren %d cau da quet"
              % (code, len(hits), n_sent))
        for h in hits[:8]:
            print("     [%3d] %s%s" % (h["ref"], "" if h["also_narrow"] else "(luoi goc BO SOT) ",
                                       h["sentence"][:110]))
        res.setdefault("n_sentences", n_sent)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
    print("\n  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
