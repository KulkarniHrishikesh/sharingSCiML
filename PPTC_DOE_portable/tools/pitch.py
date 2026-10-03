"""Change PPTC blade pitch by rotating each blade about its spindle axis.

The surface is deformed in place (same triangles), so it stays watertight:
    point -> rotate about the blade's spindle axis by dphi * w(r)
with w(r) a smoothstep from 0 at R1 (top of the root fillets) to 1 at R2.
Hub, fillets and shaft (r < R1) are untouched.

Spindle axis of blade b: radial line through the propeller axis (x axis) at
the axial position and azimuth of the blade's root-section centroid
(r = 42..48 mm). Positive dphi increases the geometric pitch angle.

Usage: python pitch.py in.stl out.stl dphi_deg [scale_in_to_m]
"""
import sys
import numpy as np
import pyvista as pv

R1, R2 = 40.5e-3, 48.0e-3          # ramp limits [m]
NBLADE = 5


def smoothstep(r):
    t = np.clip((r - R1) / (R2 - R1), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def blade_id(theta, theta0):
    """Index of the nearest blade centre azimuth for each point."""
    d = (theta[:, None] - theta0[None, :] + np.pi) % (2 * np.pi) - np.pi
    return np.argmin(np.abs(d), axis=1)


def spindles(p):
    r = np.hypot(p[:, 1], p[:, 2])
    th = np.arctan2(p[:, 2], p[:, 1])
    m = (r > 42e-3) & (r < 48e-3)
    # cluster root points into 5 blades by azimuth
    h, e = np.histogram(th[m], bins=360, range=(-np.pi, np.pi))
    # coarse centres: 72-degree comb fitted to the histogram
    best, best_s = None, -1
    for off in np.linspace(-np.pi / NBLADE, np.pi / NBLADE, 145):
        c = off + np.arange(NBLADE) * 2 * np.pi / NBLADE
        s = np.sum(np.cos(th[m][:, None] - c[None, :]) > np.cos(np.radians(20)))
        if s > best_s:
            best, best_s = c, s
    ids = blade_id(th[m], best)
    out = []
    for b in range(NBLADE):
        q = p[m][ids == b]
        thb = np.arctan2(np.mean(np.sin(np.arctan2(q[:, 2], q[:, 1]))),
                         np.mean(np.cos(np.arctan2(q[:, 2], q[:, 1]))))
        out.append((float(np.mean(q[:, 0])), float(thb)))
    return out


def pitch_angle(p, R=0.0875, dr=1.5e-3):
    """Mean nose-tail pitch angle (deg) of the 5 blades at radius R."""
    r = np.hypot(p[:, 1], p[:, 2])
    th = np.arctan2(p[:, 2], p[:, 1])
    m = np.abs(r - R) < dr
    sp = spindles(p)
    th0 = np.array([s[1] for s in sp])
    ids = blade_id(th[m], th0)
    angs = []
    for b in range(NBLADE):
        q = p[m][ids == b]
        if len(q) < 10:
            continue
        s = R * ((np.arctan2(q[:, 2], q[:, 1]) - th0[b] + np.pi) % (2 * np.pi) - np.pi)
        x = q[:, 0]
        pts = np.c_[s, x]
        # nose-tail line = farthest pair
        d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
        i, j = np.unravel_index(np.argmax(d), d.shape)
        v = pts[j] - pts[i]
        angs.append(np.degrees(np.arctan2(abs(v[1]), abs(v[0]))))
    return float(np.mean(angs)), float(np.std(angs))


def rotate_about_axis(v, k, ang):
    """Rodrigues rotation of vectors v (N,3) about unit axis k by angles ang (N,)."""
    c, s = np.cos(ang)[:, None], np.sin(ang)[:, None]
    return v * c + np.cross(k, v) * s + k * (v @ k)[:, None] * (1 - c)


def apply(p, dphi_deg):
    r = np.hypot(p[:, 1], p[:, 2])
    th = np.arctan2(p[:, 2], p[:, 1])
    sp = spindles(p)
    th0 = np.array([s[1] for s in sp])
    ids = blade_id(th, th0)
    w = smoothstep(r)
    out = p.copy()
    for b, (xs, thb) in enumerate(sp):
        sel = (ids == b) & (w > 0)
        k = np.array([0.0, np.cos(thb), np.sin(thb)])      # spindle direction
        o = np.array([xs, 0.0, 0.0])                        # point on spindle
        out[sel] = o + rotate_about_axis(p[sel] - o, k, np.radians(dphi_deg) * w[sel])
    return out, sp


if __name__ == "__main__":
    src, dst, dphi = sys.argv[1], sys.argv[2], float(sys.argv[3])
    scale = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    s = pv.read(src)
    s.points = s.points * scale
    a0 = pitch_angle(s.points)
    newp, sp = apply(s.points, dphi)
    a1 = pitch_angle(newp)
    # choose rotation sign so that dphi > 0 increases pitch
    if dphi != 0 and np.sign(a1[0] - a0[0]) != np.sign(dphi):
        newp, sp = apply(s.points, -dphi)
        a1 = pitch_angle(newp)
    s.points = newp
    s.save(dst, binary=True)
    print(f"spindles (x mm, azimuth deg): {[(round(x*1e3,1), round(np.degrees(t),1)) for x,t in sp]}")
    print(f"pitch angle at r/R=0.7: before {a0[0]:.2f} (+-{a0[1]:.2f}) deg, after {a1[0]:.2f} (+-{a1[1]:.2f}) deg, change {a1[0]-a0[0]:+.2f} deg (target {dphi:+.2f})")
