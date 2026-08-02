#!/usr/bin/env python3
"""SUB article-page generator. Two layouts:
   layout='photo-left'  -> photo left half, Space Mono text right (black)
   layout='text-top'    -> Space Mono text top (black), photo fills the bottom
"""
from PIL import Image, ImageDraw, ImageFont
import os
WHITE=(255,255,255); BLACK=(0,0,0)
FONT_CANDIDATES=["SpaceMono-Regular.ttf",
    "/sessions/eloquent-dreamy-thompson/mnt/outputs/SpaceMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
def _font_path():
    for p in FONT_CANDIDATES:
        if os.path.exists(p): return p
    raise FileNotFoundError("no font")
def _fit(img,w,h):
    iw,ih=img.size; s=max(w/iw,h/ih); nw,nh=int(iw*s+.5),int(ih*s+.5)
    img=img.resize((nw,nh),Image.LANCZOS); l,t=(nw-w)//2,(nh-h)//2
    return img.crop((l,t,l+w,t+h))
def _wrap(words,cpl):
    lines,cur=[],""
    for wd in words:
        test=wd if not cur else cur+" "+wd
        if len(test)>cpl and cur: lines.append(cur); cur=wd
        else: cur=test
    if cur: lines.append(cur)
    return lines
def _layout_lines(draw,fpath,fs,paras,avail_w):
    font=ImageFont.truetype(fpath,fs); cw=draw.textlength("M",font=font)
    cpl=max(4,int(avail_w/cw)); lines=[]
    for i,p in enumerate(paras):
        lines+=_wrap(p.split(),cpl)
        if i<len(paras)-1: lines.append("")
    return font,lines

def make_article(bg_path, body, out_path, size=(2080,2600),
                 layout="photo-left", split=0.5, line_spacing=1.4, max_fs=None):
    # Fill-to-fit: text grows to fill the available height, capped by max_fs.
    # Long articles naturally shrink to stay dense; short blurbs grow to fill
    # the text half instead of leaving dead space.
    if max_fs is None:
        max_fs = 72 if layout=="text-top" else 74
    W,H=size; canvas=Image.new("RGB",(W,H),BLACK); draw=ImageDraw.Draw(canvas)
    fpath=_font_path()
    paras=[p.strip() for p in body.upper().split("\n\n") if p.strip()]

    if layout=="photo-left":
        pw=int(W*split)
        canvas.paste(_fit(Image.open(bg_path).convert("RGB"),pw,H),(0,0))
        tx0=pw; pad_x=int(W*.028); pad_y=int(H*.03)
        avail_w=W-tx0-2*pad_x; avail_h=H-2*pad_y; tx=tx0+pad_x; ty=pad_y
    else:  # text-top
        pad_x=int(W*.03); pad_y=int(H*.02)
        text_h=int(H*split)
        avail_w=W-2*pad_x; avail_h=text_h-pad_y; tx=pad_x; ty=pad_y

    fs=max_fs
    while fs>16:
        font,lines=_layout_lines(draw,fpath,fs,paras,avail_w)
        if len(lines)*fs*line_spacing<=avail_h: break
        fs-=2

    if layout=="text-top":
        photo_y=int(H*split); ph=H-photo_y
        canvas.paste(_fit(Image.open(bg_path).convert("RGB"),W,ph),(0,photo_y))

    y=ty
    for ln in lines:
        if ln: draw.text((tx,y),ln,font=font,fill=WHITE)
        y+=fs*line_spacing
    canvas.save(out_path,quality=95)
    print("saved",out_path,"|",layout,"| font_px",fs,"| lines",len(lines))

if __name__=="__main__":
    body=open("_stack_body.txt").read()
    make_article("_leftphoto.jpg", body, "article_stack_test.png",
                 layout="text-top", split=0.47)
