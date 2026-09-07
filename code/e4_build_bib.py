"""E4 — Dung thu muc tham khao tu NGUON GOC, khong chep lai chuoi trich dan cua khao sat.

⛔ VI SAO. Trong so co luat: ref phai mo nguon goc va kiem sau truong; loi song sot thuong nam
o TAC GIA THU HAI va DUOI TIEU DE. Chuoi trich dan trong khao sat 2606.05216 la nguon THU CAP:
neu no sai thi bai nay chep nguyen cai sai, va bon cong kiem ref deu se bao xanh vi chung chi so
bai voi tep .bib chu khong so voi the gioi.

⇒ Tep nay hoi thang arXiv API cho tung cong trinh DA KHOP TIEU DE o E2a, lay tac gia, tieu de,
nam va DOI tu ban ghi goc. Cong trinh nao khong xac minh duoc thi ghi ro trang thai va KHONG
duoc dua vao .bib.

⚠ BA TRANG THAI, khong phai hai: "xac minh duoc" · "khong co ban arXiv" · "loi mang". Ca thu ba
KHONG duoc gop vao ca thu hai, vi mot loi mang bi doc thanh "khong ton tai" chinh la lop loi
cong-cu-hong-doc-thanh-ket-qua-am da ghi trong so.

Chay:  python3 code/e4_build_bib.py
"""

import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FETCH = os.path.join(ROOT, "results", "e2_fetch_population.json")
OUTB = os.path.join(ROOT, "paper", "refs-population.bib")
OUTJ = os.path.join(ROOT, "results", "e4_bib.json")
UA = {"User-Agent": "ntn-semcom-audit/1.0 (research; haodp@dau.edu.vn)"}


def api(aid):
    url = "http://export.arxiv.org/api/query?id_list=%s" % urllib.parse.quote(aid.split("v")[0])
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            return r.read().decode("utf-8", "replace"), None
    except Exception as e:
        return None, "loi mang: %s" % type(e).__name__


def field(xml, tag):
    m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), xml, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else None


def parse(xml):
    entry = re.search(r"<entry>(.*?)</entry>", xml, re.S)
    if not entry:
        return None
    e = entry.group(1)
    authors = [re.sub(r"\s+", " ", a).strip()
               for a in re.findall(r"<name>(.*?)</name>", e, re.S)]
    pub = field(e, "published")
    doi = field(e, "arxiv:doi") or None
    jref = field(e, "arxiv:journal_ref") or None
    return {"title": field(e, "title"), "authors": authors,
            "year": (pub or "")[:4], "doi": doi, "journal_ref": jref}


def key_of(rec, ref):
    a = (rec["authors"][0].split()[-1] if rec["authors"] else "anon")
    return re.sub(r"[^A-Za-z]", "", a).lower() + str(rec["year"]) + "r%d" % ref


def main():
    doc = json.load(io.open(FETCH, encoding="utf-8"))
    items = [i for i in doc["items"] if i.get("arxiv_id") and i["arxiv_id"] != "(da co trong cache)"]
    # bai nam trong cache tu lan chay truoc cung can metadata: tra lai tu tieu de
    print("  E4 — %d cong trinh co ma arXiv da khop tieu de\n" % len(items))
    out, nb, nerr = [], 0, 0
    entries = []
    for i, it in enumerate(items, 1):
        xml, err = api(it["arxiv_id"])
        time.sleep(3.2)
        if err:
            out.append({"ref": it["ref"], "status": err})
            nerr += 1
            print("   %2d [%3d] ⛔ %s" % (i, it["ref"], err), flush=True)
            continue
        rec = parse(xml)
        if not rec or not rec["title"]:
            out.append({"ref": it["ref"], "status": "khong doc duoc ban ghi arXiv"})
            nerr += 1
            continue
        k = key_of(rec, it["ref"])
        rec.update(ref=it["ref"], key=k, arxiv_id=it["arxiv_id"], status="xac minh tu arXiv")
        out.append(rec)
        nb += 1
        auth = " and ".join(rec["authors"])
        ent = ["@article{%s," % k, "  author  = {%s}," % auth,
               "  title   = {{%s}}," % rec["title"], "  year    = {%s}," % rec["year"],
               "  journal = {%s}," % (rec["journal_ref"] or
                                      "arXiv preprint arXiv:%s" % rec["arxiv_id"])]
        if rec["doi"]:
            ent.append("  doi     = {%s}," % rec["doi"])
        ent.append("}")
        entries.append("\n".join(ent))
        print("   %2d [%3d] %-52s %s" % (i, it["ref"], rec["title"][:52],
                                         "%d tac gia" % len(rec["authors"])), flush=True)

    os.makedirs(os.path.dirname(OUTB), exist_ok=True)
    io.open(OUTB, "w", encoding="utf-8").write(
        "%% SINH TU DONG boi code/e4_build_bib.py tu ban ghi arXiv GOC. Khong sua tay.\n"
        "%% Chi chua cong trinh XAC MINH DUOC. Cong trinh khong xac minh duoc nam o\n"
        "%% results/e4_bib.json voi ly do cu the, va KHONG duoc trich trong bai.\n\n"
        + "\n\n".join(entries) + "\n")
    io.open(OUTJ, "w", encoding="utf-8").write(json.dumps(
        {"n_verified": nb, "n_failed": nerr, "items": out}, ensure_ascii=False, indent=1))
    print("\n  xac minh: %d · that bai: %d" % (nb, nerr))
    print("  da ghi %s" % OUTB)
    return 0


if __name__ == "__main__":
    sys.exit(main())
