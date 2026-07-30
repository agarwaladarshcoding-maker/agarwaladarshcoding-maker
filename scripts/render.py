#!/usr/bin/env python3
"""Render the bespoke SVG assets used by the profile README.

No third-party dependencies on purpose: this runs in CI every day and a
dependency resolution failure would silently rot the profile.

Reads data/status.json (written by verify.py) and writes light/dark pairs of:
  assets/header-{theme}.svg    identity + animated retrieve/verify loop
  assets/stack-{theme}.svg     stack panel + real language distribution
  assets/verified-{theme}.svg  live self-verification strip
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / "status.json"

THEMES = {
    "dark": dict(
        bg1="#0b0f14", bg2="#0d1522", panel="#111a26", stroke="#1e2c3d",
        text="#e6edf3", muted="#8b98a5", faint="#5a6874",
        accent="#3ddc97", accent2="#58a6ff", bad="#f85149", dot="#243244",
    ),
    "light": dict(
        bg1="#ffffff", bg2="#f5f8fa", panel="#ffffff", stroke="#d4dbe2",
        text="#1f2328", muted="#59636e", faint="#8b949e",
        accent="#0f7d59", accent2="#0969da", bad="#cf222e", dot="#e4eaf0",
    ),
}

MONO = "ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,monospace"
SANS = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"

# SVG collapses ordinary runs of whitespace, which closes up the padding around
# separators. Non-breaking spaces survive.
NB = "&#160;"

# Phrases for the typing line in the header.
PHRASES = [
    "retrieval systems that verify their own answers",
    "claim-level hallucination detection",
    "PyTorch · RAG · agents · C++ fast paths",
]

STACK = [
    ("AI / ML", [
        "PyTorch", "Transformers / HF", "RAG & retrieval",
        "LoRA fine-tuning", "scikit-learn", "OpenCV",
    ]),
    ("QUANT / SYSTEMS", [
        "C++17 / 20", "NumPy / Pandas", "Monte Carlo",
        "Limit order books", "Statistical arbitrage", "PCA factor models",
    ]),
    ("WEB / INFRA", [
        "TypeScript", "React / Next.js", "Node / Express",
        "MongoDB", "Tailwind CSS", "GitHub Actions",
    ]),
]


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def mono_w(text, size):
    """Advance width of monospace text. SFMono/Menlo are 0.6em per char."""
    return len(text) * size * 0.6


def load_status():
    if DATA.exists():
        return json.loads(DATA.read_text())
    return {
        "checks": {"passed": 0, "total": 0},
        "groups": [], "generated": "never", "ok": False, "languages": [],
    }


# ─────────────────────────────────────────────────────────────── header ────

def header(t):
    """Identity block plus an animated retrieve → draft → split → verify loop.

    The loop is not decoration: it is the architecture of the Medical RAG
    project, which splits its own draft into claims and re-checks each one.
    """
    W, H = 1200, 300
    n = len(PHRASES)
    span = 4.5                      # seconds each phrase is on screen
    T = span * n                    # full cycle
    type_dur = 1.5                  # seconds spent typing a phrase

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" fill="none" role="img" '
        f'aria-label="Adarsh Agarwala — AI/ML engineer, retrieval and agent systems">',
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg1"]}"/>'
        f'<stop offset="1" stop-color="{t["bg2"]}"/></linearGradient>',
        f'<pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.5" cy="1.5" r="1.5" fill="{t["dot"]}"/></pattern>',
        f'<linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{t["accent"]}"/>'
        f'<stop offset="1" stop-color="{t["accent2"]}"/></linearGradient>',
        f'<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,1 L9,5 L0,9 z" fill="{t["faint"]}"/></marker>',
        f'<marker id="arA" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
        f'<path d="M0,1 L9,5 L0,9 z" fill="{t["accent"]}"/></marker>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>',
        f'<rect width="{W}" height="{H}" rx="14" fill="url(#grid)" opacity="0.55"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" '
        f'stroke="{t["stroke"]}"/>',
    ]

    # ── left: identity ──
    out += [
        f'<text x="52" y="54" xml:space="preserve" font-family="{MONO}" '
        f'font-size="12.5" letter-spacing="3.4" fill="{t["accent"]}">AI / ML'
        f'<tspan fill="{t["faint"]}">{NB}·{NB}</tspan>'
        f'<tspan fill="{t["accent2"]}">QUANTITATIVE SYSTEMS</tspan></text>',

        f'<text x="52" y="100" font-family="{SANS}" font-size="40" '
        f'font-weight="700" letter-spacing="0.6" fill="{t["text"]}">'
        f'Adarsh Agarwala</text>',

        # width is set statically as well as animated: a renderer that ignores
        # SMIL (or samples the document at t=0) must still show the finished art
        f'<rect x="52" y="117" width="72" height="3" rx="1.5" fill="url(#rule)">'
        f'<animate attributeName="width" dur="0.9s" '
        f'begin="0s" fill="freeze" calcMode="spline" '
        f'keySplines="0.2 0.8 0.2 1" keyTimes="0;1" values="0;72"/></rect>',

        f'<text x="52" y="153" font-family="{SANS}" font-size="17" '
        f'fill="{t["muted"]}">AI/ML engineer · retrieval, RAG and agent systems'
        f'</text>',
    ]

    # ── typing line ──
    tx, ty, fs = 52, 197, 16.5
    out.append(
        f'<text x="{tx}" y="{ty}" font-family="{MONO}" font-size="{fs}" '
        f'fill="{t["accent"]}">▸</text>'
    )
    body_x = tx + 22
    for i, phrase in enumerate(PHRASES):
        start, end = i * span, (i + 1) * span
        w = mono_w(phrase, fs)
        # opacity: hard on at start, hard off at end of this phrase's window
        eps = 0.004
        kt = [0.0, max(start / T - eps, 0.0), start / T,
              end / T - eps, min(end / T, 1.0), 1.0]
        ov = [0, 0, 1, 1, 0, 0]
        if i == 0:                       # first phrase owns t=0
            kt, ov = [0.0, (end / T) - eps, end / T, 1.0], [1, 1, 0, 0]
        kts = ";".join(f"{v:.5f}" for v in kt)
        ovs = ";".join(str(v) for v in ov)

        # clip width: 0 → full over type_dur inside the window
        ck = [0.0, start / T, (start + type_dur) / T, 1.0]
        cv = [0, 0, w, w]
        if i == 0:
            ck, cv = [0.0, type_dur / T, 1.0], [0, w, w]
        cks = ";".join(f"{v:.5f}" for v in ck)
        cvs = ";".join(f"{v:.1f}" for v in cv)

        caret_xs = ";".join(f"{body_x + float(v):.1f}" for v in cvs.split(";"))
        out += [
            # static width = full phrase, so a non-animating renderer shows the
            # line typed out rather than an empty gap
            f'<clipPath id="cp{i}"><rect x="{body_x}" y="{ty-fs}" '
            f'height="{fs*1.5:.0f}" width="{w:.1f}">'
            f'<animate attributeName="width" values="{cvs}" '
            f'keyTimes="{cks}" dur="{T}s" repeatCount="indefinite" '
            f'calcMode="linear"/></rect></clipPath>',

            f'<g opacity="{1 if i == 0 else 0}">'
            f'<animate attributeName="opacity" values="{ovs}" '
            f'keyTimes="{kts}" dur="{T}s" repeatCount="indefinite" '
            f'calcMode="discrete"/>'
            f'<text x="{body_x}" y="{ty}" font-family="{MONO}" '
            f'font-size="{fs}" fill="{t["text"]}" clip-path="url(#cp{i})">'
            f'{esc(phrase)}</text>'
            # caret rides the end of the typed text, blinking on its own clock
            f'<rect x="{body_x + w:.1f}" y="{ty-fs+2.5}" width="9" '
            f'height="{fs+1}" fill="{t["accent"]}" opacity="0.9">'
            f'<animate attributeName="x" values="{caret_xs}" '
            f'keyTimes="{cks}" dur="{T}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="0.9;0.9;0;0" '
            f'keyTimes="0;0.5;0.51;1" dur="1.1s" repeatCount="indefinite" '
            f'calcMode="discrete"/></rect>'
            f'</g>',
        ]

    out.append(
        f'<text x="52" y="240" xml:space="preserve" font-family="{MONO}" '
        f'font-size="13" fill="{t["faint"]}">B.Tech CSE, IIIT Pune ’29'
        f'<tspan fill="{t["muted"]}">{NB}{NB}·{NB}{NB}</tspan>CGPA 9.38/10'
        f'<tspan fill="{t["muted"]}">{NB}{NB}·{NB}{NB}</tspan>India</text>'
    )

    # ── right: the self-checking loop ──
    nodes = [
        ("RETRIEVE", 820, 105, 118),
        ("DRAFT", 980, 105, 92),
        ("SPLIT CLAIMS", 980, 195, 136),
        ("VERIFY", 800, 195, 104),
    ]
    for label, cx, cy, w in nodes:
        hot = label == "VERIFY"
        col = t["accent"] if hot else t["stroke"]
        out.append(
            f'<g><rect x="{cx-w/2:.0f}" y="{cy-18}" width="{w}" height="36" '
            f'rx="8" fill="{t["panel"]}" stroke="{col}" '
            f'stroke-width="{1.6 if hot else 1}"/>'
            + (f'<rect x="{cx-w/2:.0f}" y="{cy-18}" width="{w}" height="36" '
               f'rx="8" fill="{t["accent"]}" opacity="0">'
               f'<animate attributeName="opacity" values="0;0.16;0" '
               f'keyTimes="0;0.5;1" dur="2.6s" begin="1.5s" '
               f'repeatCount="indefinite"/></rect>' if hot else "")
            + f'<text x="{cx}" y="{cy+4.5}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="11.5" letter-spacing="0.9" '
            f'fill="{t["accent"] if hot else t["muted"]}">{label}</text></g>'
        )

    out += [
        f'<path d="M761 105 L828 105" stroke="{t["faint"]}" '
        f'marker-end="url(#ar)"/>',
        f'<path d="M1026 105 L1062 105 L1062 195 L1056 195" '
        f'stroke="{t["faint"]}" marker-end="url(#ar)" fill="none"/>',
        f'<path d="M912 195 L860 195" stroke="{t["faint"]}" '
        f'marker-end="url(#ar)"/>',
        # the re-check return edge, drawn in accent because it is the point
        f'<path d="M748 195 L714 195 L714 105 L755 105" stroke="{t["accent"]}" '
        f'stroke-dasharray="4 3" marker-end="url(#arA)" fill="none" '
        f'opacity="0.85"/>',
        f'<text x="707" y="152" text-anchor="middle" font-family="{MONO}" '
        f'font-size="10.5" fill="{t["accent"]}" letter-spacing="0.6" '
        f'transform="rotate(-90 707 152)">re-check</text>',
    ]

    # travelling pulse around the loop
    loop = ("M820 105 L980 105 L1062 105 L1062 195 L980 195 L800 195 "
            "L714 195 L714 105 Z")
    out.append(
        f'<circle r="4.5" fill="{t["accent"]}">'
        f'<animateMotion dur="6s" repeatCount="indefinite" '
        f'path="{loop}" rotate="auto"/>'
        f'<animate attributeName="opacity" values="0.25;1;1;0.25" '
        f'keyTimes="0;0.15;0.85;1" dur="6s" repeatCount="indefinite"/>'
        f'</circle>'
    )

    out.append(
        f'<text x="888" y="252" text-anchor="middle" font-family="{MONO}" '
        f'font-size="11" letter-spacing="1.6" fill="{t["faint"]}">'
        f'EVERY ANSWER CHECKED AGAINST ITS SOURCES</text>'
    )
    out.append("</svg>")
    return "\n".join(out)


# ──────────────────────────────────────────────────────────────── stack ────

def stack(t, langs):
    # Languages under 1% are noise from a stray config file, not a skill claim.
    langs = [(n, p) for n, p in langs if p >= 1.0]
    W, H = 1200, 356
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" fill="none" role="img" aria-label="Tech stack">',
        "<defs>",
        f'<linearGradient id="sbg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{t["bg1"]}"/>'
        f'<stop offset="1" stop-color="{t["bg2"]}"/></linearGradient>',
        "</defs>",
        f'<rect width="{W}" height="{H}" rx="14" fill="url(#sbg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" '
        f'stroke="{t["stroke"]}"/>',
        f'<text x="44" y="46" font-family="{MONO}" font-size="12.5" '
        f'letter-spacing="3.4" fill="{t["accent"]}">STACK</text>',
    ]

    col_x = [44, 448, 836]
    for ci, (title, items) in enumerate(STACK):
        x = col_x[ci]
        out.append(
            f'<text x="{x}" y="86" font-family="{MONO}" font-size="12" '
            f'letter-spacing="1.6" fill="{t["text"]}">{esc(title)}</text>'
        )
        out.append(
            f'<rect x="{x}" y="96" width="30" height="2" rx="1" '
            f'fill="{t["accent2"]}"/>'
        )
        for ii, item in enumerate(items):
            y = 124 + ii * 24
            out += [
                f'<circle cx="{x+4}" cy="{y-4}" r="2.5" fill="{t["accent"]}" '
                f'opacity="0.75"/>',
                f'<text x="{x+18}" y="{y}" font-family="{SANS}" '
                f'font-size="14.5" fill="{t["muted"]}">{esc(item)}</text>',
            ]

    # real language distribution, stacked bar across the bottom
    if langs:
        bx, by, bw, bh = 44, 298, W - 88, 12
        palette = [t["accent"], t["accent2"], "#a371f7", "#f0883e",
                   "#e3b341", "#79c0ff", "#7ee787"]
        out.append(
            f'<text x="{bx}" y="{by-12}" font-family="{MONO}" font-size="10.5" '
            f'letter-spacing="1.5" fill="{t["faint"]}">'
            f'LANGUAGE DISTRIBUTION — MEASURED FROM PUBLIC REPOS</text>'
        )
        cx = bx
        for i, (name, pct) in enumerate(langs[:7]):
            seg = bw * pct / 100.0
            first, last = i == 0, i == len(langs[:7]) - 1
            out.append(
                f'<rect x="{cx:.1f}" y="{by}" width="{max(seg,1):.1f}" '
                f'height="{bh}" fill="{palette[i % len(palette)]}" '
                f'opacity="0.9" rx="{6 if (first or last) else 0}">'
                f'<animate attributeName="height" values="0;{bh}" '
                f'dur="0.7s" begin="{0.08*i:.2f}s" fill="freeze"/>'
                f'<animate attributeName="y" values="{by+bh};{by}" '
                f'dur="0.7s" begin="{0.08*i:.2f}s" fill="freeze"/></rect>'
            )
            cx += seg
        # legend
        lx = bx
        for i, (name, pct) in enumerate(langs[:7]):
            out += [
                f'<rect x="{lx}" y="{by+26}" width="9" height="9" rx="2" '
                f'fill="{palette[i % len(palette)]}"/>',
                f'<text x="{lx+15}" y="{by+34.5}" font-family="{MONO}" '
                f'font-size="11" fill="{t["muted"]}">{esc(name)} '
                f'<tspan fill="{t["faint"]}">{pct:.0f}%</tspan></text>',
            ]
            lx += 34 + mono_w(f"{name} {pct:.0f}%", 11)
    out.append("</svg>")
    return "\n".join(out)


# ───────────────────────────────────────────────────────────── verified ────

def verified(t, st):
    W, H = 1200, 66
    ok = st.get("ok", False)
    passed = st["checks"]["passed"]
    total = st["checks"]["total"]
    col = t["accent"] if ok else t["bad"]
    verdict = "ALL CHECKS PASSING" if ok else "CHECKS FAILING"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" fill="none" role="img" '
        f'aria-label="Self-verification: {passed} of {total} checks passing">',
        f'<rect width="{W}" height="{H}" rx="12" fill="{t["panel"]}"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" '
        f'stroke="{col}" opacity="0.45"/>',
        # pulsing status dot
        f'<circle cx="34" cy="33" r="5.5" fill="{col}"/>',
        f'<circle cx="34" cy="33" r="5.5" fill="{col}" opacity="0.6">'
        f'<animate attributeName="r" values="5.5;14" dur="2.4s" '
        f'repeatCount="indefinite"/>'
        f'<animate attributeName="opacity" values="0.6;0" dur="2.4s" '
        f'repeatCount="indefinite"/></circle>',
        f'<text x="56" y="29" font-family="{MONO}" font-size="12.5" '
        f'letter-spacing="2.2" fill="{col}">SELF-VERIFIED</text>',
        f'<text x="56" y="47" font-family="{MONO}" font-size="11.5" '
        f'fill="{t["faint"]}">this README re-checks its own claims daily '
        f'in CI</text>',
        f'<text x="{W-32}" y="29" text-anchor="end" font-family="{MONO}" '
        f'font-size="15" fill="{t["text"]}">{passed}/{total} '
        f'<tspan font-size="12" fill="{col}">{verdict}</tspan></text>',
    ]

    # literal U+00A0, not the entity: this string is run through esc() below,
    # which would turn "&#160;" into "&amp;#160;"
    parts = " · ".join(
        f'{g["name"]} {g["passed"]}/{g["total"]}' for g in st.get("groups", [])
    )
    stamp = st.get("generated", "never")
    out.append(
        f'<text x="{W-32}" y="47" text-anchor="end" font-family="{MONO}" '
        f'font-size="11.5" fill="{t["faint"]}">{esc(parts)}'
        + (f'<tspan fill="{t["muted"]}">  ·  </tspan>{esc(stamp)}'
           if parts else esc(stamp))
        + "</text>"
    )
    out.append("</svg>")
    return "\n".join(out)


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    st = load_status()
    langs = [(l["name"], l["pct"]) for l in st.get("languages", [])]
    for name, theme in THEMES.items():
        (ASSETS / f"header-{name}.svg").write_text(header(theme))
        (ASSETS / f"stack-{name}.svg").write_text(stack(theme, langs))
        (ASSETS / f"verified-{name}.svg").write_text(verified(theme, st))
    print(f"rendered 6 assets · {st['checks']['passed']}/{st['checks']['total']} "
          f"checks · {len(langs)} languages")


if __name__ == "__main__":
    main()
