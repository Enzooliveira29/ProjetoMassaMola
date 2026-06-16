from cloth import Cloth
from spring import SpringType

# ---------------------------------------------------------------------------
# Demonstracao das etapas implementadas no simulador massa-mola.
# ---------------------------------------------------------------------------
ROWS, COLS, SPACING = 10, 10, 0.1
STIFFNESS, DAMPING, DT = 80.0, 0.8, 0.005

cloth = Cloth()
cloth.build_grid(ROWS, COLS, spacing=SPACING,
                 stiffness=STIFFNESS, damping=DAMPING)

# ---- Itens 2, 5 e 6: vizinhanca, tipos de vertice e planilha --------------
print("== Vizinhanca por tipo de vertice (amostra) ==")
print(f"{'id':>4} {'i':>3} {'j':>3} {'tipo':>8} "
      f"{'estr':>5} {'cis':>4} {'flex':>5} {'tot':>4}")

amostra = [(0, 0), (0, 5), (5, 0), (1, 1), (5, 5)]
for (i, j) in amostra:
    v = cloth.vertices[cloth.index(i, j)]
    e = len(v.neighbors[SpringType.STRUCTURAL])
    s = len(v.neighbors[SpringType.SHEAR])
    b = len(v.neighbors[SpringType.BENDING])
    print(f"{v.id:>4} {v.i:>3} {v.j:>3} {v.tipo:>8} "
          f"{e:>5} {s:>4} {b:>5} {e + s + b:>4}")

path = cloth.export_reference_table("vizinhanca.csv")
print(f"\n-> Planilha de vizinhanca exportada para '{path}' "
      f"({len(cloth.vertices)} vertices, {len(cloth.springs)} molas)")

# ---- Itens 3 e 4: integracao (Euler explicito) + amortecimento ------------
print(f"\n== Simulacao: Euler explicito | dt={DT}, k={STIFFNESS}, c={DAMPING} "
      f"(estavel se dt <= c/k = {DAMPING / STIFFNESS:.4f}) ==")
PASSOS = 300
for _ in range(PASSOS):
    cloth.update(DT, metodo="explicito")

# ---- Item 1: decomposicao das forcas em um vertice ------------------------
v = cloth.vertices[cloth.index(5, 5)]
print(f"\nDecomposicao das forcas no vertice {v.id} "
      f"(i={v.i}, j={v.j}, tipo={v.tipo}) apos {PASSOS} passos (componentes x,y):")
for nome, f in v.forces.items():
    print(f"  {nome:>13}: {f[:2].round(4)}")
print(f"  {'TOTAL':>13}: {v.force_total[:2].round(4)}")
print(f"\nPosicao final do vertice {v.id}: {v.position.round(4)}")

print("\nVisualizacao:")
print("  python visualize.py          -> animacao do tecido")
print("  python visualize.py forces   -> animacao com vetores de forca")
print("  python visualize.py semi     -> usa Euler semi-implicito (comparacao)")
