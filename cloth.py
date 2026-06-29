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

# ---------------------------------------------------------------------------
# Parametros fisicos da Simulacao 1 da dissertacao (Carvalho, 2012, Tab. 5.1).
# Sao "todos os parametros dela" -- usados por padrao em build_grid.
# ---------------------------------------------------------------------------
# Rigidez das molas por tipo (k, N/m). Estruturais bem mais rigidas para
# evitar superelasticidade (Secao 4.3); flexao quase nula.
STIFFNESS_BY_TYPE = {
    SpringType.STRUCTURAL: 2000.0,
    SpringType.SHEAR: 100.0,
    SpringType.BENDING: 0.001,
}

# Coeficiente de amortecimento das molas por tipo (k^d, N*s/m).
DAMPING_BY_TYPE = {
    SpringType.STRUCTURAL: 2.0,
    SpringType.SHEAR: 1.0,
    SpringType.BENDING: 0.001,
}

# Coeficiente de arrasto do ar (C^res) por tipo de particula.
AIR_DRAG_BY_TIPO = {
    "canto": 0.005,
    "borda": 0.01,
    "interno": 0.02,
}

DENSITY = 2050.0     # densidade do tecido (rho), kg/m^3
THICKNESS = 0.0001   # espessura do tecido (epsilon), m
CLOTH_SIZE = 2.0     # tecido quadrado de 2 m x 2 m

# Z e o eixo vertical (tecido na horizontal, cai em -Z), conforme Figura 5.1.
GRAVITY = np.array([0.0, 0.0, -9.81])


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
    def build_grid(self, rows, cols, cloth_size=CLOTH_SIZE,
                   stiffness_by_type=None, damping_by_type=None,
                   air_drag_by_tipo=None, density=DENSITY, thickness=THICKNESS,
                   fixed_points=None):
        """Monta a Simulacao 1 da dissertacao: tecido quadrado de
        ``cloth_size`` m na horizontal (plano XY), discretizado em rows x cols,
        preso em ``fixed_points`` e caindo apenas pela gravidade (em -Z).

        Sem ``fixed_points``, prende os dois cantos do mesmo lado (a aresta do
        topo): (0, 0) e (0, cols-1).
        """
        self.rows = rows
        self.cols = cols
        # Grade regular: o tecido de lado ``cloth_size`` e dividido em
        # (n-1) intervalos, logo o espacamento entre vertices e size/(n-1).
        spacing = cloth_size / (max(rows, cols) - 1)
        self.spacing = spacing

        stiffness_by_type = stiffness_by_type or STIFFNESS_BY_TYPE
        damping_by_type = damping_by_type or DAMPING_BY_TYPE
        air_drag_by_tipo = air_drag_by_tipo or AIR_DRAG_BY_TIPO

        if fixed_points is None:
            fixed_points = {(0, 0), (0, cols - 1)}  # dois cantos do mesmo lado
        else:
            fixed_points = set(fixed_points)

        # Massa por area de influencia (Eqs. 4.7-4.8): m = rho * epsilon * A.
        # Em malha regular A vale uma celula no interno, metade na borda e um
        # quarto no canto.
        cell_area = spacing * spacing
        base_mass = density * thickness * cell_area
        area_mass = {"interno": base_mass,
                     "borda": base_mass / 2.0,
                     "canto": base_mass / 4.0}

        for i in range(rows):
            for j in range(cols):
                # Tecido na horizontal: ocupa o plano XY em z = 0.
                position = [j * spacing, i * spacing, 0.0]
                tipo = self.classify(i, j)
                fixed = (i, j) in fixed_points

                vertex = Vertex(
                    id=len(self.vertices),
                    position=position,
                    mass=area_mass[tipo],
                    fixed=fixed,
                    i=i,
                    j=j,
                )
                vertex.tipo = tipo
                vertex.air_drag = air_drag_by_tipo[tipo]
                self.vertices.append(vertex)

        self.build_springs(stiffness_by_type, damping_by_type)
        self.build_neighborhoods()

    def build_springs(self, stiffness_by_type, damping_by_type):
        for i in range(self.rows):
            for j in range(self.cols):
                for stype, offsets in FORWARD_OFFSETS_BY_TYPE.items():
                    for di, dj in offsets:
                        ni, nj = i + di, j + dj
                        if self.in_bounds(ni, nj):
                            self.springs.append(Spring(
                                self.vertices[self.index(i, j)],
                                self.vertices[self.index(ni, nj)],
                                stiffness_by_type[stype],
                                damping_by_type[stype],
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
                # Gravidade (Eq. 4.4) e resistencia do ar (Eq. 4.5):
                # f^res = -C^res * v.
                vertex.forces["gravidade"] += GRAVITY * vertex.mass
                vertex.forces["ar"] += -vertex.air_drag * vertex.velocity

        for spring in self.springs:
            spring.apply_force()

    def integrate(self, dt, metodo="explicito"):
        """Integracao numerica.

        metodo="explicito"  -> Euler explicito (forward): a posicao usa a
                               velocidade ANTIGA. Conforme o enunciado.
        metodo="semi"       -> Euler semi-implicito (Euler-Cromer): a posicao
                               usa a velocidade JA atualizada. Mais estavel.
        metodo="kangcho"    -> Euler implicito resolvido pelo esquema iterativo
                               de Jacobi com uma unica iteracao (Kang e Cho,
                               2004 -- Secao 4.2.2.1 da dissertacao).
        """
        if metodo == "kangcho":
            self.integrate_kangcho(dt)
            return

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

    def integrate_kangcho(self, dt):
        """Euler implicito resolvido pelo metodo de Kang e Cho (2004).

        O passo implicito leva ao sistema linear esparso (Eq. 4.25)

            (M - dt^2 * df/dx - dt * df/dv) * dv = dt * (f + dt * df/dx * v),

        que Kang e Cho decompoem em m equacoes 3x3 (uma por particula) e
        resolvem com o esquema iterativo de Jacobi. Como apontado pelos
        autores, **uma unica iteracao** ja gera solucoes estaveis e plausiveis
        (Eq. 4.31). O algoritmo aqui implementado e exatamente esse:

          1. monta, por particula i, o bloco diagonal 3x3
                 A_ii = m_i*I + dt*C^res_i*I + sum_j (dt^2*J_ij + dt*D_ij)
             e o lado direito  b_i = dt * f~_i, onde
                 f~_i = f_i + dt * sum_j J_ij (v_j - v_i)   (Eq. 4.26);
          2. estimativa inicial   p_i = A_ii^{-1} b_i        (dv_i^0);
          3. uma iteracao de Jacobi:
                 dv_i = A_ii^{-1} ( b_i + sum_j (dt^2*J_ij + dt*D_ij) p_j );
          4. v_i <- v_i + dv_i ;  x_i <- x_i + dt * v_i .

        J_ij e D_ij sao os blocos de Spring.jacobians(). Note que o bloco de
        acoplamento (dt^2*J + dt*D) e o mesmo que entra na diagonal -- por isso
        e calculado uma so vez por mola.

        Esta versao e vetorizada com NumPy (todas as molas/particulas de uma
        vez), o que e ~30x mais rapido que o laco em Python. A matematica e a
        mesma; cada bloco abaixo corresponde a um passo da lista acima.
        """
        self._ensure_kangcho_arrays()
        h = dt
        I3 = np.eye(3)
        a, b = self._kc_a, self._kc_b            # ids dos extremos de cada mola
        k, c, L = self._kc_k, self._kc_c, self._kc_L

        # Estado atual em arrays (n, 3): posicao, velocidade e forca total.
        P = np.array([v.position for v in self.vertices])
        Vv = np.array([v.velocity for v in self.vertices])
        F = np.array([v.force_total for v in self.vertices])

        # --- Jacobianas por mola (Eqs. 4.33-4.35), todas de uma vez ---
        d = P[a] - P[b]                          # (m,3)  d = x_a - x_b
        r2 = np.einsum("mi,mi->m", d, d)         # (m,)   ||d||^2
        r2 = np.where(r2 == 0.0, 1.0, r2)        # guarda contra divisao por 0
        r = np.sqrt(r2)
        outer = np.einsum("mi,mj->mij", d, d) / r2[:, None, None]   # d d^T / r^2
        J = k[:, None, None] * (I3 - (L / r)[:, None, None] * (I3 - outer))  # df/dx
        D = c[:, None, None] * outer                                # df^d/dv
        blk = (h * h) * J + h * D                 # bloco de acoplamento (m,3,3)

        # --- (1) bloco diagonal A_ii (n,3,3) e lado direito b_i = dt*f~_i ---
        A = (self._kc_mass + h * self._kc_air)[:, None, None] * I3  # massa + ar
        np.add.at(A, a, blk)                      # soma blk em A[a] e A[b]
        np.add.at(A, b, blk)

        f_tilde = F.copy()
        contrib = h * np.einsum("mij,mj->mi", J, Vv[b] - Vv[a])     # dt*J*(v_b-v_a)
        np.add.at(f_tilde, a, contrib)
        np.add.at(f_tilde, b, -contrib)
        rhs0 = h * f_tilde

        # Inverte os blocos 3x3 em lote (rapido). Particulas fixas: dv = 0.
        Ainv = np.linalg.inv(A)                   # (n,3,3)
        free = self._kc_free

        # --- (2) estimativa inicial dv^0 = A_ii^{-1} b_i (Eq. 4.31) ---
        p = np.einsum("nij,nj->ni", Ainv, rhs0)
        p[~free] = 0.0

        # --- (3) uma iteracao de Jacobi: soma a influencia dos vizinhos ---
        rhs = rhs0.copy()
        np.add.at(rhs, a, np.einsum("mij,mj->mi", blk, p[b]))
        np.add.at(rhs, b, np.einsum("mij,mj->mi", blk, p[a]))
        dv = np.einsum("nij,nj->ni", Ainv, rhs)
        dv[~free] = 0.0

        # --- (4) atualiza v e x (somente nas particulas livres) ---
        Vv = Vv + dv
        P = P + h * Vv
        for idx, v in enumerate(self.vertices):
            if free[idx]:
                v.velocity = Vv[idx]
                v.position = P[idx]

    def _ensure_kangcho_arrays(self):
        """Pre-computa, uma unica vez, os arrays estaticos (topologia das molas,
        massas, arrasto e quais particulas sao livres) usados na versao
        vetorizada de integrate_kangcho. Nada disso muda durante a simulacao."""
        if getattr(self, "_kc_ready", False):
            return
        self._kc_a = np.array([s.v1.id for s in self.springs])
        self._kc_b = np.array([s.v2.id for s in self.springs])
        self._kc_k = np.array([s.stiffness for s in self.springs])
        self._kc_c = np.array([s.damping for s in self.springs])
        self._kc_L = np.array([s.rest_length for s in self.springs])
        self._kc_mass = np.array([v.mass for v in self.vertices])
        self._kc_air = np.array([v.air_drag for v in self.vertices])
        self._kc_free = np.array([not v.fixed for v in self.vertices])
        self._kc_ready = True

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
