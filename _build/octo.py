"""The octopus mark: a soft dome and eight tapered arms that curl outward.
One head sets the intent; eight arms work on their own. Geometry is generated so the hero can animate each arm."""
import math

HEAD = ("M50 14C60 14 66.5 22.5 66.5 33C66.5 40 64 45.2 60 48.6C57.4 50.8 54 51.8 50 51.8"
        "C46 51.8 42.6 50.8 40 48.6C36 45.2 33.5 40 33.5 33C33.5 22.5 40 14 50 14Z")

# (spread: -1 far left .. 1 far right, length, total curl in degrees, root x)
ARMS = [(-1.00, 44, 230, 38.5), (-0.70, 42, 185, 41.5), (-0.42, 38, 135, 44.8), (-0.14, 34, 90, 48.4),
        (0.14, 34, -90, 51.6), (0.42, 38, -135, 55.2), (0.70, 42, -185, 58.5), (1.00, 44, -230, 61.5)]
EYES = ((45, 35), (55, 35))


def _outline(root, heading0, length, turn, w0, w1, steps=20):
    x, y = root
    pts = [(x, y, math.radians(heading0))]
    for i in range(1, steps + 1):
        th = math.radians(heading0) + math.radians(turn) * ((i / steps) ** 2.2)
        x += math.cos(th) * length / steps
        y += math.sin(th) * length / steps
        pts.append((x, y, th))
    left, right = [], []
    for i, (px, py, a) in enumerate(pts):
        w = (w0 + (w1 - w0) * ((i / steps) ** 0.8)) / 2
        nx, ny = -math.sin(a), math.cos(a)
        left.append((px + nx * w, py + ny * w))
        right.append((px - nx * w, py - ny * w))
    tx, ty, ta = pts[-1]
    return left + [(tx + math.cos(ta) * w1 / 2, ty + math.sin(ta) * w1 / 2)] + right[::-1]


def _smooth(poly):
    n = len(poly)
    d = f"M{poly[0][0]:.1f} {poly[0][1]:.1f}"
    for i in range(n):
        p0, p1, p2, p3 = poly[i - 1], poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + "Z"


def arms(width=1.0):
    out = []
    for s, length, turn, rx in ARMS:
        root = (rx, 46.5 + (1 - abs(s)) * 3.2)
        out.append((root, _smooth(_outline(root, 90 - s * 78, length, turn, 3.9 * width, 0.8 * width))))
    return out


def mark(width=1.0, eye_r=2.2):
    """Static mark: fill follows currentColor; the eyes take --octo-eye (the page background)."""
    body = "".join(f'<path d="{d}"/>' for _, d in arms(width)) + f'<path d="{HEAD}"/>'
    eyes = "".join(f'<circle cx="{x}" cy="{y}" r="{eye_r}" fill="var(--octo-eye,#fff)"/>' for x, y in EYES)
    return body + eyes


def hero():
    """Animated mark: every arm is its own group (sways from its root); the pupils follow the cursor."""
    out = []
    for i, (root, d) in enumerate(arms()):
        out.append(f'<g class="arm" style="--i:{i};transform-origin:{root[0]:.1f}px {root[1]:.1f}px"><path d="{d}"/></g>')
    out.append(f'<path class="head" d="{HEAD}"/>')
    out.append('<g class="eyes">' + "".join(
        f'<g class="eye"><circle class="white" cx="{x}" cy="{y}" r="2.9"/><circle class="pupil" cx="{x}" cy="{y + .3}" r="1.45"/></g>'
        for x, y in EYES) + "</g>")
    return "".join(out)


def favicon():
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="24" fill="#0b0b0b"/>'
            f'<g fill="#fff" transform="translate(3 0) scale(.94)">'
            + "".join(f'<path d="{d}"/>' for _, d in arms(1.55)) + f'<path d="{HEAD}"/></g>'
            + "".join(f'<circle cx="{x * .94 + 3:.1f}" cy="{y * .94:.1f}" r="2.9" fill="#0b0b0b"/>' for x, y in EYES)
            + "</svg>")
