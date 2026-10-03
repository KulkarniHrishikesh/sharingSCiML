"""NumPy-only blade pitch change for binary STL (runs on the compute pod; no pyvista).

Same method as pitch.py: each blade point is rotated about its spindle axis by
dphi * w(r), w a smoothstep from 0 at R1 to 1 at R2. Points are deformed as a
function of position only, so duplicated triangle vertices move identically and
the surface stays watertight.

Usage: python3 pitch_np.py base.stl out.stl dphi_deg
"""
import sys
import numpy as np

R1, R2, NB = 40.5e-3, 48.0e-3, 5
REC = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])


def read_stl(path):
    with open(path, "rb") as f:
        head = f.read(80)
        n = np.frombuffer(f.read(4), "<u4")[0]
        data = np.frombuffer(f.read(n * REC.itemsize), REC)
    return head, data["v"].astype(np.float64).reshape(-1, 3)


def write_stl(path, pts, head=b"pitch_np"):
    tri = pts.reshape(-1, 3, 3)
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    l = np.linalg.norm(nrm, axis=1, keepdims=True); l[l == 0] = 1
    rec = np.zeros(len(tri), REC)
    rec["n"] = (nrm / l).astype("<f4"); rec["v"] = tri.astype("<f4")
    with open(path, "wb") as f:
        f.write(head[:80].ljust(80, b" ")); f.write(np.uint32(len(tri)).tobytes()); f.write(rec.tobytes())


def smoothstep(r):
    t = np.clip((r - R1) / (R2 - R1), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blade_id(th, th0):
    d = (th[:, None] - th0[None, :] + np.pi) % (2 * np.pi) - np.pi
    return np.argmin(np.abs(d), axis=1)


def spindles(p):
    r = np.hypot(p[:, 1], p[:, 2]); th = np.arctan2(p[:, 2], p[:, 1])
    m = (r > 42e-3) & (r < 48e-3); thm = th[m]
    best, best_s = None, -1
    for off in np.linspace(-np.pi / NB, np.pi / NB, 145):
        c = off + np.arange(NB) * 2 * np.pi / NB
        s = np.sum(np.cos(thm[:, None] - c[None, :]) > np.cos(np.radians(20)))
        if s > best_s: best, best_s = c, s
    ids = blade_id(thm, best); out = []
    for b in range(NB):
        q = p[m][ids == b]; t = np.arctan2(q[:, 2], q[:, 1])
        out.append((float(q[:, 0].mean()), float(np.arctan2(np.sin(t).mean(), np.cos(t).mean()))))
    return out


def pitch_angle(p, R=0.0875, dr=1.5e-3):
    p = np.unique(np.round(p, 9), axis=0)
    r = np.hypot(p[:, 1], p[:, 2]); th = np.arctan2(p[:, 2], p[:, 1]); m = np.abs(r - R) < dr
    th0 = np.array([s[1] for s in spindles(p)]); ids = blade_id(th[m], th0); a = []
    for b in range(NB):
        q = p[m][ids == b]
        if len(q) < 10: continue
        s = R * ((np.arctan2(q[:, 2], q[:, 1]) - th0[b] + np.pi) % (2 * np.pi) - np.pi)
        pts = np.c_[s, q[:, 0]]
        d = np.linalg.norm(pts[:, None] - pts[None], axis=2); i, j = np.unravel_index(np.argmax(d), d.shape)
        v = pts[j] - pts[i]; a.append(np.degrees(np.arctan2(abs(v[1]), abs(v[0]))))
    return float(np.mean(a))


def rot(v, k, ang):
    c, s = np.cos(ang)[:, None], np.sin(ang)[:, None]
    return v * c + np.cross(k, v) * s + k * (v @ k)[:, None] * (1 - c)


def apply(p, dphi):
    r = np.hypot(p[:, 1], p[:, 2]); th = np.arctan2(p[:, 2], p[:, 1])
    sp = spindles(p); ids = blade_id(th, np.array([s[1] for s in sp])); w = smoothstep(r); out = p.copy()
    for b, (xs, tb) in enumerate(sp):
        sel = (ids == b) & (w > 0); k = np.array([0.0, np.cos(tb), np.sin(tb)]); o = np.array([xs, 0.0, 0.0])
        out[sel] = o + rot(p[sel] - o, k, np.radians(dphi) * w[sel])
    return out


if __name__ == "__main__":
    src, dst, dphi = sys.argv[1], sys.argv[2], float(sys.argv[3])
    head, p = read_stl(src)
    a0 = pitch_angle(p)
    q = apply(p, dphi)
    if dphi != 0 and np.sign(pitch_angle(q) - a0) != np.sign(dphi):
        q = apply(p, -dphi)          # orientation-independent sign: +dphi raises pitch
    a1 = pitch_angle(q)
    write_stl(dst, q)
    print(f"pitch {dphi:+.2f} deg: angle at r/R=0.7 {a0:.2f} -> {a1:.2f} deg (change {a1-a0:+.2f})")
