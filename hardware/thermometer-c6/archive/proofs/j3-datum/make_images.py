#!/usr/bin/env python3
"""Proof images for the J3 datum question.

  1. datum-proof.png   the datasheet layout view with every measured datum
                       and the 5.79 / 4.18 arrow-tip terminations marked.
  2. side-by-side.png  datasheet land pattern vs our J3 footprint, both at
                       204 px/mm, aligned on PCB EDGE / Edge_Cuts.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCR = "out/j3-datum"            # raster_check.py output
OUT = "archive/proofs/j3-datum"
PX = 204.0                      # px per mm at 1200 dpi
EDGE_ROW = 2321.0               # PCB EDGE line in rc-1.png
CTR_COL = 1522.5                # connector centre column in rc-1.png


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            pass
    return ImageFont.load_default()


# ---- measured datasheet values, mm above the PCB EDGE line (vector method) --
DS = {
    "pad row far edge (north)": 7.4118,
    "pad row CENTRELINE": 6.8431,
    "pad row near edge (south)": 6.2745,
    "REAR slot centre": 6.2794,
    "NPTH post centre": 5.7794,
    "FRONT slot centre": 2.1078,
    "PCB EDGE": 0.0,
}
TIP = {                      # dimension arrow-tip terminations
    "1.64 top tip": 7.4118,
    "1.64 / 0.50 / 5.79 datum": 5.7745,
    "0.50 top tip / 4.18 top tip": 6.2745,
    "4.18 bottom tip": 2.0980,
    "5.79 bottom tip": 0.0000,
}

# ---- our board, mm from the north Edge_Cuts (y = -0.05) --------------------
BOARD_EDGE_Y = 0.000          # Edge_Cuts line CENTRELINE (bbox -0.05 is half the 0.1mm width)
OURS = {
    "front slot centre": 0.695,
    "NPTH centre": 4.345,
    "rear slot centre": 4.875,
    "pad row centre": 5.790,
}
SHIFT = 1.415                 # mm south, derived in VERDICT.md
PADS = [(20.15, .6), (20.95, .6), (21.65, .3), (22.15, .3), (22.65, .3),
        (23.15, .3), (23.65, .3), (24.15, .3), (24.65, .3), (25.15, .3),
        (25.85, .6), (26.65, .6)]


def image1():
    src = Image.open(f"{SCR}/rc-1.png").convert("RGB")
    x0, x1 = 260, 3760
    y0, y1 = 620, 2560
    im = src.crop((x0, y0, x1, y1))
    d = ImageDraw.Draw(im)
    f = font(34)
    fb = font(40)

    def row(v):
        return EDGE_ROW - v * PX - y0

    colours = {"PCB EDGE": (200, 0, 0), "FRONT slot centre": (0, 130, 220),
               "REAR slot centre": (0, 130, 220), "NPTH post centre": (0, 160, 60),
               "pad row CENTRELINE": (230, 120, 0)}
    lx = {"pad row far edge (north)": 14, "pad row CENTRELINE": 14,
          "pad row near edge (south)": 700, "REAR slot centre": 14,
          "NPTH post centre": 14, "FRONT slot centre": 14, "PCB EDGE": 14}
    for lab, v in DS.items():
        y = row(v)
        c = colours.get(lab, (150, 150, 150))
        w = 5 if lab == "PCB EDGE" else 3
        d.line([(0, y), (im.width, y)], fill=c, width=w)
        t = f"{lab}   {v:.4f} mm"
        x = lx.get(lab, 14)
        d.rectangle([(x - 6, y - 46), (x + 22 * len(t), y - 4)],
                    fill=(255, 255, 255))
        d.text((x, y - 44), t, fill=c, font=f)

    # arrow-tip callouts on the right dimension columns
    fx = font(30)
    for lab, v in TIP.items():
        y = row(v)
        d.ellipse([(3316 - x0 - 16, y - 16), (3316 - x0 + 16, y + 16)],
                  outline=(255, 0, 255), width=6)
        d.text((3316 - x0 + 26, y - 40), lab, fill=(255, 0, 255), font=fx)

    hdr = ("HRO TYPE-C-31-M-12  RECOMMEND P.C.B LAYOUT - measured datums "
           "(vector extraction, 12.24 pt/mm)")
    d.rectangle([(0, 0), (im.width, 58)], fill=(255, 255, 255))
    d.text((14, 10), hdr, fill=(0, 0, 0), font=fb)
    im.resize((im.width // 2, im.height // 2), Image.LANCZOS).save(
        f"{OUT}/datum-proof.png")
    print("wrote datum-proof.png")


def board_panel(W, TOP, Hp, shift):
    """Our J3 footprint drawn at 204 px/mm; `shift` mm added southward."""
    im = Image.new("RGB", (W, Hp), (255, 255, 255))
    dr = ImageDraw.Draw(im)

    def px(xmm, dmm):
        return (W / 2 + (xmm - 23.4) * PX, TOP * PX - dmm * PX)

    def rect(xc, d, w, h, **kw):
        dr.rectangle([px(xc - w / 2, d + h / 2), px(xc + w / 2, d - h / 2)], **kw)

    def slot(xc, d, w, h, dw, dh):
        rect(xc, d, w, h, fill=(255, 190, 60), outline=(120, 80, 0), width=4)
        rect(xc, d, dw, dh, fill=(255, 255, 255), outline=(120, 80, 0), width=3)

    for xc, w in PADS:
        rect(xc, 5.790 + shift, w, 1.45, fill=(220, 60, 60),
             outline=(120, 0, 0), width=3)
    for xc in (19.08, 27.72):
        slot(xc, 4.875 + shift, 1.00, 2.10, 0.6, 1.7)
        slot(xc, 0.695 + shift, 1.00, 1.60, 0.6, 1.2)
    for xc in (20.51, 26.29):
        dr.ellipse([px(xc - 0.325, 4.345 + shift + 0.325),
                    px(xc + 0.325, 4.345 + shift - 0.325)],
                   outline=(0, 0, 0), width=4)
    return im


def image2():
    """Datasheet | our board as placed | our board moved 1.365 mm south."""
    src = Image.open(f"{SCR}/rc-1.png").convert("RGB")
    W = 2320                       # 11.37 mm wide panel
    TOP, BOT = 8.6, 1.9
    Hp = int((TOP + BOT) * PX)
    sx0 = int(CTR_COL - W / 2)
    sy0 = int(EDGE_ROW - TOP * PX)
    panels = [src.crop((sx0, sy0, sx0 + W, sy0 + Hp)),
              board_panel(W, TOP, Hp, 0.0),
              board_panel(W, TOP, Hp, SHIFT)]
    titles = ["DATASHEET land pattern (real drawing)",
              "OUR BOARD - J3 as placed  (WRONG)",
              f"OUR BOARD - J3 moved +{SHIFT:.3f} mm south"]

    f, fb = font(34), font(46)
    gap = 60
    canvas = Image.new("RGB", (W * 3 + gap * 2, Hp + 150), (255, 255, 255))
    for i, p in enumerate(panels):
        canvas.paste(p, (i * (W + gap), 100))
    dc = ImageDraw.Draw(canvas)
    for lab, v, c in (("front slot centre  2.108", 2.1078, (0, 130, 220)),
                      ("NPTH centre  5.779", 5.7794, (0, 160, 60)),
                      ("rear slot centre  6.279", 6.2794, (0, 130, 220)),
                      ("pad row centre  6.843", 6.8431, (230, 120, 0))):
        y = 100 + (TOP - v) * PX
        dc.line([(0, y), (canvas.width, y)], fill=c, width=3)
        dc.rectangle([(4, y - 44), (4 + 21 * len(lab), y - 2)], fill=(255, 255, 255))
        dc.text((8, y - 42), lab, fill=c, font=f)
    y = 100 + TOP * PX
    dc.line([(0, y), (canvas.width, y)], fill=(200, 0, 0), width=8)
    dc.rectangle([(4, y + 8), (700, y + 52)], fill=(255, 255, 255))
    dc.text((8, y + 10), "PCB EDGE / Edge_Cuts", fill=(200, 0, 0), font=f)

    for i, t in enumerate(titles):
        dc.text((i * (W + gap) + 20, 24), t, fill=(0, 0, 0), font=fb)
    canvas.resize((canvas.width // 2, canvas.height // 2), Image.LANCZOS).save(
        f"{OUT}/side-by-side.png")
    print("wrote side-by-side.png")


if __name__ == "__main__":
    image1()
    image2()
