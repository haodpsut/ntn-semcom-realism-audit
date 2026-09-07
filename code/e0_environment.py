"""E0 — thu MOI TRUONG CHAY that su cua ca hai may, ghi vao results/environment.json.

⛔ VI SAO CAN. Bai nay di kiem toan van lieu vi khong khai DIEU KIEN danh gia. Neu chinh no
khong khai may nao chay phep do nao, voi phien ban thu vien nao, thi no dang mac dung loi ma no
di phe binh, va nguoi phan bien se noi dieu do truoc.

⚠ Bai TRON HAI MAY: hinh hoc quy dao chay tren may tram (thuan CPU), con huan luyen bo ma chay
tren may chu GPU. So trong ghi rang moi con so cua MOT bai phai den tu MOT may, sau khi cung mot
script cho 0,1198 tren Linux va 0,1140 tren Mac. Luat do van dung, va o day no KHONG bi vi pham:
khong phep do nao chay tren ca hai may, nen khong dai luong nao co hai gia tri. Dieu can lam la
KHAI RA, chu khong phai giau.

Chay tren may tram:   python3 code/e0_environment.py
Chay tren may GPU:    python3 code/e0_environment.py --gpu-server
"""
import io, json, os, platform, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "environment.json")


def ver(name):
    try:
        return getattr(__import__(name), "__version__", "?")
    except Exception:
        return None


def cpu():
    if platform.system() == "Darwin":
        return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                              capture_output=True, text=True).stdout.strip()
    try:
        for l in io.open("/proc/cpuinfo", encoding="utf-8"):
            if l.startswith("model name"):
                return l.split(":", 1)[1].strip()
    except Exception:
        pass
    return "?"


def main():
    key = "gpu_server" if "--gpu-server" in sys.argv else "workstation"
    rec = {"os": "%s %s" % (platform.system(), platform.machine()), "cpu": cpu(),
           "python": platform.python_version()}
    for m in ("numpy", "matplotlib", "sgp4", "torch"):
        v = ver(m)
        if v:
            rec[m] = v
    if key == "gpu_server":
        try:
            import torch
            rec["cuda"] = torch.version.cuda
            rec["gpu"] = torch.cuda.get_device_name(0)
        except Exception:
            pass
    doc = json.load(io.open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {"machines": {}}
    doc["machines"].setdefault(key, {}).update(rec)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, indent=1, ensure_ascii=False))
    print("  da ghi %s cho '%s'" % (OUT, key))
    return 0


if __name__ == "__main__":
    sys.exit(main())
