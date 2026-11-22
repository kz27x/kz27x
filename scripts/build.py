#!/usr/bin/env python3
"""Gera os SVGs do perfil kz27x na identidade Alumínio da Zarpa (tema escuro e claro).
   assets/header-{dark,light}.svg   cabeçalho
   assets/painel-{dark,light}.svg   retrato em caracteres + números do GitHub
   assets/btn-*.svg                 botões
Sem GITHUB_TOKEN usa dados de exemplo, só para testar o visual."""
import json, os, random, urllib.request, html
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = lambda *p: os.path.join(ROOT, "assets", *p)
USER = os.environ.get("GH_USER", "kz27x")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
e = lambda s: html.escape(str(s))

THEMES = {
    "dark": dict(bg="#050506", surf="#0E0E10", line="#1C1C1E", line2="#2C2C2E", text="#F5F5F7",
                 dim="#8E8E93", faint="#48484A", blob="#3A3A3C", blob2="#1C1C1E",
                 alu=["#8E8E93", "#F5F5F7", "#A1A1A6", "#E8E8ED", "#8E8E93"],
                 heat=["#1F1F22", "#3A3A3C", "#636366", "#AEAEB2", "#F5F5F7"],
                 ink={1: "#5A5A5E", 2: "#C7C7CC", 3: "#FFFFFF"}, grain=0.07),
    "light": dict(bg="#ECECEF", surf="#F5F5F7", line="#D9D9DE", line2="#C7C7CC", text="#1D1D1F",
                  dim="#6E6E73", faint="#AEAEB2", blob="#FFFFFF", blob2="#D2D2D7",
                  alu=["#3A3A3C", "#8E8E93", "#1D1D1F", "#636366", "#3A3A3C"],
                  heat=["#E0E0E5", "#C7C7CC", "#8E8E93", "#48484A", "#1D1D1F"],
                  ink={1: "#AEAEB2", 2: "#48484A", 3: "#000000"}, grain=0.05),
}


def fontcss(*names):
    fam = {"sans": "ZSans", "sanslight": "ZSansL", "serif": "ZSerif", "mono": "ZMono"}
    css = "".join(f"@font-face{{font-family:{fam[n]};src:url(data:font/woff;base64,"
                  f"{open(A('fonts', n + '.b64')).read().strip()}) format('woff')}}" for n in names)
    return (css + ".s{font-family:ZSans,'Inter','Helvetica Neue',sans-serif}"
            ".sl{font-family:ZSansL,'Inter','Helvetica Neue',sans-serif}"
            ".i{font-family:ZSerif,Georgia,serif;font-style:italic}"
            ".m{font-family:ZMono,ui-monospace,Menlo,Consolas,monospace}")


# medida real do texto, a partir da própria fonte (para alinhar régua e cotas)
try:
    from fontTools.ttLib import TTFont
    _F = {"sans": "/usr/share/fonts/opentype/inter/InterDisplay-ExtraLight.otf",
          "serif": "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"}
    _M = {k: TTFont(v) for k, v in _F.items() if os.path.exists(v)}
except Exception:
    _M = {}


def width(text, font, size, fallback=0.5):
    f = _M.get(font)
    if not f:
        return len(text) * size * fallback
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap[ord(ch)]][0] for ch in text if ord(ch) in cmap) * size / upm


def defs_common(t, w, h, uid):
    return (f'<filter id="g{uid}" x="0" y="0" width="100%" height="100%">'
            f'<feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 {1 if uid.startswith("d") else 0}  0 0 0 0 {1 if uid.startswith("d") else 0}  0 0 0 0 {1 if uid.startswith("d") else 0}  0 0 0 {t["grain"]*1.4} 0"/></filter>'
            f'<filter id="b{uid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>'
            f'<clipPath id="c{uid}"><rect width="{w}" height="{h}" rx="16"/></clipPath>')


def blob(t, uid, cx, cy, r, dx, dy, dur):
    return (f'<g filter="url(#b{uid})"><ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{r*0.62}" fill="{t["blob"]}" opacity=".55">'
            f'<animate attributeName="cx" values="{cx};{cx+dx};{cx-dx*0.4};{cx}" dur="{dur}s" repeatCount="indefinite"/>'
            f'<animate attributeName="cy" values="{cy};{cy+dy};{cy-dy};{cy}" dur="{dur*1.3:.1f}s" repeatCount="indefinite"/></ellipse>'
            f'<ellipse cx="{cx-180}" cy="{cy+60}" rx="{r*0.7}" ry="{r*0.4}" fill="{t["blob2"]}" opacity=".8">'
            f'<animate attributeName="cx" values="{cx-180};{cx-120};{cx-220};{cx-180}" dur="{dur*1.7:.1f}s" repeatCount="indefinite"/></ellipse></g>')


def alu_grad(t, gid, x1, x2):
    st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in zip((0, .38, .55, .72, 1), t["alu"]))
    span = x2 - x1
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="0" x2="{x2}" y2="40" spreadMethod="reflect">{st}'
            f'<animateTransform attributeName="gradientTransform" type="translate" values="{-span} 0;{span} 0" dur="7s" repeatCount="indefinite"/>'
            f'</linearGradient>')


# ───────────────────────── cabeçalho ─────────────────────────
def header(mode):
    t, u = THEMES[mode], mode[0] + "h"
    W, H = 900, 336
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<style>{fontcss("sans", "serif", "mono")}'
         f'.st{{opacity:.28;animation:st 8s infinite}}'
         f'@keyframes st{{0%,8%{{opacity:.28}}12%,30%{{opacity:1}}36%,100%{{opacity:.28}}}}'
         f'.ty{{opacity:0;animation:ty .3s forwards}}@keyframes ty{{to{{opacity:1}}}}</style>',
         f'<defs>{defs_common(t, W, H, u)}']
    x0, y1, y2, s1 = 40, 150, 226, 66
    w_a = width("Quem desenha", "sans", s1)
    w_b = width("é quem ", "sans", s1)
    w_c = width("constrói.", "serif", s1)
    o.append(alu_grad(t, "al" + u, x0 + w_b, x0 + w_b + w_c))
    o.append('</defs>')
    o.append(f'<g clip-path="url(#c{u})"><rect width="{W}" height="{H}" fill="{t["bg"]}"/>')
    o.append(blob(t, u, 690, 150, 230, 70, 30, 16))
    o.append(f'<rect width="{W}" height="{H}" filter="url(#g{u})"/>')
    # linha de topo
    o.append(f'<text class="m" x="{x0}" y="38" font-size="10.5" letter-spacing="2.2" fill="{t["dim"]}">KZ27X — ZARPA DEV</text>')
    o.append(f'<text class="m" x="{W-40}" y="38" font-size="10.5" letter-spacing="2.2" fill="{t["dim"]}" text-anchor="end">20°19′S · 40°20′W · ES, BRASIL</text>')
    o.append(f'<line x1="{x0}" y1="54" x2="{W-40}" y2="54" stroke="{t["line2"]}" stroke-width="1"/>')
    # título
    o.append(f'<text class="s" x="{x0-3}" y="{y1}" font-size="{s1}" fill="{t["text"]}" letter-spacing="-1.5">Quem desenha</text>')
    o.append(f'<text x="{x0-3}" y="{y2}" font-size="{s1}" letter-spacing="-1.5"><tspan class="s" fill="{t["text"]}">é quem </tspan>'
             f'<tspan class="i" fill="url(#al{u})" letter-spacing="-1">constrói.</tspan></text>')
    # cota sobre "constrói." (medido)
    cx1, cx2, cy = x0 + w_b - 1, x0 + w_b + w_c - 10, y2 + 22
    mm = round((cx2 - cx1) * 0.2646)
    o.append(f'<g stroke="{t["faint"]}" stroke-width="1" opacity="0"><animate attributeName="opacity" from="0" to="1" begin="1.2s" dur=".8s" fill="freeze"/>'
             f'<line x1="{cx1:.0f}" y1="{cy-6}" x2="{cx1:.0f}" y2="{cy+6}"/><line x1="{cx2:.0f}" y1="{cy-6}" x2="{cx2:.0f}" y2="{cy+6}"/>'
             f'<line x1="{cx1:.0f}" y1="{cy}" x2="{cx2:.0f}" y2="{cy}" stroke-dasharray="2 3"/></g>')
    o.append(f'<text class="m" x="{(cx1+cx2)/2:.0f}" y="{cy+16}" font-size="9" fill="{t["dim"]}" text-anchor="middle" letter-spacing="1.5" opacity="0">'
             f'<animate attributeName="opacity" from="0" to="1" begin="1.6s" dur=".8s" fill="freeze"/>{mm} MM · SOB MEDIDA</text>')
    # régua (desenha da esquerda para a direita)
    ry, rx2 = 282, W - 40
    L = rx2 - x0
    ticks = "".join(f'M{x0+i*10} {ry}V{ry-(9 if i % 10 == 0 else 5 if i % 5 == 0 else 3)}' for i in range(int(L/10) + 1))
    o.append(f'<path d="M{x0} {ry}H{rx2}{ticks}" stroke="{t["faint"]}" stroke-width="1" fill="none" stroke-dasharray="{L*3}" stroke-dashoffset="{L*3}">'
             f'<animate attributeName="stroke-dashoffset" from="{L*3}" to="0" begin=".3s" dur="2.4s" fill="freeze" calcMode="spline" keySplines=".2 .7 .2 1" keyTimes="0;1"/></path>')
    # etapas (cada uma acende na sua vez)
    steps = ["MATÉRIA BRUTA", "MEDIDO", "USINADO", "SOB MEDIDA"]
    sx = x0
    for i, s in enumerate(steps):
        o.append(f'<text class="m st" x="{sx}" y="{ry+30}" font-size="10.5" letter-spacing="2" fill="{t["text"]}" style="animation-delay:{i*2}s">{s}</text>')
        sx += len(s) * 10.5 * 0.602 + len(s) * 2 + 14
        if i < 3:
            o.append(f'<text class="m" x="{sx}" y="{ry+30}" font-size="10.5" fill="{t["faint"]}">→</text>')
            sx += 26
    # terminal à direita
    tx, ty = 610, 112
    lines = [("$ ", "whoami", 0.6), ("", "kauã pessin", 1.5), ("$ ", "cat ofício.txt", 2.2), ("", "sites e sistemas sob medida", 3.1),
             ("$ ", "zarpar", 3.8)]
    for i, (pr, txt, b) in enumerate(lines):
        col = t["dim"] if pr else t["text"]
        o.append(f'<text class="m ty" x="{tx}" y="{ty+i*21}" font-size="12" style="animation-delay:{b}s">'
                 f'<tspan fill="{t["faint"]}">{pr}</tspan><tspan fill="{col}">{e(txt)}</tspan></text>')
    cur_x = tx + len("$ zarpar") * 12 * 0.602 + 4
    o.append(f'<rect x="{cur_x:.0f}" y="{ty+4*21-10}" width="7" height="13" fill="{t["text"]}" opacity="0">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1.1s" begin="4s" repeatCount="indefinite"/></rect>')
    o.append(f'</g><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{t["line"]}"/></svg>')
    open(A(f"header-{mode}.svg"), "w", encoding="utf-8").write("".join(o))


# ───────────────────────── dados do GitHub ─────────────────────────
def fetch():
    if not TOKEN:
        random.seed(3)
        d0 = date.today() - timedelta(days=364)
        days = [(d0 + timedelta(i), random.choice([0, 0, 0, 0, 1, 2, 4])) for i in range(365)]
        return days, dict(commits=9, prs=0, repos=4), {"JavaScript": 70, "HTML": 20, "CSS": 10}
    q = """{ user(login:"%s"){
      repositories(ownerAffiliations:OWNER,isFork:false,first:100){totalCount
        nodes{languages(first:5,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
      contributionsCollection{totalCommitContributions totalPullRequestContributions
        contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""" % USER
    req = urllib.request.Request("https://api.github.com/graphql", data=json.dumps({"query": q}).encode(),
                                 headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"})
    u = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]
    cc = u["contributionsCollection"]
    days = [(date.fromisoformat(x["date"]), x["contributionCount"])
            for w in cc["contributionCalendar"]["weeks"] for x in w["contributionDays"]]
    langs = {}
    for r in u["repositories"]["nodes"]:
        for ed in r["languages"]["edges"]:
            langs[ed["node"]["name"]] = langs.get(ed["node"]["name"], 0) + ed["size"]
    return days, dict(commits=cc["totalCommitContributions"], prs=cc["totalPullRequestContributions"],
                      repos=u["repositories"]["totalCount"]), langs


def streaks(days):
    best = cur = 0
    for _, n in days:
        cur = cur + 1 if n else 0
        best = max(best, cur)
    now, today = 0, date.today()
    for d, n in reversed(days):
        if n: now += 1
        elif d != today: break
    return now, best


# ───────────────────────── painel ─────────────────────────
def painel(mode, data):
    days, st, langs = data
    t, u = THEMES[mode], mode[0] + "p"
    W, H = 900, 452
    grid = json.load(open(A(f"portrait-{mode}.json")))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<style>{fontcss("sanslight", "mono")}</style><defs>{defs_common(t, W, H, u)}',
         f'<linearGradient id="sc{u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["text"]}" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="{t["text"]}" stop-opacity=".22"/><stop offset="1" stop-color="{t["text"]}" stop-opacity="0"/></linearGradient>'
         f'<clipPath id="pc{u}"><rect x="24" y="52" width="390" height="388"/></clipPath></defs>',
         f'<g clip-path="url(#c{u})"><rect width="{W}" height="{H}" fill="{t["bg"]}"/>',
         blob(t, u, 230, 260, 190, 40, 25, 19),
         f'<rect width="{W}" height="{H}" filter="url(#g{u})"/>']
    # barra de cima
    o.append(f'<text class="m" x="28" y="32" font-size="10" letter-spacing="1.8" fill="{t["dim"]}">~/KAUÃ/RETRATO.TXT</text>')
    o.append(f'<text class="m" x="{W-28}" y="32" font-size="10" letter-spacing="1.8" fill="{t["dim"]}" text-anchor="end">'
             f'MEDIDO EM {date.today():%d·%m·%Y}</text>')
    o.append(f'<line x1="28" y1="44" x2="{W-28}" y2="44" stroke="{t["line2"]}"/>')
    # retrato em caracteres: linha por linha, como se estivesse sendo usinado
    fs, cwid = 8.6, 8.6 * 0.602
    lh = cwid * 1.65
    rows = len(grid)
    y0 = 52 + (388 - rows * lh) / 2 + lh
    o.append(f'<g clip-path="url(#pc{u})">')
    for r, row in enumerate(grid):
        segs, cur, buf = [], None, ""
        for ch, k in row:
            k = 1 if ch == " " else k
            if k != cur and buf:
                segs.append((cur, buf)); buf = ""
            cur = k; buf += ch
        segs.append((cur, buf))
        spans = "".join(f'<tspan fill="{t["ink"][k]}">{e(s)}</tspan>' for k, s in segs)
        b = 0.25 + r * 0.055
        o.append(f'<text class="m" x="28" y="{y0 + r*lh:.1f}" font-size="{fs}" xml:space="preserve" opacity="0">'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{b:.2f}s" dur=".25s" fill="freeze"/>{spans}</text>')
    total = 0.25 + rows * 0.055
    o.append(f'<rect x="24" y="52" width="390" height="26" fill="url(#sc{u})">'
             f'<animate attributeName="y" values="40;{52+rows*lh:.0f}" dur="{total:.2f}s" fill="freeze"/>'
             f'<animate attributeName="y" values="40;440;440" keyTimes="0;.55;1" dur="7s" begin="{total+1:.1f}s" repeatCount="indefinite"/></rect>')
    o.append('</g>')
    o.append(f'<line x1="430" y1="60" x2="430" y2="{H-28}" stroke="{t["line"]}"/>')

    # coluna da direita
    X, R = 456, W - 28
    o.append(f'<text class="m" x="{X}" y="72" font-size="9.5" letter-spacing="2" fill="{t["dim"]}">CONTRIBUIÇÕES · 12 MESES</text>')
    weeks, col = [], []
    for d, n in days:
        if d.weekday() == 6 and col: weeks.append(col); col = []
        col.append((d, n))
    if col: weeks.append(col)
    weeks = weeks[-53:]
    mx = max([n for _, n in days] + [1])
    gap = 2; cell = ((R - X) - gap * 52) / 53
    for wi, w in enumerate(weeks):
        for d, n in w:
            lv = 0 if n == 0 else min(4, 1 + int(3 * n / mx))
            o.append(f'<rect x="{X + wi*(cell+gap):.1f}" y="{84 + ((d.weekday()+1) % 7)*(cell+gap):.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="1.4" fill="{t["heat"][lv]}"/>')
    total_c = sum(n for _, n in days)
    now, best = streaks(days)
    stats = [(total_c, "contribuições"), (st["commits"], "commits"), (st["repos"], "repositórios"),
             (f"{best}d", "maior sequência"), (f"{now}d", "sequência atual"), (st["prs"], "pull requests")]
    o.append(f'<text class="m" x="{X}" y="186" font-size="9.5" letter-spacing="2" fill="{t["dim"]}">EM NÚMEROS</text>')
    cw3 = (R - X) / 3
    for i, (v, k) in enumerate(stats):
        cx, cy = X + (i % 3) * cw3, 236 + (i // 3) * 66
        o.append(f'<text class="sl" x="{cx}" y="{cy}" font-size="34" letter-spacing="-1" fill="{t["text"]}">{e(v)}</text>')
        o.append(f'<text class="m" x="{cx+1}" y="{cy+18}" font-size="9" letter-spacing="1.4" fill="{t["dim"]}">{e(k.upper())}</text>')
    # linguagens
    o.append(f'<text class="m" x="{X}" y="354" font-size="9.5" letter-spacing="2" fill="{t["dim"]}">LINGUAGENS</text>')
    tot = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
    shades = [t["text"], t["heat"][3], t["heat"][2], t["heat"][1]]
    bx = X
    for i, (n, v) in enumerate(top):
        w = (R - X) * v / tot
        o.append(f'<rect x="{bx:.1f}" y="366" width="{max(w-3, 2):.1f}" height="3" rx="1.5" fill="{shades[i]}"/>')
        bx += w
    lx = X
    for i, (n, v) in enumerate(top):
        lbl = f"{n} {v/tot*100:.0f}%"
        o.append(f'<circle cx="{lx+3}" cy="389" r="3" fill="{shades[i]}"/><text class="m" x="{lx+11}" y="392" font-size="9.5" fill="{t["dim"]}">{e(lbl)}</text>')
        lx += len(lbl) * 9.5 * 0.602 + 30
    o.append(f'<line x1="{X}" y1="410" x2="{R}" y2="410" stroke="{t["line"]}"/>')
    o.append(f'<text class="m" x="{X}" y="430" font-size="9.5" letter-spacing="1.6" fill="{t["dim"]}">ENTENDER → PENSAR → CONSTRUIR → LANÇAR</text>')
    o.append(f'</g><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="{t["line"]}"/></svg>')
    open(A(f"painel-{mode}.svg"), "w", encoding="utf-8").write("".join(o))


# ───────────────────────── botões ─────────────────────────
def botao(nome, label, fill_defs, fill, glow, text_col="#FFFFFF", font="sanslight"):
    W, H, bw, bh = 236, 76, 196, 46
    x, y = (W - bw) / 2, (H - bh) / 2
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
         f'<style>{fontcss(font)}</style><defs>{fill_defs}'
         f'<filter id="gl" x="-40%" y="-80%" width="180%" height="260%"><feGaussianBlur stdDeviation="9"/></filter></defs>'
         f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="{bh/2}" fill="{glow}" filter="url(#gl)" opacity=".55">'
         f'<animate attributeName="opacity" values=".35;.7;.35" dur="3.2s" repeatCount="indefinite"/></rect>'
         f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="{bh/2}" fill="{fill}"/>'
         f'<rect x="{x+.5}" y="{y+.5}" width="{bw-1}" height="{bh/2}" rx="{bh/2-1}" fill="#fff" opacity=".12"/>'
         f'<text class="{"sl" if font == "sanslight" else "m"}" x="{W/2}" y="{H/2+6}" font-size="17" fill="{text_col}" text-anchor="middle" letter-spacing=".3">{e(label)}</text></svg>')
    open(A(f"btn-{nome}.svg"), "w", encoding="utf-8").write(s)


def botoes():
    botao("whatsapp", "WhatsApp  ↗", "", "#25D366", "#25D366")
    ig = ('<linearGradient id="ig" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#FEDA75"/><stop offset=".3" stop-color="#FA7E1E"/>'
          '<stop offset=".55" stop-color="#D62976"/><stop offset=".8" stop-color="#962FBF"/><stop offset="1" stop-color="#4F5BD5"/></linearGradient>')
    botao("instagram", "Instagram  ↗", ig, "url(#ig)", "#D62976")
    for mode, t in THEMES.items():
        for nome, label in (("site", "zarpadev.com.br"), ("zarpa", "@zarpa.dev")):
            W, H, bw, bh = 236, 76, 196, 46
            x, y = (W - bw) / 2, (H - bh) / 2
            st = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in zip((0, .38, .55, .72, 1), t["alu"]))
            s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
                 f'<style>{fontcss("sanslight")}</style><defs><linearGradient id="a" x1="0" y1="0" x2="1" y2="1">{st}</linearGradient></defs>'
                 f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="{bh/2}" fill="{t["surf"]}" fill-opacity=".9"/>'
                 f'<rect x="{x+.5}" y="{y+.5}" width="{bw-1}" height="{bh-1}" rx="{bh/2}" fill="none" stroke="url(#a)" stroke-width="1"/>'
                 f'<text class="sl" x="{W/2}" y="{H/2+6}" font-size="16" fill="{t["text"]}" text-anchor="middle">{e(label)}</text></svg>')
            open(A(f"btn-{nome}-{mode}.svg"), "w", encoding="utf-8").write(s)


if __name__ == "__main__":
    data = fetch()
    for m in THEMES:
        painel(m, data)
    # cabeçalho e botões não dependem de dados: só são gerados localmente (precisam das fontes para medir o texto)
    if not os.environ.get("CI"):
        for m in THEMES:
            header(m)
        botoes()
    print("ok")
