"""E2a — LAY VE toan van cua quan the, va DO xem lay duoc bao nhieu.

⛔ VI SAO KHONG KIEM KE TU COT CUA KHAO SAT. Bang III/IV cua khao sat co cot
"Channel/protocol consideration", va doc luot thi rat de ket luan tu no: chi 2/23 o nhac
Doppler, 1/23 nhac cua so nhin thay, va nhieu o khong phai mo hinh kenh gi ca ("On-board sparse
encoder", "Hierarchical FL", "Energy harvesting").

Nhung mot cot tom tat KHONG phai bang chung ve viec bai goc lam gi. Bai co the mo phong Doppler
ma nguoi viet khao sat khong ghi vao o do, vi o do dai chua toi 30 ky tu. Ket luan tu cot nay se
la dung lop loi da ghi trong so: cong suy SU KIEN tu DAU VET MO.

⇒ Tep nay di lay TOAN VAN. Cai lay duoc thi ma hoa tu toan van; cai khong lay duoc thi ghi ro la
KHONG LAY DUOC va dem rieng, chu khong doan.

⚠ Ti le lay duoc CHINH NO la mot so cua bai: mot cong trinh khong doc duoc toan van thi khong
kiem toan duoc, va do la mot phat bieu ve tinh tai lap cua linh vuc nay.

Chay:  python3 code/e2_fetch_population.py
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
POP = os.path.join(ROOT, "data", "population_refs.json")
CACHE = os.path.join(ROOT, "data", "fulltext")
OUT = os.path.join(ROOT, "results", "e2_fetch_population.json")
UA = {"User-Agent": "ntn-semcom-audit/1.0 (research; haodp.sut@gmail.com)"}


def parse_title(cite):
    """Chuoi trich dan cua khao sat co dang 'TAC GIA (NAM) Tieu de . Venue...'."""
    m = re.search(r"\(\d{4}[a-z]?\)\s*(.+?)\s*\.\s", cite)
    if not m:
        return None
    t = m.group(1).strip(" .")
    return re.sub(r"\s+", " ", t)


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def arxiv_lookup(title):
    """Tra cuu arXiv theo TIEU DE. Chi nhan khi tieu de tra ve KHOP, khong nhan ket qua gan dung."""
    q = urllib.parse.quote('ti:"%s"' % title[:200])
    url = ("http://export.arxiv.org/api/query?search_query=%s"
           "&start=0&max_results=3" % q)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
            xml = r.read().decode("utf-8", "replace")
    except Exception as e:
        return None, "loi mang: %s" % type(e).__name__
    ids = re.findall(r"<id>http://arxiv\.org/abs/([^<]+)</id>", xml)
    tis = re.findall(r"<title>(.*?)</title>", xml, re.S)
    ids = ids[0:] if ids else []
    tis = [re.sub(r"\s+", " ", t).strip() for t in tis[1:]] if len(tis) > 1 else []
    for aid, at in zip(ids, tis):
        # ⛔ chi chap nhan khi tieu de TRUNG sau khi chuan hoa. arXiv tra ve ket qua gan dung,
        #    va nhan mot bai KHAC lam bai can kiem toan la lop loi te nhat co the.
        if norm(at) == norm(title):
            return aid, "khop tieu de"
    return None, "khong co ban arXiv khop tieu de"


def fetch_text(aid):
    base = aid.split("v")[0]
    for url in ("https://arxiv.org/html/%s" % aid, "https://arxiv.org/abs/%s" % base):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                b = r.read().decode("utf-8", "replace")
            if len(b) > 4000:
                return b, url
        except Exception:
            continue
    return None, None


def main():
    pop = json.load(io.open(POP, encoding="utf-8"))["population"]
    seen, items = set(), []
    for p in pop:
        if p["ref"] in seen:
            continue
        seen.add(p["ref"])
        items.append(p)
    os.makedirs(CACHE, exist_ok=True)
    print("  E2a — %d cong trinh trong quan the\n" % len(items))

    rows, n_ok = [], 0
    for i, p in enumerate(items, 1):
        title = parse_title(p["cite"])
        rec = {"ref": p["ref"], "table": p["table"], "cite": p["cite"], "title": title,
               "survey_channel_col": p.get("survey_channel_col")}
        if not title:
            rec.update(arxiv_id=None, status="khong doc duoc tieu de tu chuoi trich dan")
        else:
            cpath = os.path.join(CACHE, "ref%03d.html" % p["ref"])
            if os.path.exists(cpath):
                rec.update(arxiv_id="(da co trong cache)", status="toan van OK",
                           path=os.path.relpath(cpath, ROOT))
                n_ok += 1
            else:
                aid, why = arxiv_lookup(title)
                time.sleep(3.2)                       # arXiv API doi >=3s giua hai truy van
                if aid:
                    body, src = fetch_text(aid)
                    if body:
                        io.open(cpath, "w", encoding="utf-8").write(body)
                        rec.update(arxiv_id=aid, source=src, status="toan van OK",
                                   path=os.path.relpath(cpath, ROOT))
                        n_ok += 1
                    else:
                        rec.update(arxiv_id=aid, status="co arXiv nhung khong tai duoc toan van")
                else:
                    rec.update(arxiv_id=None, status=why)
        rows.append(rec)
        print("   %2d/%d [%3d] %-58s %s"
              % (i, len(items), p["ref"], (title or "?")[:58], rec["status"]), flush=True)

    doc = {"n_population": len(items), "n_fulltext": n_ok,
           "pct_fulltext": round(100.0 * n_ok / len(items), 1), "items": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=1))
    print("\n  lay duoc toan van: %d/%d = %.1f%%" % (n_ok, len(items), doc["pct_fulltext"]))
    print("  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
