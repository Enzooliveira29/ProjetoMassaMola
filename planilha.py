"""Gera e visualiza a planilha de referencia da malha massa-mola.

A "planilha" e a tabela que, para cada tipo de vertice (interno, borda,
canto), define a vizinhanca (molas estruturais, de cisalhamento e de flexao).
Este script CRIA essa planilha a partir do modelo e oferece tres formas de
visualiza-la:

  1. Mapa de tipos de vertice na malha;
  2. Diagramas de vizinhanca (canto / borda / interno);
  3. Tabela renderizada com as assinaturas distintas de vizinhanca.

Tambem exporta a planilha completa (um vertice por linha) em CSV.

Uso:
    python planilha.py            # malha 10x10 (padrao)
    python planilha.py 6 6        # malha 6x6
"""
import sys
from collections import Counter

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from cloth import Cloth
from spring import SpringType

ROWS = int(sys.argv[1]) if len(sys.argv) > 1 else 10
COLS = int(sys.argv[2]) if len(sys.argv) > 2 else 10

cloth = Cloth()
cloth.build_grid(ROWS, COLS)  # so a vizinhanca importa aqui; geometria e indiferente
csv_path = cloth.export_reference_table("vizinhanca.csv")

TIPO_COR = {"interno": "#4a90d9", "borda": "#ff9f40", "canto": "#d94a4a"}
SPRING_COR = {
    SpringType.STRUCTURAL: "#1f77b4",
    SpringType.SHEAR: "#2ca02c",
    SpringType.BENDING: "#ff7f0e",
}
SPRING_NOME = {
    SpringType.STRUCTURAL: "estrutural",
    SpringType.SHEAR: "cisalhamento",
    SpringType.BENDING: "flexao",
}


def counts(v):
    return (len(v.neighbors[SpringType.STRUCTURAL]),
            len(v.neighbors[SpringType.SHEAR]),
            len(v.neighbors[SpringType.BENDING]))


# --- Agregacao: assinaturas distintas de vizinhanca (a planilha resumida) ---
assinaturas = Counter()
for v in cloth.vertices:
    e, s, b = counts(v)
    assinaturas[(v.tipo, e, s, b)] += 1

ordem = {"canto": 0, "borda": 1, "interno": 2}
linhas = sorted(assinaturas.items(),
                key=lambda kv: (ordem[kv[0][0]], -(kv[0][1] + kv[0][2] + kv[0][3])))

print("== Planilha de vizinhanca (assinaturas distintas) ==")
print(f"{'tipo':>8} {'estrut':>6} {'cisalh':>6} {'flexao':>6} {'total':>5} {'qtd':>4}")
table_rows = []
for (tipo, e, s, b), n in linhas:
    print(f"{tipo:>8} {e:>6} {s:>6} {b:>6} {e + s + b:>5} {n:>4}")
    table_rows.append([tipo, e, s, b, e + s + b, n])
print(f"\nPlanilha por vertice (CSV): {csv_path}")


def representative(tipo):
    """Vertice 'tipico' do tipo: o que tem mais vizinhos (caso canonico)."""
    cand = [v for v in cloth.vertices if v.tipo == tipo]
    max_tot = max(sum(counts(v)) for v in cand)
    melhores = [v for v in cand if sum(counts(v)) == max_tot]
    return melhores[len(melhores) // 2]


def draw_type_map(ax):
    for tipo, cor in TIPO_COR.items():
        pts = np.array([v.position[:2] for v in cloth.vertices if v.tipo == tipo])
        if len(pts):
            ax.scatter(pts[:, 0], pts[:, 1], s=60, color=cor, label=tipo,
                       edgecolors="white", linewidths=0.5)
    ax.set_title("Mapa de tipos de vertice")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=8, loc="upper right")


def draw_neighborhood(ax, v):
    P = np.array([w.position[:2] for w in cloth.vertices])
    ax.scatter(P[:, 0], P[:, 1], s=10, color="#dddddd", zorder=1)
    for stype, cor in SPRING_COR.items():
        for w in v.neighbors[stype]:
            ax.plot([v.position[0], w.position[0]],
                    [v.position[1], w.position[1]],
                    "-", color=cor, lw=2, zorder=2)
            ax.scatter(w.position[0], w.position[1], s=45, color=cor,
                       zorder=3, edgecolors="white", linewidths=0.5)
    ax.scatter(v.position[0], v.position[1], s=110, color="black", zorder=4)
    e, s, b = counts(v)
    ax.set_title(f"Vizinhanca: {v.tipo} (i={v.i}, j={v.j})  ->  "
                 f"{e}+{s}+{b}={e + s + b}")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2)


# --- Figura 1: mapa de tipos + diagramas de vizinhanca ---
fig1, axes = plt.subplots(2, 2, figsize=(11, 11))
draw_type_map(axes[0, 0])
draw_neighborhood(axes[0, 1], representative("canto"))
draw_neighborhood(axes[1, 0], representative("borda"))
draw_neighborhood(axes[1, 1], representative("interno"))
handles = [Line2D([0], [0], color=SPRING_COR[t], lw=3, label=SPRING_NOME[t])
           for t in SPRING_COR]
fig1.legend(handles=handles, loc="lower center", ncol=3, fontsize=10)
fig1.suptitle(f"Planilha de vizinhanca - malha {ROWS}x{COLS}", fontsize=14)
fig1.tight_layout(rect=[0, 0.04, 1, 0.97])
fig1.savefig("planilha_diagramas.png", dpi=80)

# --- Figura 2: tabela renderizada ---
fig2, ax2 = plt.subplots(figsize=(8, 1.0 + 0.45 * len(table_rows)))
ax2.axis("off")
tab = ax2.table(
    cellText=table_rows,
    colLabels=["tipo", "estrutural", "cisalhamento", "flexao",
               "total", "qtd vertices"],
    loc="center", cellLoc="center",
)
tab.auto_set_font_size(False)
tab.set_fontsize(10)
tab.scale(1, 1.6)
for r, row in enumerate(table_rows, start=1):
    tab[(r, 0)].set_facecolor(TIPO_COR[row[0]])
    tab[(r, 0)].set_text_props(color="white")
ax2.set_title("Planilha de vizinhanca (assinaturas distintas)", fontsize=13)
fig2.tight_layout()
fig2.savefig("planilha_tabela.png", dpi=90)

if __name__ == "__main__":
    plt.show()
