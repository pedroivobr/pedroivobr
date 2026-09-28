"""Gera o card estilo neofetch do README do perfil: avatar em ASCII colorido + info.

Entrada: avatar-sem-fundo.png (avatar com o fundo removido pelo rembg).
Saida: neofetch-dark.svg e neofetch-light.svg.
"""
import colorsys
from html import escape
from PIL import Image, ImageOps

COLS, ROWS = 64, 38          # 64 colunas: com 52 o rosto virava mancha
RAMP = " .:-=+*#%@"          # vazio -> denso; escala com letras virava "sopa de texto"
FS, CW, LH = 14, 8.4, 17     # texto da direita: fonte, largura do char, altura da linha
AFS, ACW, ALH = 12, 7.2, 14  # arte: fonte menor para caber mais resolucao

INFO = [
    ("title", "pedroivobr@github"),
    ("sep", "-" * 17),
    ("kv", "Cargo", "Engenheiro de Dados"),
    ("kv", "Atual", "Analista de Dados III @ DoisA"),
    ("kv", "Local", "Natal, RN - Brasil"),
    ("kv", "Uptime", "5+ anos com dados"),
    ("kv", "Formacao", "Eng. de Computacao - UFRN"),
    ("kv", "Pos", "BI Analytics - UFRN"),
    ("kv", "OS", "Arch Linux (Omarchy)"),
    ("blank",),
    ("kv", "Linguagens", "Python, SQL (T-SQL), C++"),
    ("kv", "Dados", "Delta Lake, DuckDB, Polars, Spark"),
    ("kv", "Bancos", "SQL Server, Postgres, BigQuery"),
    ("kv", "Orquestracao", "Prefect, Airflow"),
    ("kv", "Cloud", "Azure, Synapse, Data Factory"),
    ("kv", "DevOps", "Docker, Kubernetes, CI/CD"),
    ("kv", "IA", "Claude API, agentes, LLMs"),
    ("blank",),
    ("kv", "Email", "pedroivojr@proton.me"),
    ("kv", "LinkedIn", "in/pedro-ivo-297800167"),
    ("blank",),
    ("colors",),
]

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", fg="#c9d1d9", key="#d2a8ff",
                 title="#79c0ff", dim="#8b949e", v_min=0.55, v_max=1.0),
    "light": dict(bg="#ffffff", border="#d0d7de", fg="#24292f", key="#8250df",
                  title="#0969da", dim="#57606a", v_min=0.15, v_max=0.6),
}
PALETTE = ["#f85149", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#e6edf3", "#6e7681"]


def ascii_rows(path, v_min, v_max, dark):
    """Converte o avatar em linhas de (caractere, cor).

    O fundo vem removido no canal alfa: a parede clara dominava o desenho e o
    rosto sumia. Fora da pessoa, o caractere e' espaco.
    """
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    img = img.crop((int(w * 0.08), 0, int(w * 0.92), h))
    small = img.resize((COLS, ROWS), Image.LANCZOS)
    rgb, alpha = small.convert("RGB"), small.getchannel("A")
    mask = alpha.point(lambda a: 255 if a > 128 else 0)
    # equaliza so' a luminancia da pessoa: o rosto ocupa uma faixa estreita de
    # tons e, sem isso, olhos, barba e oculos viram o mesmo caractere
    lum = ImageOps.equalize(rgb.convert("L"), mask=mask)
    rows = []
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            if not mask.getpixel((x, y)):
                row.append((" ", None))
                continue
            l = lum.getpixel((x, y)) / 255
            # no fundo escuro, claro = denso (a pele acende, barba e oculos recuam)
            d = l if dark else 1 - l
            ch = RAMP[1 + min(len(RAMP) - 2, int(d * (len(RAMP) - 1)))]
            # mantem matiz e saturacao, mas prende o brilho numa faixa legivel no
            # fundo do tema (o chapeu azul-escuro sumia no fundo escuro)
            r, g, b = rgb.getpixel((x, y))
            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            vv = v_min + (v_max - v_min) * vv
            ss = min(1.0, ss * 1.3)
            rr, gg, bb = (int(c * 255) // 16 * 16 for c in colorsys.hsv_to_rgb(hh, ss, vv))
            row.append((ch, "#%02x%02x%02x" % (rr, gg, bb)))
        rows.append(row)
    return rows


def svg(theme):
    t = THEMES[theme]
    dark = theme == "dark"
    pad = 24
    art_w = COLS * ACW
    info_x = pad + art_w + 28
    h = pad * 2 + ROWS * ALH
    w = info_x + 40 * CW + pad
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h}" '
           f'viewBox="0 0 {w:.0f} {h}" font-family="ui-monospace,SFMono-Regular,Consolas,'
           f'Liberation Mono,Menlo,monospace" font-size="{FS}">',
           f'<rect width="100%" height="100%" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>']

    for i, row in enumerate(ascii_rows("avatar-sem-fundo.png", t["v_min"], t["v_max"], dark)):
        y = pad + (i + 1) * ALH - 3
        spans, cur, buf = [], None, ""
        for ch, cor in row + [("", "fim")]:
            if cor != cur and buf:
                spans.append(escape(buf) if cur is None else f'<tspan fill="{cur}">{escape(buf)}</tspan>')
                buf = ""
            cur, buf = cor, buf + ch
        out.append(f'<text x="{pad}" y="{y}" xml:space="preserve" font-size="{AFS}" '
                   f'textLength="{art_w:.0f}" lengthAdjust="spacing">{"".join(spans)}</text>')

    y0 = pad + (h - 2 * pad - len(INFO) * LH) // 2
    for i, item in enumerate(INFO):
        y = y0 + (i + 1) * LH - 4
        kind = item[0]
        if kind == "title":
            user, host = item[1].split("@")
            out.append(f'<text x="{info_x}" y="{y}" font-weight="bold">'
                       f'<tspan fill="{t["title"]}">{user}</tspan><tspan fill="{t["fg"]}">@</tspan>'
                       f'<tspan fill="{t["title"]}">{host}</tspan></text>')
        elif kind == "sep":
            out.append(f'<text x="{info_x}" y="{y}" fill="{t["dim"]}">{item[1]}</text>')
        elif kind == "kv":
            out.append(f'<text x="{info_x}" y="{y}"><tspan fill="{t["key"]}" font-weight="bold">'
                       f'{escape(item[1])}</tspan><tspan fill="{t["fg"]}">: {escape(item[2])}</tspan></text>')
        elif kind == "colors":
            for j, c in enumerate(PALETTE):
                out.append(f'<rect x="{info_x + j * 3 * CW:.1f}" y="{y - 12}" width="{3 * CW:.1f}" '
                           f'height="{LH - 2}" fill="{c}"/>')
    out.append("</svg>")
    return "\n".join(out)


for theme in THEMES:
    with open(f"neofetch-{theme}.svg", "w") as f:
        f.write(svg(theme))
print("ok")
