"""E3 — Mo hinh huan luyen o MOT diem SNR con dung o dau kia cua luot bay khong?

⛔ DAY LA PHAN [dependent] CUA TO KHAI. Neu no ra null (mo hinh giu nguyen chat luong tren ca
dai SNR va duoi Doppler du) thi ba dong gop [independent] van con, va bai doi giong chu khong
doi so dong gop. Da ghi truoc o `claim-structure.md`.

⚠ KHONG BIA RA MOT HE THONG. Hai cho de bia nhat da duoc chan:

 1. **SNR.** Dai SNR khong do tac gia chon. No lay tu E1: bien thien FSPL tron mot luot bay,
    trung vi 3,72 dB va cuc dai 6,48 dB, do tren 30.922 luot bay tu TLE that. Va do la CAN DUOI
    vi E1 chi tinh hinh hoc.

 2. **Doppler.** Khong dat "toc do ky hieu" nao ca, vi moi lua chon deu tuy tien. Tham so hoa
    bang **do lech tan chuan hoa** eps = f_res / R_s, tuc goc quay pha cong them tren MOI lan
    dung kenh. Dai eps quet duoc quy chieu ve so do that cua E1 o phan bao cao: voi f_d = 359
    kHz (Ka-band, trung vi) va R_s = 10 Msym/s thi eps khong bu = 0,0359; bu duoc 99% thi
    eps = 3,59e-4. Nguoi doc doi R_s cua ho vao la ra ngay diem lam viec cua ho.

**Bon nhanh, va nhanh thu tu la CACH CHUA chu khong phai loi phan nan:**
  A. train-fixed  : huan luyen tai MOT SNR (thuc hanh pho bien: 16/26 bai dung AWGN co dinh)
  B. eval-sweep   : cung mo hinh A, danh gia tren ca dai SNR cua luot bay
  C. eval-cfo     : cung mo hinh A, danh gia duoi do lech tan du
  D. train-aug    : huan luyen co ngau nhien hoa SNR va CFO ⇒ do xem loi co CHUA DUOC RE khong

Chay:  CUDA_VISIBLE_DEVICES=1 python code/e3_train_eval.py
⚠ GPU 0 tren sol1 dang co nguoi khac dung. Chi dung GPU 1.
"""

import io
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "results", "e3_train_eval.json")
DATA = os.path.join(ROOT, "data", "torchvision")

SEEDS = [0, 1, 2]
EPOCHS = int(os.environ.get("NTN_EPOCHS", "30"))
BATCH = 128
C_CH = 16                       # kenh dac trung -> 16*8*8/2 = 512 ky hieu phuc
SNR_TRAIN = 10.0                # dB, diem huan luyen co dinh
# Dai quet SNR: +-4 dB bao tron ca bien thien FSPL trung vi 3,72 va cuc dai 6,48 cua E1
SNR_EVAL = [float(x) for x in np.arange(4.0, 16.5, 1.0)]
EPS_EVAL = [0.0, 1e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2]
DEV = "cuda" if torch.cuda.is_available() else "cpu"


class JSCC(nn.Module):
    """DeepJSCC kieu Bourtsoulatze 2019: ma hoa tich chap, chuan hoa cong suat, giai ma."""

    def __init__(self, c=C_CH):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(3, 64, 5, 2, 2), nn.PReLU(),
            nn.Conv2d(64, 128, 5, 2, 2), nn.PReLU(),
            nn.Conv2d(128, 128, 5, 1, 2), nn.PReLU(),
            nn.Conv2d(128, 128, 5, 1, 2), nn.PReLU(),
            nn.Conv2d(128, c, 5, 1, 2))
        self.dec = nn.Sequential(
            nn.ConvTranspose2d(c, 128, 5, 1, 2), nn.PReLU(),
            nn.ConvTranspose2d(128, 128, 5, 1, 2), nn.PReLU(),
            nn.ConvTranspose2d(128, 128, 5, 1, 2), nn.PReLU(),
            nn.ConvTranspose2d(128, 64, 5, 2, 2, output_padding=1), nn.PReLU(),
            nn.ConvTranspose2d(64, 3, 5, 2, 2, output_padding=1), nn.Sigmoid())

    def encode(self, x):
        z = self.enc(x)
        b = z.shape[0]
        v = z.reshape(b, -1)
        # chuan hoa cong suat trung binh ve 1 tren moi anh
        v = v * torch.sqrt(torch.tensor(v.shape[1], dtype=v.dtype, device=v.device)) \
            / (v.norm(dim=1, keepdim=True) + 1e-9)
        return v, z.shape

    def decode(self, v, shape):
        return self.dec(v.reshape(shape))


def channel(v, snr_db, eps, gen):
    """Kenh AWGN phuc, kem do lech tan du eps = f_res/R_s.

    ⚠ eps gay QUAY PHA TICH LUY theo chi so ky hieu: phi_k = 2*pi*eps*k. Day dung la co che
    vat ly cua do lech tan chua bu het, va no KHAC voi nhieu pha ngau nhien: no co huong.
    """
    b, n = v.shape
    c = torch.complex(v[:, 0::2], v[:, 1::2])                 # n/2 ky hieu phuc
    if eps:
        k = torch.arange(c.shape[1], device=v.device, dtype=torch.float32)
        c = c * torch.exp(1j * 2 * np.pi * eps * k)
    sig_p = (c.abs() ** 2).mean()
    n0 = sig_p / (10 ** (snr_db / 10.0))
    nr = torch.randn(c.shape, generator=gen, device=v.device) * torch.sqrt(n0 / 2)
    ni = torch.randn(c.shape, generator=gen, device=v.device) * torch.sqrt(n0 / 2)
    y = c + torch.complex(nr, ni)
    out = torch.zeros_like(v)
    out[:, 0::2] = y.real
    out[:, 1::2] = y.imag
    return out


def psnr(a, b):
    mse = F.mse_loss(a, b, reduction="none").reshape(a.shape[0], -1).mean(1)
    return (10 * torch.log10(1.0 / torch.clamp(mse, min=1e-12))).mean().item()


def loaders():
    tf = transforms.ToTensor()
    tr = datasets.CIFAR10(DATA, train=True, download=True, transform=tf)
    te = datasets.CIFAR10(DATA, train=False, download=True, transform=tf)
    return (torch.utils.data.DataLoader(tr, BATCH, shuffle=True, num_workers=4, drop_last=True),
            torch.utils.data.DataLoader(te, 256, shuffle=False, num_workers=4))


def train(mode, seed, tr):
    torch.manual_seed(seed)
    np.random.seed(seed)
    m = JSCC().to(DEV)
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    gen = torch.Generator(device=DEV).manual_seed(seed + 777)
    rng = np.random.default_rng(seed + 999)
    for ep in range(EPOCHS):
        m.train()
        for x, _ in tr:
            x = x.to(DEV, non_blocking=True)
            if mode == "fixed":
                snr, eps = SNR_TRAIN, 0.0
            else:                       # 'aug': ngau nhien hoa dung dai do duoc o E1
                snr = float(rng.uniform(SNR_TRAIN - 4.0, SNR_TRAIN + 4.0))
                eps = float(10 ** rng.uniform(-5, -2)) if rng.random() < 0.5 else 0.0
            v, sh = m.encode(x)
            xh = m.decode(channel(v, snr, eps, gen), sh)
            loss = F.mse_loss(xh, x)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
        if (ep + 1) % 10 == 0:
            print("      %s seed%d ep%02d loss %.5f" % (mode, seed, ep + 1, loss.item()),
                  flush=True)
    return m


@torch.no_grad()
def evaluate(m, te, snr, eps, seed):
    m.eval()
    gen = torch.Generator(device=DEV).manual_seed(seed + 4242)
    tot, n = 0.0, 0
    for x, _ in te:
        x = x.to(DEV, non_blocking=True)
        v, sh = m.encode(x)
        xh = m.decode(channel(v, snr, eps, gen), sh)
        tot += psnr(xh, x) * x.shape[0]
        n += x.shape[0]
    return tot / n


def main():
    print("  E3 — thiet bi %s · %s" % (DEV, torch.cuda.get_device_name(0) if DEV == "cuda" else ""))
    print("  %d seed x %d epoch x 2 che do huan luyen" % (len(SEEDS), EPOCHS))
    tr, te = loaders()
    doc = {"seeds": SEEDS, "epochs": EPOCHS, "snr_train_db": SNR_TRAIN,
           "c_channels": C_CH, "bandwidth_ratio": C_CH * 8 * 8 / 2 / (32 * 32 * 3),
           "snr_eval_db": SNR_EVAL, "eps_eval": EPS_EVAL, "device": DEV,
           "e1_link": {"fspl_swing_median_db": 3.72, "fspl_swing_max_db": 6.48,
                       "doppler_ka_median_khz": 359.2,
                       "note": "dai SNR quet lay tu E1, khong do tac gia chon"},
           "runs": {}}
    for mode in ("fixed", "aug"):
        doc["runs"][mode] = []
        for seed in SEEDS:
            t0 = time.time()
            m = train(mode, seed, tr)
            r = {"seed": seed,
                 "snr_curve": {("%.1f" % s): evaluate(m, te, s, 0.0, seed) for s in SNR_EVAL},
                 "cfo_curve": {("%.0e" % e): evaluate(m, te, SNR_TRAIN, e, seed)
                               for e in EPS_EVAL},
                 "train_s": time.time() - t0}
            doc["runs"][mode].append(r)
            print("    %s seed%d xong %.0fs · PSNR@%gdB=%.2f · PSNR@eps=1e-3: %.2f"
                  % (mode, seed, r["train_s"], SNR_TRAIN,
                     r["snr_curve"]["%.1f" % SNR_TRAIN], r["cfo_curve"]["1e-03"]), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, ensure_ascii=False, indent=1))
    print("  da ghi %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
