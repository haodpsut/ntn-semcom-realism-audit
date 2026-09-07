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

SEEDS = [0, 1, 2, 3, 4]                    # 5 seed: diem 4 cua phan bien
K = E3.C_CH * 8 * 8 // 2                   # 512 ky hieu phuc, giu nguyen bo ma
L_GRID = [1, 32, 128, 512]                 # 1 = bam hoan hao; 512 = vong ho nhu (11)
EPS_GRID = [0.0, 1e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]


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
           "snr_db": E3.SNR_TRAIN, "epochs": E3.EPOCHS,
           "predicted_cliff": {str(L): (None if L == 1 else 1.0 / (2 * (L - 1)))
                               for L in L_GRID},
           "note": "bo ma va ti le nen KHONG doi giua cac L; chi khoang uoc luong lai pha doi",
           "runs": {}}
    for mode in ("fixed", "aug"):
        doc["runs"][mode] = []
        for seed in SEEDS:
            t0 = time.time()
            m = E3.train(mode, seed, tr)
            grid = {}
            for L in L_GRID:
                grid[str(L)] = {("%.0e" % e): evaluate(m, te, E3.SNR_TRAIN, e, L, seed)
                                for e in EPS_GRID}
            doc["runs"][mode].append({"seed": seed, "grid": grid, "train_s": time.time() - t0})
            print("    %s seed%d %.0fs · L=512 eps=1e-3: %.2f · L=32 eps=1e-3: %.2f"
                  % (mode, seed, time.time() - t0,
                     grid["512"]["1e-03"], grid["32"]["1e-03"]), flush=True)
            io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=1))
    print("  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
