import csv

import numpy as np

from vertex import Vertex
from spring import Spring, SpringType


# ---------------------------------------------------------------------------
# Vizinhanca canonica (i = linha, j = coluna). Fonte unica de verdade:
# tanto a criacao das molas quanto a classificacao dos vertices derivam daqui.
# ---------------------------------------------------------------------------
STRUCTURAL_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1)]      # cima/baixo/esq/dir
SHEAR_OFFSETS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]         # 4 diagonais
BENDING_OFFSETS = [(-2, 0), (2, 0), (0, -2), (0, 2)]         # a 2 celulas

OFFSETS_BY_TYPE = {
    SpringType.STRUCTURAL: STRUCTURAL_OFFSETS,
    SpringType.SHEAR: SHEAR_OFFSETS,
    SpringType.BENDING: BENDING_OFFSETS,
}

# Offsets "para frente": cada mola e criada uma unica vez (evita duplicatas).
FORWARD_OFFSETS_BY_TYPE = {
    SpringType.STRUCTURAL: [(0, 1), (1, 0)],
    SpringType.SHEAR: [(1, 1), (1, -1)],
    SpringType.BENDING: [(0, 2), (2, 0)],
}

GRAVITY = np.array([0.0, -9.81, 0.0])


class Cloth:
    def __init__(self):
        self.vertices = []
        self.springs = []
        self.rows = 0
        self.cols = 0
        self.spacing = 1.0

    # ---- utilidades de indexacao da malha ---------------------------------
    def index(self, i, j):
        return i * self.cols + j

    def in_bounds(self, i, j):
        return 0 <= i < self.rows and 0 <= j < self.cols

    def classify(self, i, j):
        """Classifica o vertice pela quantidade de bordas que ele toca."""
        bordas = sum([i == 0, i == self.rows - 1, j == 0, j == self.cols - 1])
        return {2: "canto", 1: "borda"}.get(bordas, "interno")

    # ---- construcao da malha ----------------------------------------------
    def build_grid(self, rows, cols, spacing=1.0,
                   stiffness=80.0, damping=0.8, mass=1.0):
        self.rows = rows
        self.cols = cols
        self.spacing = spacing

        # Massa concentrada (lumped mass) proporcional a area que o vertice
        # representa: interno = 1 celula, borda = 1/2, canto = 1/4.
        area_mass = {"interno": mass, "borda": mass / 2.0, "canto": mass / 4.0}

        for i in range(rows):
            for j in range(cols):
                position = [j * spacing, -i * spacing, 0.0]
                fixed = (i == 0)  # primeira linha presa
                tipo = self.classify(i, j)

                vertex = Vertex(
                    id=len(self.vertices),
                    position=position,
                    mass=area_mass[tipo],
                    fixed=fixed,
                    i=i,
                    j=j,
                )
                vertex.tipo = tipo
                self.vertices.append(vertex)

        self.build_springs(stiffness, damping)
        self.build_neighborhoods()

    def build_springs(self, stiffness, damping):
        for i in range(self.rows):
            for j in range(self.cols):
                for stype, offsets in FORWARD_OFFSETS_BY_TYPE.items():
                    for di, dj in offsets:
                        ni, nj = i + di, j + dj
                        if self.in_bounds(ni, nj):
                            self.springs.append(Spring(
                                self.vertices[self.index(i, j)],
                                self.vertices[self.index(ni, nj)],
                                stiffness,
                                damping,
                                stype,
                            ))

    def build_neighborhoods(self):
        """Preenche, para cada vertice, a vizinhanca por tipo de mola.

        A verificacao de limites resolve automaticamente vertices internos,
        de borda e de canto: cada um fica apenas com os vizinhos validos.
        """
        for i in range(self.rows):
            for j in range(self.cols):
                v = self.vertices[self.index(i, j)]
                v.neighbors = {}
                for stype, offsets in OFFSETS_BY_TYPE.items():
                    v.neighbors[stype] = [
                        self.vertices[self.index(i + di, j + dj)]
                        for di, dj in offsets
                        if self.in_bounds(i + di, j + dj)
                    ]

    # ---- dinamica ---------------------------------------------------------
    def compute_forces(self):
        for vertex in self.vertices:
            vertex.reset_forces()
            if not vertex.fixed:
                vertex.forces["gravidade"] += GRAVITY * vertex.mass

        for spring in self.springs:
            spring.apply_force()

    def integrate(self, dt, metodo="explicito"):
        """Integracao numerica.

        metodo="explicito"  -> Euler explicito (forward): a posicao usa a
                               velocidade ANTIGA. Conforme o enunciado.
        metodo="semi"       -> Euler semi-implicito (Euler-Cromer): a posicao
                               usa a velocidade JA atualizada. Mais estavel.
        """
        for vertex in self.vertices:
            if vertex.fixed:
                continue

            vertex.acceleration = vertex.force_total / vertex.mass

            if metodo == "explicito":
                vertex.position = vertex.position + vertex.velocity * dt
                vertex.velocity = vertex.velocity + vertex.acceleration * dt
            else:
                vertex.velocity = vertex.velocity + vertex.acceleration * dt
                vertex.position = vertex.position + vertex.velocity * dt

    def update(self, dt, metodo="explicito"):
        self.compute_forces()
        self.integrate(dt, metodo)

    # ---- planilha de referencia (item 6) ----------------------------------
    def export_reference_table(self, path="vizinhanca.csv"):
        """Gera a tabela de vizinhanca (vertice x tipo x vizinhos) em CSV,
        para comparacao direta com a planilha de referencia do projeto."""
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id", "i", "j", "tipo",
                        "n_estrutural", "n_cisalhamento", "n_flexao", "total"])
            for v in self.vertices:
                e = len(v.neighbors[SpringType.STRUCTURAL])
                s = len(v.neighbors[SpringType.SHEAR])
                b = len(v.neighbors[SpringType.BENDING])
                w.writerow([v.id, v.i, v.j, v.tipo, e, s, b, e + s + b])
        return path
