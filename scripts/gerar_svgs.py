#!/usr/bin/env python3
"""Gera os SVGs do README de perfil: banner, cards de projeto e rodapé, nos temas escuro e claro.

    python3 scripts/gerar_svgs.py

Tudo sai em assets/. O GitHub serve essas imagens isoladas — sem fonte externa e sem script —,
então a tipografia usa as fontes do sistema e toda animação é SMIL.

O banner tem um pouco de física de verdade: os períodos seguem a 3ª lei de Kepler (T² ∝ a³) e o
movimento é angular uniforme, que é o certo para órbita circular vista em perspectiva. A escala,
não: ver "Notas sobre o banner" no README.
"""

from __future__ import annotations

import math
import random
from html import escape
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

TEMAS = {
    "dark": {
        "fundo_a": "#060A14", "fundo_b": "#101934",
        "card": "#0D1322", "borda": "#1E2942",
        "titulo": "#F2F5FA", "texto": "#A7B1C6", "fraco": "#66728C",
        "ouro": "#F5B841", "laranja": "#FF8A3D",
        "linha": "#FFFFFF", "linha_op": 0.14,
        "estrela": "#FFFFFF", "estrela_op": 1.0,
        "chip_fundo": "#131B30", "chip_borda": "#27324D", "chip_texto": "#C8D1E3",
        "brilho_op": 0.55, "nebulosa": "#3B5BDB",
    },
    "light": {
        "fundo_a": "#FFFDF8", "fundo_b": "#EDF1F9",
        "card": "#FFFFFF", "borda": "#D8DEE8",
        "titulo": "#141A26", "texto": "#4B5567", "fraco": "#8590A3",
        "ouro": "#B7791F", "laranja": "#D9601A",
        "linha": "#1B2233", "linha_op": 0.17,
        "estrela": "#1B2233", "estrela_op": 0.45,
        "chip_fundo": "#F4F6FA", "chip_borda": "#D8DEE8", "chip_texto": "#2F3848",
        "brilho_op": 0.35, "nebulosa": "#7C9CF5",
    },
}


def misturar(cor: str, alvo: str, t: float) -> str:
    """Interpola duas cores #RRGGBB; t=0 devolve `cor`, t=1 devolve `alvo`."""
    a = [int(cor[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(alvo[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


def f(x: float) -> str:
    """Número curto para atributo SVG."""
    return f"{x:.2f}".rstrip("0").rstrip(".")


def largura_mono(texto: str, tamanho: float) -> float:
    return len(texto) * tamanho * 0.61


def chips(itens: list[str], x: float, y: float, t: dict, tamanho: float = 13, cor_texto: str | None = None) -> str:
    """Fileira de pílulas em fonte mono, que tem largura previsível em qualquer sistema."""
    partes, cx = [], x
    altura = tamanho * 2.1
    for item in itens:
        w = largura_mono(item, tamanho) + tamanho * 1.7
        partes.append(
            f'<rect x="{f(cx)}" y="{f(y)}" width="{f(w)}" height="{f(altura)}" rx="{f(altura / 2)}" '
            f'fill="{t["chip_fundo"]}" stroke="{t["chip_borda"]}"/>'
            f'<text x="{f(cx + w / 2)}" y="{f(y + altura * 0.66)}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="{tamanho}" fill="{cor_texto or t["chip_texto"]}">{escape(item)}</text>'
        )
        cx += w + tamanho * 0.65
    return "".join(partes)


# ─────────────────────────────────────────────────────────────── banner ──

SOL = (905.0, 178.0)
SOL_R = 26.0
INCLINACAO = 0.34          # b/a das órbitas: círculos vistos a ~70° do polo
GIRO = -9                  # rotação do plano na tela, em graus
T0, A0 = 8.0, 95.0         # período do planeta de dentro, em segundos, e o raio dele
AMOSTRAS = 96

PLANETAS = [
    {"a": 95.0, "r": 4.2, "cor": "#CFC7B9", "fase": 205},
    {"a": 140.0, "r": 6.4, "cor": "#4C9BFF", "fase": 320, "lua": True},
    {"a": 190.0, "r": 5.2, "cor": "#E5683F", "fase": 75},
    {"a": 245.0, "r": 8.6, "cor": "#E9C27C", "fase": 145, "anel": True},
]


def periodo(a: float) -> float:
    return T0 * (a / A0) ** 1.5


def orbita_valores(a: float, b: float, fase_graus: float, n: int = AMOSTRAS):
    """Pontos igualmente espaçados no TEMPO (ângulo uniforme), não no comprimento de arco.

    Com calcMode="linear", o animateMotion dá a mesma fatia de tempo a cada segmento, então o
    planeta corre na frente e atrás do Sol e quase para nas laterais da elipse projetada — como
    uma órbita circular de verdade vista de lado. O sentido escolhido faz o lado próximo (de
    baixo) correr da esquerda para a direita.
    """
    pontos = []
    for k in range(n + 1):
        th = math.radians(fase_graus) - 2 * math.pi * k / n
        pontos.append((a * math.cos(th), b * math.sin(th), math.sin(th)))
    return pontos


def planeta_svg(p: dict, t: dict, idx: int) -> str:
    a, r = p["a"], p["r"]
    b = a * INCLINACAO
    dur = periodo(a)
    pts = orbita_valores(a, b, p["fase"])
    caminho = ";".join(f"{f(x)},{f(y)}" for x, y, _ in pts)
    # Profundidade: um pouco maior e mais opaco quando passa na frente (sin θ > 0 é o lado de baixo).
    escalas = ";".join(f(1 + 0.14 * s) for _, _, s in pts)
    opacidades = ";".join(f(0.7 + 0.3 * (s + 1) / 2) for _, _, s in pts)

    grad = f"pl{idx}"
    corpo = f'<circle r="{f(r)}" fill="url(#{grad})"/>'
    if p.get("anel"):
        anel_cor = misturar(p["cor"], "#FFFFFF", 0.25)
        tras = f'<path d="M {f(-r * 1.85)} 0 A {f(r * 1.85)} {f(r * 0.55)} 0 0 1 {f(r * 1.85)} 0" fill="none" stroke="{anel_cor}" stroke-width="1.6" opacity="0.55"/>'
        frente = f'<path d="M {f(r * 1.85)} 0 A {f(r * 1.85)} {f(r * 0.55)} 0 0 1 {f(-r * 1.85)} 0" fill="none" stroke="{anel_cor}" stroke-width="1.6" opacity="0.95"/>'
        corpo = tras + corpo + frente
    if p.get("lua"):
        lua_pts = orbita_valores(14, 8.5, 30, 48)
        lua_cam = ";".join(f"{f(x)},{f(y)}" for x, y, _ in lua_pts)
        corpo += (
            f'<circle r="1.7" fill="{misturar("#D9DCE3", t["fundo_a"], 0.05)}">'
            f'<animateMotion dur="2.6s" repeatCount="indefinite" calcMode="linear" values="{lua_cam}"/></circle>'
        )
    return (
        f'<g><animateMotion dur="{f(dur)}s" repeatCount="indefinite" calcMode="linear" values="{caminho}"/>'
        f'<animate attributeName="opacity" dur="{f(dur)}s" repeatCount="indefinite" calcMode="linear" values="{opacidades}"/>'
        f'<g><animateTransform attributeName="transform" type="scale" dur="{f(dur)}s" repeatCount="indefinite" calcMode="linear" values="{escalas}"/>'
        f"{corpo}</g></g>"
    )


def banner(tema: str) -> str:
    t = TEMAS[tema]
    W, H = 1200, 340
    rnd = random.Random(1579)  # 15.79°S

    defs = [
        f'<linearGradient id="fundo" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["fundo_a"]}"/><stop offset="1" stop-color="{t["fundo_b"]}"/></linearGradient>',
        f'<radialGradient id="neb" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{t["nebulosa"]}" stop-opacity="0.16"/><stop offset="1" stop-color="{t["nebulosa"]}" stop-opacity="0"/></radialGradient>',
        f'<radialGradient id="halo" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#FFB547" stop-opacity="{t["brilho_op"]}"/><stop offset="0.35" stop-color="#FF8A3D" stop-opacity="{f(t["brilho_op"] * 0.35)}"/><stop offset="1" stop-color="#FF8A3D" stop-opacity="0"/></radialGradient>',
        '<radialGradient id="sol" cx="0.42" cy="0.4" r="0.62"><stop offset="0" stop-color="#FFF7DA"/><stop offset="0.45" stop-color="#FFCB52"/><stop offset="1" stop-color="#FF8A3D"/></radialGradient>',
        f'<linearGradient id="cauda" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["estrela"]}" stop-opacity="0"/><stop offset="1" stop-color="{t["estrela"]}" stop-opacity="0.9"/></linearGradient>',
        f'<clipPath id="moldura"><rect width="{W}" height="{H}" rx="18"/></clipPath>',
    ]
    for i, p in enumerate(PLANETAS):
        claro, escuro = misturar(p["cor"], "#FFFFFF", 0.45), misturar(p["cor"], "#000000", 0.45)
        defs.append(
            f'<radialGradient id="pl{i}" cx="0.35" cy="0.32" r="0.75"><stop offset="0" stop-color="{claro}"/>'
            f'<stop offset="0.55" stop-color="{p["cor"]}"/><stop offset="1" stop-color="{escuro}"/></radialGradient>'
        )

    estrelas = []
    for i in range(90):
        x, y = rnd.uniform(8, W - 8), rnd.uniform(8, H - 8)
        r = rnd.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2, 1.5])
        op = rnd.uniform(0.2, 0.85) * t["estrela_op"]
        brilha = ""
        if i % 6 == 0:
            d = rnd.uniform(2.8, 6.5)
            brilha = (f'<animate attributeName="opacity" values="{f(op)};{f(op * 0.15)};{f(op)}" '
                      f'dur="{f(d)}s" begin="{f(rnd.uniform(0, d))}s" repeatCount="indefinite"/>')
        estrelas.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{t["estrela"]}" opacity="{f(op)}">{brilha}</circle>')

    orbitas = []
    for p in PLANETAS:
        a = p["a"]
        b = a * INCLINACAO
        tracejado = ' stroke-dasharray="2 5"' if a == PLANETAS[-1]["a"] else ""
        # Metade de trás mais apagada que a da frente: dá profundidade sem desenhar nada a mais.
        orbitas.append(
            f'<path d="M {f(-a)} 0 A {f(a)} {f(b)} 0 0 1 {f(a)} 0" fill="none" stroke="{t["linha"]}" '
            f'stroke-opacity="{f(t["linha_op"] * 0.6)}"{tracejado}/>'
            f'<path d="M {f(a)} 0 A {f(a)} {f(b)} 0 0 1 {f(-a)} 0" fill="none" stroke="{t["linha"]}" '
            f'stroke-opacity="{f(t["linha_op"] * 1.25)}"{tracejado}/>'
        )

    sx, sy = SOL
    sistema = (
        f'<circle cx="{f(sx)}" cy="{f(sy)}" r="150" fill="url(#halo)">'
        f'<animate attributeName="r" values="146;158;146" dur="6s" repeatCount="indefinite"/></circle>'
        f'<g transform="translate({f(sx)} {f(sy)}) rotate({GIRO})">'
        + "".join(orbitas)
        + f'<circle r="{f(SOL_R)}" fill="url(#sol)"/>'
        + "".join(planeta_svg(p, t, i) for i, p in enumerate(PLANETAS))
        + "</g>"
    )

    meteoro = (
        '<g opacity="0">'
        '<animateMotion path="M 1185 26 L 1050 104" dur="13s" begin="3s" repeatCount="indefinite" rotate="auto" '
        'calcMode="linear" keyPoints="0;0;1;1" keyTimes="0;0.84;0.9;1"/>'
        '<animate attributeName="opacity" values="0;0;0.9;0;0" keyTimes="0;0.84;0.86;0.9;1" dur="13s" begin="3s" repeatCount="indefinite"/>'
        f'<line x1="-70" y1="0" x2="0" y2="0" stroke="url(#cauda)" stroke-width="1.6" stroke-linecap="round"/>'
        f'<circle r="1.6" fill="{t["estrela"]}"/></g>'
    )

    texto = (
        f'<text x="72" y="108" font-family="{MONO}" font-size="15" letter-spacing="1" fill="{t["ouro"]}">'
        f'~/brasília-df  ·  15.79°S 47.88°W</text>'
        f'<text x="68" y="186" font-family="{SANS}" font-size="74" font-weight="800" letter-spacing="-2" fill="{t["titulo"]}">Thiago Brito</text>'
        f'<text x="72" y="230" font-family="{SANS}" font-size="23" fill="{t["texto"]}">'
        f'Software que diz o que faz <tspan fill="{t["ouro"]}">—</tspan> e tem teste provando.</text>'
        + chips(["TypeScript", "C", "WebGPU", "PostgreSQL", "React Native"], 72, 262, t, 13.5)
    )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Thiago Brito — software que diz o que faz, e tem teste provando.">'
        f"<title>Thiago Brito</title><defs>{''.join(defs)}</defs>"
        f'<g clip-path="url(#moldura)">'
        f'<rect width="{W}" height="{H}" fill="url(#fundo)"/>'
        f'<ellipse cx="260" cy="60" rx="420" ry="220" fill="url(#neb)"/>'
        + "".join(estrelas) + meteoro + sistema + texto +
        f'</g><rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{t["borda"]}"/>'
        "</svg>"
    )


# ─────────────────────────────────────────────────────── cards de projeto ──

def icone(tipo: str, cor: str) -> str:
    """Glifo de 48×48 desenhado com a cor de destaque do projeto."""
    if tipo == "orbita":
        return (
            f'<g transform="rotate(-18 24 24)"><ellipse cx="24" cy="24" rx="17" ry="6.5" fill="none" stroke="{cor}" stroke-width="1.6" opacity="0.7"/>'
            f'<circle cx="24" cy="24" r="6" fill="{cor}"/>'
            f'<circle r="2.6" fill="{cor}"><animateMotion dur="4s" repeatCount="indefinite" '
            f'path="M 41 24 A 17 6.5 0 1 1 7 24 A 17 6.5 0 1 1 41 24"/></circle></g>'
        )
    if tipo == "passe":
        return (
            f'<rect x="10" y="9" width="28" height="30" rx="4.5" fill="none" stroke="{cor}" stroke-width="1.8"/>'
            f'<line x1="15" y1="16" x2="28" y2="16" stroke="{cor}" stroke-width="1.8" stroke-linecap="round"/>'
            f'<line x1="15" y1="21" x2="23" y2="21" stroke="{cor}" stroke-width="1.8" stroke-linecap="round" opacity="0.6"/>'
            f'<rect x="15" y="26" width="8" height="8" rx="1.5" fill="{cor}"/>'
            f'<rect x="25.5" y="26" width="3" height="3" rx="0.6" fill="{cor}" opacity="0.7"/>'
            f'<rect x="30" y="30.5" width="3" height="3" rx="0.6" fill="{cor}" opacity="0.7"/>'
        )
    if tipo == "virus":
        espinhos = "".join(
            f'<line x1="{f(24 + 8.5 * math.cos(a))}" y1="{f(24 + 8.5 * math.sin(a))}" '
            f'x2="{f(24 + 13.5 * math.cos(a))}" y2="{f(24 + 13.5 * math.sin(a))}" stroke="{cor}" stroke-width="1.8"/>'
            f'<circle cx="{f(24 + 15 * math.cos(a))}" cy="{f(24 + 15 * math.sin(a))}" r="2" fill="{cor}"/>'
            for a in (i * math.pi / 4 for i in range(8))
        )
        return (
            f'<g>{espinhos}<circle cx="24" cy="24" r="8.5" fill="{cor}" fill-opacity="0.25" stroke="{cor}" stroke-width="1.8"/>'
            f'<circle cx="21.5" cy="22" r="1.8" fill="{cor}"/><circle cx="26.5" cy="26.5" r="1.3" fill="{cor}"/>'
            '<animateTransform attributeName="transform" type="rotate" from="0 24 24" to="360 24 24" dur="24s" repeatCount="indefinite"/></g>'
        )
    if tipo == "gota":
        return (
            f'<path d="M24 8 C24 8 13.5 20.5 13.5 28 A10.5 10.5 0 0 0 34.5 28 C34.5 20.5 24 8 24 8 Z" '
            f'fill="{cor}" fill-opacity="0.22" stroke="{cor}" stroke-width="1.8" stroke-linejoin="round"/>'
            f'<path d="M18.5 28.5 A5.5 5.5 0 0 0 22.5 33.5" fill="none" stroke="{cor}" stroke-width="1.8" stroke-linecap="round"/>'
        )
    raise ValueError(tipo)


PROJETOS = [
    {
        "arquivo": "sistema-solar",
        "titulo": "Sistema Solar 3D",
        "sub": "thivpb/sistema-solar-3d",
        "status": "43/43 entregues",
        "icone": "orbita",
        "cor": {"dark": "#F5B841", "light": "#B7791F"},
        "linhas": [
            "Simulador N-corpos com integração simplética sobre",
            "efemérides do JPL. WebGPU com fallback WebGL2, 13 luas,",
            "laboratório de Fourier e sandbox — tudo offline.",
        ],
        "chips": ["TypeScript", "Three.js", "WebGPU", "Preact", "Playwright"],
    },
    {
        "arquivo": "wallet-loyalty",
        "titulo": "Wallet Loyalty",
        "sub": "repositório privado",
        "status": "piloto · fase 0",
        "icone": "passe",
        "cor": {"dark": "#2DD4BF", "light": "#0F8A7E"},
        "linhas": [
            "Fidelidade na Apple Wallet e no Google Wallet, sem app.",
            "Ledger imutável, outbox transacional, worker em pg-boss.",
            "A Wallet mostra o saldo; quem determina é o backend.",
        ],
        "chips": ["TypeScript", "PostgreSQL", "pg-boss", "PGlite", "Vitest"],
    },
    {
        "arquivo": "diseases-doomsday",
        "titulo": "Disease's Doomsday",
        "sub": "com @Felps-26 · Projeto Integrador",
        "status": "v1.0",
        "icone": "virus",
        "cor": {"dark": "#A3E635", "light": "#4D7C0F"},
        "linhas": [
            "Arena 2D top-down: você é um anticorpo, e cada inimigo",
            "é um patógeno real. Chefes em 3 fases, colisão em grade",
            "espacial, shaders GLSL e quiz de saúde entre as ondas.",
        ],
        "chips": ["C", "Raylib", "GLSL", "Make"],
    },
    {
        "arquivo": "aequus",
        "titulo": "Aequus",
        "sub": "thivpb/Aequus",
        "status": "protótipo",
        "icone": "gota",
        "cor": {"dark": "#FB7185", "light": "#C8264A"},
        "linhas": [
            "App para registrar aplicações de insulina e cruzá-las",
            "com alimentação e rotina. Pet virtual, Bluetooth simulado",
            "— e nunca, em hipótese alguma, sugere dose.",
        ],
        "chips": ["React Native", "Expo", "TypeScript", "Vitest"],
    },
]


VARS_CARD = ("card", "borda", "titulo", "texto", "fraco", "chip_fundo", "chip_borda", "chip_texto")


def com_variaveis(svg: str) -> str:
    """Move cores `var(--x)` de atributos de apresentação para `style`, onde var() é válido.

    Atributo de apresentação SVG não aceita var(); propriedade CSS aceita. Junta tudo num único
    `style` por elemento, porque um elemento pode ter fill e stroke ao mesmo tempo.
    """
    import re

    def tag(m: re.Match) -> str:
        texto = m.group(0)
        props = re.findall(r'\s(fill|stroke|stop-color|stop-opacity)="(var\(--[\w-]+\))"', texto)
        if not props:
            return texto
        texto = re.sub(r'\s(fill|stroke|stop-color|stop-opacity)="var\(--[\w-]+\)"', "", texto)
        estilo = ";".join(f"{k}:{v}" for k, v in props)
        fecho = "/>" if texto.endswith("/>") else ">"
        return texto[: -len(fecho)] + f' style="{estilo}"' + fecho

    return re.sub(r"<[a-zA-Z][^<>]*>", tag, svg)


def card(p: dict) -> str:
    """Um SVG só, que troca de paleta pelo prefers-color-scheme do próprio navegador.

    Os cards ficam dentro de um link para o repositório. Com <picture>, o GitHub envolve a imagem
    num segundo link (para o próprio SVG), e o clique deixaria de levar ao repositório; por isso o
    tema aqui é resolvido dentro do SVG, e o <img> fica filho direto do <a>.
    """
    t = {k: f"var(--{k.replace('_', '-')})" for k in VARS_CARD}
    cor = "var(--ac)"
    W, H = 560, 250
    status_w = largura_mono(p["status"], 12.5) + 24

    def paleta(tema: str) -> str:
        v = TEMAS[tema]
        decl = ";".join(f"--{k.replace('_', '-')}:{v[k]}" for k in VARS_CARD)
        return f"{decl};--ac:{p['cor'][tema]};--luz:{0.12 if tema == 'dark' else 0.07}"

    estilo = (
        f"<style>svg{{{paleta('dark')}}}"
        f"@media (prefers-color-scheme: light){{svg{{{paleta('light')}}}}}</style>"
    )
    linhas = "".join(
        f'<text x="28" y="{122 + 25 * i}" font-family="{SANS}" font-size="16.5" fill="{t["texto"]}">{escape(l)}</text>'
        for i, l in enumerate(p["linhas"])
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="{escape(p["titulo"])} — {escape(" ".join(p["linhas"]))}">'
        f"<title>{escape(p['titulo'])}</title>{estilo}"
        f'<defs><linearGradient id="topo" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{cor}"/>'
        f'<stop offset="0.6" stop-color="{cor}" stop-opacity="0.15"/><stop offset="1" stop-color="{cor}" stop-opacity="0"/></linearGradient>'
        f'<radialGradient id="luz" cx="0" cy="0" r="1"><stop offset="0" stop-color="{cor}" stop-opacity="var(--luz)"/>'
        f'<stop offset="1" stop-color="{cor}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>'
        f'<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="{t["card"]}"/>'
        f'<rect width="{W}" height="{H}" fill="url(#luz)"/>'
        f'<rect width="{W}" height="3" fill="url(#topo)"/></g>'
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{t["borda"]}"/>'
        f'<rect x="28" y="26" width="48" height="48" rx="12" fill="{cor}" fill-opacity="0.13" stroke="{cor}" stroke-opacity="0.35"/>'
        f'<g transform="translate(28 26)">{icone(p["icone"], cor)}</g>'
        f'<text x="92" y="50" font-family="{SANS}" font-size="23" font-weight="700" fill="{t["titulo"]}">{escape(p["titulo"])}</text>'
        f'<text x="92" y="70" font-family="{MONO}" font-size="12.5" fill="{t["fraco"]}">{escape(p["sub"])}</text>'
        f'<rect x="{f(W - 28 - status_w)}" y="30" width="{f(status_w)}" height="24" rx="12" fill="{cor}" fill-opacity="0.12" stroke="{cor}" stroke-opacity="0.45"/>'
        f'<text x="{f(W - 28 - status_w / 2)}" y="46.5" text-anchor="middle" font-family="{MONO}" font-size="12.5" fill="{cor}">{escape(p["status"])}</text>'
        + linhas
        + chips(p["chips"], 28, 196, t, 12.5)
        + "</svg>"
    )
    return com_variaveis(svg)


# ────────────────────────────────────────────────────────────── rodapé ──

def rodape(tema: str) -> str:
    t = TEMAS[tema]
    W, H = 1200, 120
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="Obrigado pela visita — até a próxima órbita."><title>Até a próxima órbita</title>'
        f'<defs><linearGradient id="arco" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{t["ouro"]}" stop-opacity="0"/>'
        f'<stop offset="0.5" stop-color="{t["ouro"]}"/><stop offset="1" stop-color="{t["ouro"]}" stop-opacity="0"/></linearGradient>'
        f'<radialGradient id="h" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#FFB547" stop-opacity="{t["brilho_op"]}"/>'
        f'<stop offset="1" stop-color="#FF8A3D" stop-opacity="0"/></radialGradient></defs>'
        f'<path d="M 60 118 Q 600 30 1140 118" fill="none" stroke="url(#arco)" stroke-width="6" opacity="0.18"/>'
        f'<path d="M 60 118 Q 600 30 1140 118" fill="none" stroke="url(#arco)" stroke-width="1.4"/>'
        f'<circle cx="600" cy="74" r="30" fill="url(#h)"><animate attributeName="r" values="26;34;26" dur="5s" repeatCount="indefinite"/></circle>'
        f'<circle cx="600" cy="74" r="5" fill="#FFCB52"/>'
        f'<text x="600" y="36" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="1" fill="{t["fraco"]}">'
        f"obrigado pela visita · até a próxima órbita</text></svg>"
    )


def main() -> None:
    (ASSETS / "projetos").mkdir(parents=True, exist_ok=True)
    gerados = []
    for tema in TEMAS:
        gerados.append((ASSETS / f"banner-{tema}.svg", banner(tema)))
        gerados.append((ASSETS / f"rodape-{tema}.svg", rodape(tema)))
    for p in PROJETOS:
        gerados.append((ASSETS / "projetos" / f"{p['arquivo']}.svg", card(p)))
    for caminho, svg in gerados:
        caminho.write_text(svg + "\n", encoding="utf-8")
        print(f"{caminho.relative_to(ASSETS.parent)}  {len(svg) / 1024:.1f} KB")
    print("períodos (s):", ", ".join(f"a={p['a']:.0f} → {periodo(p['a']):.1f}" for p in PLANETAS))


if __name__ == "__main__":
    main()
