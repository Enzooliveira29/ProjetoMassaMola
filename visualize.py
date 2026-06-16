import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from cloth import Cloth

# Modos via linha de comando:
#   forces / forcas -> desenha os vetores de forca por vertice
#   semi            -> usa Euler semi-implicito (padrao: explicito)
mode = set(arg.lower() for arg in sys.argv[1:])
SHOW_FORCES = ("forces" in mode) or ("forcas" in mode)
METODO = "semi" if "semi" in mode else "explicito"

# --- Monta o tecido ---
cloth = Cloth()
cloth.build_grid(rows=10, cols=10, spacing=0.1, stiffness=80.0, damping=0.8)

DT = 0.005
SUBSTEPS = 4  # passos de fisica por quadro

# --- Figura ---
fig, ax = plt.subplots(figsize=(7, 7))
ax.set_aspect("equal")
titulo = f"Tecido massa-mola | integracao: {METODO}"
if SHOW_FORCES:
    titulo += " | forcas: ON"
ax.set_title(titulo)
ax.set_xlim(-0.4, 1.4)
ax.set_ylim(-1.7, 0.3)
ax.grid(True, alpha=0.2)

# Molas
spring_lines = [ax.plot([], [], "-", color="#4a90d9", lw=0.7, alpha=0.5)[0]
                for _ in cloth.springs]
# Vertices
free_pts, = ax.plot([], [], "o", color="#d94a4a", ms=4, label="livre")
fixed_pts, = ax.plot([], [], "s", color="#333333", ms=6, label="fixo")

quiv_grav = quiv_spring = None
if SHOW_FORCES:
    P = np.array([v.position[:2] for v in cloth.vertices])
    zeros = np.zeros(len(cloth.vertices))
    quiv_grav = ax.quiver(P[:, 0], P[:, 1], zeros, zeros, color="#2ca02c",
                          angles="xy", scale_units="xy", scale=120,
                          width=0.003, label="gravidade")
    quiv_spring = ax.quiver(P[:, 0], P[:, 1], zeros, zeros, color="#ff7f0e",
                            angles="xy", scale_units="xy", scale=120,
                            width=0.003, label="molas")

ax.legend(loc="upper right", fontsize=8)


def update(frame):
    for _ in range(SUBSTEPS):
        cloth.update(DT, metodo=METODO)

    for line, s in zip(spring_lines, cloth.springs):
        line.set_data([s.v1.position[0], s.v2.position[0]],
                      [s.v1.position[1], s.v2.position[1]])

    free = np.array([v.position[:2] for v in cloth.vertices if not v.fixed])
    fixed = np.array([v.position[:2] for v in cloth.vertices if v.fixed])
    free_pts.set_data(free[:, 0], free[:, 1])
    fixed_pts.set_data(fixed[:, 0], fixed[:, 1])

    artists = spring_lines + [free_pts, fixed_pts]

    if SHOW_FORCES:
        P = np.array([v.position[:2] for v in cloth.vertices])
        G = np.array([v.forces["gravidade"][:2] for v in cloth.vertices])
        S = np.array([(v.forces["estrutural"] + v.forces["cisalhamento"]
                       + v.forces["flexao"] + v.forces["amortecimento"])[:2]
                      for v in cloth.vertices])
        quiv_grav.set_offsets(P)
        quiv_grav.set_UVC(G[:, 0], G[:, 1])
        quiv_spring.set_offsets(P)
        quiv_spring.set_UVC(S[:, 0], S[:, 1])
        artists += [quiv_grav, quiv_spring]

    ax.set_xlabel(f"Quadro {frame}")
    return artists


anim = FuncAnimation(fig, update, frames=600, interval=20, blit=False)

if __name__ == "__main__":
    plt.show()
