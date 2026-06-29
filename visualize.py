import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d.art3d import Line3DCollection

from cloth import Cloth, CLOTH_SIZE

# ---------------------------------------------------------------------------
# Animacao 3D da Simulacao 1 (Figura 5.1 da dissertacao): tecido horizontal de
# 2 m x 2 m preso em dois cantos opostos, caindo pela gravidade.
#
# Metodo de integracao via linha de comando:
#   (padrao)   -> Euler implicito de Kang e Cho (dt = 0,002 s)
#   explicito  -> Euler explicito              (dt = 0,0002 s)
#   semi       -> Euler semi-implicito         (dt = 0,002 s)
# ---------------------------------------------------------------------------
mode = set(arg.lower() for arg in sys.argv[1:])
if "explicito" in mode or "explicit" in mode:
    METODO, DT, SUBSTEPS = "explicito", 0.0002, 60
elif "semi" in mode:
    METODO, DT, SUBSTEPS = "semi", 0.002, 6
else:
    METODO, DT, SUBSTEPS = "kangcho", 0.002, 6

NOMES = {"kangcho": "Euler implicito (Kang e Cho)",
         "explicito": "Euler explicito",
         "semi": "Euler semi-implicito"}

# --- Monta o tecido com os parametros da Tabela 5.1 ---
cloth = Cloth()
cloth.build_grid(rows=10, cols=10)

# Pares de indices de cada mola (para montar os segmentos a cada quadro).
spring_pairs = [(s.v1.id, s.v2.id) for s in cloth.springs]

# --- Figura 3D ---
fig = plt.figure(figsize=(8, 7))
ax = fig.add_subplot(111, projection="3d")
ax.set_title(f"Tecido massa-mola 3D | {NOMES[METODO]} | dt={DT}")
ax.set_xlabel("x (m)")
ax.set_ylabel("y (m)")
ax.set_zlabel("z (m)")
ax.set_xlim(0, CLOTH_SIZE)
ax.set_ylim(0, CLOTH_SIZE)
ax.set_zlim(-CLOTH_SIZE, 0.3)
ax.view_init(elev=22, azim=-60)
try:
    ax.set_box_aspect((1, 1, 1))  # mesma escala nos tres eixos
except Exception:
    pass

# Estado inicial (tecido deitado em z = 0).
P = np.array([v.position for v in cloth.vertices])
free_idx = [v.id for v in cloth.vertices if not v.fixed]
fixed_idx = [v.id for v in cloth.vertices if v.fixed]

# Malha de molas como um unico Line3DCollection (rapido). Inicia ja com os
# segmentos do tecido -- nao pode comecar vazio (add_collection3d quebraria).
mesh = Line3DCollection([[P[a], P[b]] for (a, b) in spring_pairs],
                        colors="#4a90d9", linewidths=0.7, alpha=0.6)
ax.add_collection3d(mesh)

free = P[free_idx]
free_scatter = ax.scatter(free[:, 0], free[:, 1], free[:, 2],
                          c="#d94a4a", s=12, label="livre")
P0 = P[fixed_idx]
ax.scatter(P0[:, 0], P0[:, 1], P0[:, 2], c="#111111", s=60, marker="s",
           label="fixo (canto)")
ax.legend(loc="upper right", fontsize=8)


def update(frame):
    for _ in range(SUBSTEPS):
        cloth.update(DT, metodo=METODO)

    P = np.array([v.position for v in cloth.vertices])
    segments = [[P[a], P[b]] for (a, b) in spring_pairs]
    mesh.set_segments(segments)

    free = P[free_idx]
    free_scatter._offsets3d = (free[:, 0], free[:, 1], free[:, 2])

    ax.set_xlabel(f"x (m)   |   t = {frame * SUBSTEPS * DT:.2f} s")
    return mesh, free_scatter


anim = FuncAnimation(fig, update, frames=600, interval=20, blit=False)

if __name__ == "__main__":
    plt.show()
