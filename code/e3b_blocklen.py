"""E3b — vach da di chuyen theo DO DAI KHOI hay khong, va vong kin thi sao.

⛔ SINH RA TU HAI DIEM CHAN CUA PHAN BIEN NGOAI, va ca hai deu dung.

  Diem 2. Con so dau bai "bu duoc 97%" phu thuoc HOAN TOAN vao k = 512, ma k chua bao gio duoc
  quet. Ho tinh: k=64 thi chi con 78%, k=4096 thi len 99,7%. Toi kiem lai: 77,9% va 99,7%. Dung.

  Diem 3. Cong thuc (11) la mot doc pha VONG HO tich luy 3,21 radian tron khoi. May thu that co
  vong bam song mang se sua mot do lech du 10 kHz trong vai ky hieu chu khong de no tich luy.
  Cach dat "he thong lam an tu te" phu thuoc vao mot lua chon kien truc chua he duoc khai.

⭐ MOT thi nghiem tra loi CA HAI, va no khong phai la tron hai cau hoi lai:

  Doi k tuc la doi ca TI LE NEN, vi k = C*8*8/2 va R = k/n. Nhu vay quet k se lan hai hieu ung
  vao nhau va khong ket luan duoc gi. Thay vao do, GIU NGUYEN bo ma va dat lai pha sau moi L ky
  hieu:

        phi_m = 2*pi*eps*(m mod L)

  L la khoang UOC LUONG LAI song mang. L = k la vong ho, dung nhu (11). L = 1 la bam hoan hao.
  L o giua la mot may thu uoc luong lai pha dinh ky, tuc dung cai ma nguoi phan bien noi may thu
  that lam. Ti le nen KHONG doi khi L doi, nen hieu ung tach bach.

  Va (13) tro thanh mot DU DOAN KIEM DUOC: vach da phai o eps = 1/(2(L-1)), tuc phai DICH theo L
  dung mot he so biet truoc. Bai truoc chi kiem du doan o mot diem; nay kiem no o nam diem.

⚠ Diem 4 cua phan bien (3 seed, do trai 4,03 dB, ma bao 2 chu so thap phan) cung sua o day:
  nang len 5 seed va bao khoang tin cay chu khong bao diem.

Chay:  CUDA_VISIBLE_DEVICES=1 python code/e3b_blocklen.py
"""

import io
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn.functional as F

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import e3_train_eval as E3                                            # noqa: E402

ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "e3b_blocklen.json")

# ⛔ Ti le SAP cao (4/10 tren hai lan chay), nen so seed can chay > so lan chay hop le muon co.
#    Cho phep chi dinh dai seed va nhanh qua bien moi truong, va GOP vao tep ket qua da co thay
#    vi ghi de: chay them seed KHONG duoc lam mat cac lan chay hop le da co.
SEEDS = [int(x) for x in os.environ.get("NTN_SEEDS", "0,1,2,3,4").split(",")]
MODES = tuple(os.environ.get("NTN_MODES", "fixed,aug").split(","))
K = E3.C_CH * 8 * 8 // 2                   # 512 ky hieu phuc, giu nguyen bo ma
# ⛔ NOI DAI 07/09/2026 theo de nghi cua phan bien vong 2: ba diem tren 16x la mong de khang
#    dinh mot quy luat co gian. Nay nam diem kiem duoc tren 256x (L = 2 den 512).
L_GRID = [1, 2, 8, 32, 128, 512]           # 1 = bam hoan hao; 512 = vong ho nhu (11)
EPS_GRID = [0.0, 1e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
SNR_GRID = [float(x) for x in np.arange(4.0, 16.5, 1.0)]

# ⛔ NGUONG HOP LE, khai TRUOC khi chay. Mot lan chay ma PSNR tren kenh SACH khong vuot nguong
#    nay la mo hinh CHET chu khong phai mot phep do, va PHAI bi loai ra khoi moi thong ke, kem
#    bao cao ti le sap. Khong co nguong nay thi 3 lan chay sap da duoc gop vao trung vi va lam
#    hong ca ket qua. Du lieu ra phai co BA trang thai: do duoc / khong do duoc / cong cu hong.
VALID_PSNR_MIN = 20.0


def channel_L(v, snr_db, eps, L, gen):
    """Kenh AWGN phuc voi do lech tan du, DAT LAI PHA sau moi L ky hieu."""
    b, n = v.shape
    c = torch.complex(v[:, 0::2], v[:, 1::2])
    if eps:
        m = torch.arange(c.shape[1], device=v.device, dtype=torch.float32)
        m = m % L if L > 1 else torch.zeros_like(m)
        c = c * torch.exp(1j * 2 * np.pi * eps * m)
    sig_p = (c.abs() ** 2).mean()
    n0 = sig_p / (10 ** (snr_db / 10.0))
    nr = torch.randn(c.shape, generator=gen, device=v.device) * torch.sqrt(n0 / 2)
    ni = torch.randn(c.shape, generator=gen, device=v.device) * torch.sqrt(n0 / 2)
    y = c + torch.complex(nr, ni)
    out = torch.zeros_like(v)
    out[:, 0::2] = y.real
    out[:, 1::2] = y.imag
    return out


@torch.no_grad()
def evaluate(m, te, snr, eps, L, seed):
    m.eval()
    gen = torch.Generator(device=E3.DEV).manual_seed(seed + 4242)
    tot, n = 0.0, 0
    for x, _ in te:
        x = x.to(E3.DEV, non_blocking=True)
        v, sh = m.encode(x)
        xh = m.decode(channel_L(v, snr, eps, L, gen), sh)
        tot += E3.psnr(xh, x) * x.shape[0]
        n += x.shape[0]
    return tot / n


def main():
    print("  E3b — %d seed · k=%d ky hieu · L in %s" % (len(SEEDS), K, L_GRID))
    print("  du doan tu (13): vach da o eps = 1/(2(L-1))")
    for L in L_GRID:
        print("     L=%4d -> eps du doan %s" % (L, "khong co (bam hoan hao)" if L == 1
                                                else "%.3e" % (1.0 / (2 * (L - 1)))))
    tr, te = E3.loaders()
    doc = {"seeds": SEEDS, "k_symbols": K, "L_grid": L_GRID, "eps_grid": EPS_GRID,
           "snr_db": E3.SNR_TRAIN, "epochs": E3.EPOCHS, "snr_grid": SNR_GRID,
           "valid_psnr_min": VALID_PSNR_MIN,
           "predicted_cliff": {str(L): (None if L == 1 else 1.0 / (2 * (L - 1)))
                               for L in L_GRID},
           "note": "bo ma va ti le nen KHONG doi giua cac L; chi khoang uoc luong lai pha doi",
           "runs": {}}
    # gop voi ket qua da co
    if os.path.exists(OUT):
        prev = json.load(io.open(OUT, encoding="utf-8"))
        doc["runs"] = prev.get("runs", {})
        doc["seeds"] = sorted(set(prev.get("seeds", [])) | set(SEEDS))
    for mode in MODES:
        doc["runs"].setdefault(mode, [])
        done = {r["seed"] for r in doc["runs"][mode]}
        for seed in SEEDS:
            if seed in done:
                continue
            t0 = time.time()
            m = E3.train(mode, seed, tr)
            # ⚠ Luu trong so: L la tham so DANH GIA, nen moi lan nay dai L sau nay khong can
            #    huan luyen lai. Lan truoc phai chay lai 45 phut chi de them hai gia tri L.
            wdir = os.path.join(ROOT, "results", "weights")
            os.makedirs(wdir, exist_ok=True)
            torch.save(m.state_dict(), os.path.join(wdir, "%s_seed%d.pt" % (mode, seed)))
            grid = {}
            for L in L_GRID:
                grid[str(L)] = {("%.0e" % e): evaluate(m, te, E3.SNR_TRAIN, e, L, seed)
                                for e in EPS_GRID}
            snr = {("%.1f" % v): evaluate(m, te, v, 0.0, K, seed) for v in SNR_GRID}
            clean = grid["512"]["0e+00"]
            valid = clean >= VALID_PSNR_MIN
            doc["runs"][mode].append({"seed": seed, "grid": grid, "snr_curve": snr,
                                      "clean_psnr": clean, "valid": valid,
                                      "train_s": time.time() - t0})
            print("    %s seed%d %.0fs · sach %.2f %s · L=512 eps=1e-3: %.2f · L=32: %.2f"
                  % (mode, seed, time.time() - t0, clean,
                     "OK" if valid else "⛔ SAP, LOAI",
                     grid["512"]["1e-03"], grid["32"]["1e-03"]), flush=True)
            io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=1))
    print("  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
