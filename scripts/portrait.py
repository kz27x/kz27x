#!/usr/bin/env python3
"""Converte assets/avatar.jpg em assets/portrait.json: o retrato desenhado em caracteres.
Contornos viram traços direcionais (| / - \\), cabelo e pele viram texturas de densidade.
Cada célula guarda (caractere, classe), para o painel pintar contorno e preenchimento em tons diferentes."""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLS = 72
import sys
MODE = sys.argv[1] if len(sys.argv) > 1 else "dark"  # dark: luz = denso; light: sombra = denso

im = Image.open(os.path.join(ROOT, "assets", "avatar.jpg")).convert("RGB")
im = im.crop((170, 150, 1900, 2048))
rgb = np.asarray(im).astype(float) / 255
lum = rgb @ [0.299, 0.587, 0.114]
bg = np.asarray(im.getpixel((5, 5))).astype(float) / 255
is_bg = np.abs(rgb - bg).sum(2) < 0.09

# contornos: o desenho tem linhas escuras finas; detecta pelo gradiente
sx, sy = ndimage.sobel(lum, 1), ndimage.sobel(lum, 0)
mag = np.hypot(sx, sy)
ang = (np.degrees(np.arctan2(sy, sx)) + 180) % 180  # direção do gradiente

H, W = lum.shape
cw = W / COLS
ch = cw * 1.65  # célula mais alta que larga (fonte mono ~0.6em)
ROWS = int(H / ch)

def cell(a, r, c):
    return a[int(r * ch):int((r + 1) * ch), int(c * cw):int((c + 1) * cw)]

RAMP = " .,:;irsXA253hMHGS#9B&@"  # do mais vazio ao mais denso
# tom de cada célula (fundo = 0); luz = densidade de caractere (o painel é escuro)
tone = np.zeros((ROWS, COLS)); edgec = [[None]*COLS for _ in range(ROWS)]
for r in range(ROWS):
    for c in range(COLS):
        b = cell(is_bg, r, c)
        if b.mean() > 0.9: tone[r, c] = -1; continue
        l = cell(lum, r, c)[~b]
        tone[r, c] = l.mean() ** 1.6 if MODE == 'dark' else (1 - l.mean()) ** 1.3 * 0.62
        m, a = cell(mag, r, c), cell(ang, r, c)
        strong = m > 1.6
        if strong.mean() > 0.10:
            th = np.degrees(np.arctan2(np.sin(np.radians(a[strong]*2)).mean(),
                                       np.cos(np.radians(a[strong]*2)).mean()))/2 % 180
            e = (th + 90) % 180
            edgec[r][c] = "-" if e < 22 or e >= 158 else "\\" if e < 68 else "|" if e < 112 else "/"
# pontilhado com ruído (sem padrão repetido): cada célula sorteia entre os dois caracteres vizinhos do tom
rng = np.random.default_rng(27); n = len(RAMP) - 1
grid = []
for r in range(ROWS):
    row = []
    for c in range(COLS):
        if tone[r, c] < 0: row.append([" ", 0]); continue
        if edgec[r][c]: row.append([edgec[r][c], 3]); continue
        v = min(max(tone[r, c] + rng.normal(0, 0.07), 0), 1) * n
        k = int(v) + (1 if rng.random() < v - int(v) else 0)
        row.append([RAMP[min(k, n)], 2 if k / n > 0.45 else 1])
    grid.append(row)

# corta linhas vazias nas pontas
while grid and all(x[0] == " " for x in grid[0]): grid.pop(0)
while grid and all(x[0] == " " for x in grid[-1]): grid.pop()
json.dump(grid, open(os.path.join(ROOT, "assets", f"portrait-{MODE}.json"), "w"))
print(len(grid), "linhas")
print("\n".join("".join(x[0] for x in r) for r in grid))
