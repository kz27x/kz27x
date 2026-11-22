#!/usr/bin/env python3
"""Gera assets/dashboard.svg (painel estilo terminal) a partir dos dados do GitHub.
Sem GITHUB_TOKEN usa dados de demonstração (serve para testar o visual)."""
import json, os, sys, random, urllib.request, html
from datetime import date, timedelta

USER = os.environ.get("GH_USER", "SEU_USUARIO")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AMBER, DIM, BG, PANEL, TXT = "#FFB000", "#7a6a45", "#0d0b08", "#15120d", "#e8dcc0"
LEVELS = ["#1c1810", "#4a3a12", "#8a6a10", "#d99a00", "#FFB000"]
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


def gql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]


def fetch():
    if not TOKEN:
        random.seed(7)
        days, d = [], date.today() - timedelta(days=370)
        while d <= date.today():
            days.append((d, random.choice([0, 0, 0, 1, 2, 3, 5, 8]) if d.weekday() < 6 else random.choice([0, 0, 1])))
            d += timedelta(days=1)
        langs = {"TypeScript": 41, "JavaScript": 27, "HTML": 14, "CSS": 10, "Python": 8}
        return days, dict(commits=612, prs=23, repos=18, stars=9), langs
    q = """{ user(login:"%s"){
      repositories(ownerAffiliations:OWNER,isFork:false,first:100){totalCount
        nodes{stargazerCount languages(first:5,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}
      contributionsCollection{totalCommitContributions totalPullRequestContributions
        contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""" % USER
    u = gql(q)
    cc = u["contributionsCollection"]
    days = [(date.fromisoformat(x["date"]), x["contributionCount"])
            for w in cc["contributionCalendar"]["weeks"] for x in w["contributionDays"]]
    langs, stars = {}, 0
    for r in u["repositories"]["nodes"]:
        stars += r["stargazerCount"]
        for e in r["languages"]["edges"]:
            langs[e["node"]["name"]] = langs.get(e["node"]["name"], 0) + e["size"]
    stats = dict(commits=cc["totalCommitContributions"], prs=cc["totalPullRequestContributions"],
                 repos=u["repositories"]["totalCount"], stars=stars)
    return days, stats, langs


def streaks(days):
    best = cur = 0
    for _, n in days:
        cur = cur + 1 if n > 0 else 0
        best = max(best, cur)
    now = 0
    for _, n in reversed(days):
        if n > 0:
            now += 1
        elif now or _ != date.today():
            break
    return now, best


def lvl(n, mx):
    if n == 0: return 0
    r = n / max(mx, 1)
    return 1 if r < .25 else 2 if r < .5 else 3 if r < .75 else 4


def e(s): return html.escape(str(s))


def build():
    days, st, langs = fetch()
    total = sum(n for _, n in days)
    now, best = streaks(days)
    mx = max(n for _, n in days)
    W, H = 900, 372
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
           f'<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="#2a2418"/>']
    # barra do terminal
    out.append(f'<rect x="0" y="0" width="{W}" height="30" rx="10" fill="{PANEL}"/><rect x="0" y="20" width="{W}" height="10" fill="{PANEL}"/>')
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        out.append(f'<circle cx="{18+i*18}" cy="15" r="5" fill="{c}"/>')
    out.append(f'<text x="{W/2}" y="19" fill="{DIM}" font-size="12" text-anchor="middle">kaua@zarpa — ~/painel</text>')

    # painel esquerdo: retrato ASCII
    out.append(f'<text x="22" y="56" fill="{AMBER}" font-size="12">$ ./retrato</text>')
    p = os.path.join(ROOT, "assets", "portrait.txt")
    av = os.path.join(ROOT, "assets", "avatar-thumb.b64")
    lines = open(p, encoding="utf-8").read().rstrip("\n").split("\n") if os.path.exists(p) else []
    if not lines and os.path.exists(av):
        b64 = open(av).read().strip()
        out.append(f'<clipPath id="av"><rect x="22" y="68" width="280" height="280" rx="8"/></clipPath>')
        out.append(f'<image x="22" y="68" width="280" height="280" clip-path="url(#av)" href="data:image/jpeg;base64,{b64}"/>')
    lh = min(7.2, 250 / max(len(lines), 1))
    for i, l in enumerate(lines):
        out.append(f'<text x="22" y="{70+i*lh:.1f}" fill="{TXT}" font-size="{lh*0.95:.1f}" xml:space="preserve" textLength="{len(l)*lh*0.55:.0f}" lengthAdjust="spacingAndGlyphs">{e(l)}</text>')

    # painel direito: heatmap
    x0, y0 = 330, 56
    out.append(f'<text x="{x0}" y="{y0}" fill="{AMBER}" font-size="12">$ git log --heatmap --12m</text>')
    weeks, col = [], []
    for d, n in days:
        if d.weekday() == 6 and col:  # semana começa no domingo
            weeks.append(col); col = []
        col.append((d, n))
    if col: weeks.append(col)
    weeks = weeks[-53:]
    cell, gap = 8.2, 2
    for wi, w in enumerate(weeks):
        for d, n in w:
            dow = (d.weekday() + 1) % 7
            out.append(f'<rect x="{x0+wi*(cell+gap):.1f}" y="{y0+12+dow*(cell+gap):.1f}" width="{cell}" height="{cell}" rx="2" fill="{LEVELS[lvl(n,mx)]}"/>')
    # números
    tiles = [("contribuições 12m", total), ("commits", st["commits"]), ("pull requests", st["prs"]),
             ("repositórios", st["repos"]), ("maior sequência", f"{best}d"), ("sequência atual", f"{now}d")]
    ty = 190
    out.append(f'<text x="{x0}" y="{ty}" fill="{AMBER}" font-size="12">$ git shortlog --resumo</text>')
    for i, (k, v) in enumerate(tiles):
        cx, cy = x0 + (i % 3) * 190, ty + 14 + (i // 3) * 50
        out.append(f'<rect x="{cx}" y="{cy}" width="178" height="42" rx="6" fill="{PANEL}" stroke="#2a2418"/>')
        out.append(f'<text x="{cx+12}" y="{cy+19}" fill="{AMBER}" font-size="18" font-weight="700">{e(v)}</text>')
        out.append(f'<text x="{cx+12}" y="{cy+34}" fill="{DIM}" font-size="10">{e(k)}</text>')
    # linguagens
    ly = 322
    tot = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    out.append(f'<text x="{x0}" y="{ly}" fill="{AMBER}" font-size="12">$ linguagens</text>')
    bx, bw = x0, 560
    for i, (name, v) in enumerate(top):
        if v / tot < 0.08: bx += bw * v / tot; continue
        w = bw * v / tot
        out.append(f'<rect x="{bx:.1f}" y="{ly+8}" width="{max(w-2,2):.1f}" height="8" rx="2" fill="{LEVELS[4-min(i,3)]}"/>')
        out.append(f'<text x="{bx:.1f}" y="{ly+30}" fill="{TXT}" font-size="10">{e(name)} {v/tot*100:.0f}%</text>')
        bx += w
    out.append("</svg>")
    path = os.path.join(ROOT, "assets", "dashboard.svg")
    open(path, "w", encoding="utf-8").write("\n".join(out))
    print("ok", path)


if __name__ == "__main__":
    build()
