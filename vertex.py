import numpy as np

# Componentes em que a forca resultante sobre o vertice e decomposta.
# Permite analisar a contribuicao individual da gravidade, da resistencia
# do ar e de cada tipo de mola (item 1 das proximas etapas).
FORCE_COMPONENTS = (
    "gravidade",
    "estrutural",
    "cisalhamento",
    "flexao",
    "amortecimento",
    "ar",
)


class Vertex:
    def __init__(self, id, position, mass=1.0, fixed=False, i=None, j=None):
        self.id = id

        # Coordenadas na malha (linha, coluna) e classificacao do vertice
        # ("interno" | "borda" | "canto"), definida por Cloth.
        self.i = i
        self.j = j
        self.tipo = None

        self.position = np.array(position, dtype=float)
        self.velocity = np.zeros(3)
        self.acceleration = np.zeros(3)

        self.mass = mass
        self.fixed = fixed

        # Coeficiente de arrasto do ar (C^res, Eq. 4.5). Depende do tipo do
        # vertice (canto/borda/interno) e e definido por Cloth.build_grid.
        self.air_drag = 0.0

        # Vizinhanca por tipo de mola (preenchida por Cloth.build_neighborhoods).
        self.neighbors = {}

        # Decomposicao das forcas que atuam sobre o vertice.
        self.forces = {name: np.zeros(3) for name in FORCE_COMPONENTS}

    def reset_forces(self):
        for name in self.forces:
            self.forces[name][:] = 0.0

    @property
    def force_total(self):
        total = np.zeros(3)
        for f in self.forces.values():
            total += f
        return total
