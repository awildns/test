#!/usr/bin/env python3
"""SUB cover generator (Route A)."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

SUB_RED = (158, 55, 56)   # #9e3738
WHITE   = (255, 255, 255)

FONT_CANDIDATES = [
    "BebasNeue-Regular.ttf",
    "/sessions/eloquent-dreamy-thompson/mnt/outputs/BebasNeue-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
def _font_path():
    for p in FONT_CANDIDATES:
        if os.path.exists(p): return p
    raise FileNotFoundError("no font")

def _cover_fit(img, size):
    tw, th = size; iw, ih = img.size
    s = max(tw/iw, th/ih); nw, nh = int(iw*s+.5), int(ih*s+.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    l, t = (nw-tw)//2, (nh-th)//2
    return img.crop((l, t, l+tw, t+th))

def _bottom_gradient(size, height_frac=0.40, max_alpha=120):
    w, h = size; g = Image.new("L", (1, h), 0)
    start = int(h*(1-height_frac))
    for y in range(start, h):
        t = (y-start)/max(1, h-start); g.putpixel((0, y), int(max_alpha*(t**1.5)))
    g = g.resize((w, h)); blk = Image.new("RGBA", (w, h), (0, 0, 0, 255)); blk.putalpha(g)
    return blk

def _measure(d, w, f, tr): b = d.textbbox((0,0), w, font=f); return (b[2]-b[0]) + tr*max(0, len(w)-1)

def _wrap(d, words, f, max_w, tr, sw):
    lines, cur, cw = [], [], 0
    for wd in words:
        ww = _measure(d, wd, f, tr); add = ww if not cur else sw+ww
        if cur and cw+add > max_w: lines.append(cur); cur, cw = [wd], ww
        else: cur.append(wd); cw += add
    if cur: lines.append(cur)
    return lines

def make_cover(bg_path, title, red_words, out_path, logo_path="sub-logo-overlay.png",
               size=(2080, 2600), scrim_alpha=60, title_px=133,
               overlay_path="overlay.png", logo_glow=True):
    W, H = size
    canvas = _cover_fit(Image.open(bg_path).convert("RGB"), size).convert("RGBA")

    # --- darkening layer between photo and text ---
    if overlay_path and os.path.exists(overlay_path):
        ov = Image.open(overlay_path).convert("RGBA").resize((W, H), Image.LANCZOS)
        canvas.alpha_composite(ov)
    else:
        canvas.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, scrim_alpha)))  # full-frame scrim
        canvas.alpha_composite(_bottom_gradient(size))                             # + soft bottom

    draw = ImageDraw.Draw(canvas)
    fpath = _font_path()
    _PUNCT = "?!.,\"'“”‘’"
    red_set = {w.upper().strip(_PUNCT) for w in red_words}
    words = title.upper().split()
    max_w = int(W*0.86); tracking = max(1, W//900)

    fs = title_px                       # ~32pt @300ppi = 133px
    while fs > 20:                      # only shrink if it would overflow width
        font = ImageFont.truetype(fpath, fs)
        sw = draw.textbbox((0,0), " ", font=font)[2]
        lines = _wrap(draw, words, font, max_w, tracking, sw)
        widest = max(sum(_measure(draw, w, font, tracking) for w in ln)+sw*(len(ln)-1) for ln in lines)
        if widest <= max_w: break
        fs -= 3

    line_h = int(fs*1.06); y = H - int(H*0.05) - line_h*len(lines)
    for ln in lines:
        lw = sum(_measure(draw, w, font, tracking) for w in ln)+sw*(len(ln)-1)
        x = (W-lw)//2
        for wd in ln:
            col = SUB_RED if wd.strip(_PUNCT).upper() in red_set else WHITE
            for ch in wd:
                draw.text((x, y), ch, font=font, fill=col)      # NO glow on text
                x += draw.textbbox((0,0), ch, font=font)[2] + tracking
            x += sw
        y += line_h

    # --- logo ---
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        # full-canvas logo overlay (pre-positioned, own glow): composite as-is
        if abs(logo.width/logo.height - W/H) < 0.05 and logo.width > W*0.6:
            canvas.alpha_composite(logo.resize((W, H), Image.LANCZOS))
            canvas.convert("RGB").save(out_path, quality=95)
            print("saved", out_path, "| title_px", fs, "| lines", len(lines), "| overlay-logo")
            return
        tw = int(W*0.26); logo = logo.resize((tw, int(logo.height*(tw/logo.width))), Image.LANCZOS)
        lx, ly = (W-tw)//2, int(H*0.03)
        if logo_glow:
            pad = int(logo.height*0.6)
            g = Image.new("RGBA", (logo.width+2*pad, logo.height+2*pad), (0,0,0,0))
            sil = Image.new("RGBA", logo.size, (0,0,0,0)); sil.putalpha(logo.getchannel("A"))
            g.paste(sil, (pad, pad), sil)
            g = g.filter(ImageFilter.GaussianBlur(pad*0.35))
            ga = g.getchannel("A").point(lambda p: int(p*0.9))
            g.putalpha(ga)
            canvas.alpha_composite(g, (lx-pad, ly-pad))
        canvas.alpha_composite(logo, (lx, ly))

    canvas.convert("RGB").save(out_path, quality=95)
    print("saved", out_path, "| title_px", fs, "| lines", len(lines))

if __name__ == "__main__":
    make_cover("tr.jpg", "How does Lewisham have so much musical tallent?",
               ["lewisham","tallent"], "cover_test.png",
               logo_path="sub-logo-overlay.png", size=(2080,2600))
