import numpy as np

from cloth import (Cloth, GRAVITY, STIFFNESS_BY_TYPE, DAMPING_BY_TYPE,
                   AIR_DRAG_BY_TIPO, DENSITY, THICKNESS, CLOTH_SIZE)
from spring import SpringType

# ---------------------------------------------------------------------------
# Demonstracao da Simulacao 1 da dissertacao (Carvalho, 2012):
#   tecido quadrado de 2 m x 2 m, grade 10x10, na horizontal, preso em dois
#   cantos opostos e caindo apenas pela gravidade. Integracao pelo metodo
#   implicito de Euler de Kang e Cho (Secao 4.2.2.1).
# ---------------------------------------------------------------------------
ROWS, COLS = 10, 10

# Passos de tempo da Tabela 5.x: o implicito de Kang e Cho admite passo 10x
# maior que o explicito (0,002 s vs 0,0002 s).
DT_KANGCHO = 0.002
DT_EXPLICITO = 0.0002

cloth = Cloth()
cloth.build_grid(ROWS, COLS)  # usa todos os parametros da Tabela 5.1

# ---- Parametros fisicos em uso (Tabela 5.1) -------------------------------
print("== Parametros fisicos (Simulacao 1, Tabela 5.1) ==")
print(f"  tecido            : {CLOTH_SIZE} m x {CLOTH_SIZE} m, grade {ROWS}x{COLS}, "
      f"espacamento {cloth.spacing:.4f} m")
print(f"  densidade (rho)   : {DENSITY} kg/m^3   espessura (eps): {THICKNESS} m")
print(f"  massa total       : {sum(v.mass for v in cloth.vertices):.4f} kg "
      f"(= rho * eps * area)")
print(f"  rigidez (k)       : estrut={STIFFNESS_BY_TYPE[SpringType.STRUCTURAL]}  "
      f"cis={STIFFNESS_BY_TYPE[SpringType.SHEAR]}  "
      f"flex={STIFFNESS_BY_TYPE[SpringType.BENDING]} N/m")
print(f"  amortecimento (kd): estrut={DAMPING_BY_TYPE[SpringType.STRUCTURAL]}  "
      f"cis={DAMPING_BY_TYPE[SpringType.SHEAR]}  "
      f"flex={DAMPING_BY_TYPE[SpringType.BENDING]} N*s/m")
print(f"  arrasto do ar     : canto={AIR_DRAG_BY_TIPO['canto']}  "
      f"borda={AIR_DRAG_BY_TIPO['borda']}  interno={AIR_DRAG_BY_TIPO['interno']}")
print(f"  gravidade (g)     : ({GRAVITY[0]:g}, {GRAVITY[1]:g}, {GRAVITY[2]:g}) m/s^2")
fixos = [(v.i, v.j) for v in cloth.vertices if v.fixed]
print(f"  pontos fixos      : {fixos}")

# ---- Vizinhanca por tipo de vertice + planilha (itens 2, 5 e 6) -----------
print("\n== Vizinhanca por tipo de vertice (amostra) ==")
print(f"{'id':>4} {'i':>3} {'j':>3} {'tipo':>8} "
      f"{'estr':>5} {'cis':>4} {'flex':>5} {'tot':>4}")
for (i, j) in [(0, 0), (0, 5), (5, 0), (1, 1), (5, 5)]:
    v = cloth.vertices[cloth.index(i, j)]
    e = len(v.neighbors[SpringType.STRUCTURAL])
    s = len(v.neighbors[SpringType.SHEAR])
    b = len(v.neighbors[SpringType.BENDING])
    print(f"{v.id:>4} {v.i:>3} {v.j:>3} {v.tipo:>8} "
          f"{e:>5} {s:>4} {b:>5} {e + s + b:>4}")

path = cloth.export_reference_table("vizinhanca.csv")
print(f"\n-> Planilha de vizinhanca exportada para '{path}' "
      f"({len(cloth.vertices)} vertices, {len(cloth.springs)} molas)")

# ---- Simulacao: Euler implicito de Kang e Cho -----------------------------
print(f"\n== Simulacao: Euler implicito (Kang e Cho) | dt={DT_KANGCHO} ==")
PASSOS = 2500  # ~5 s de simulacao: tempo de sobra para o tecido assentar
for passo in range(1, PASSOS + 1):
    cloth.update(DT_KANGCHO, metodo="kangcho")
    if passo % 500 == 0 or passo == PASSOS:
        z = np.array([v.position[2] for v in cloth.vertices])
        print(f"  passo {passo:>4}/{PASSOS}  t={passo * DT_KANGCHO:5.2f}s  "
              f"z_min={z.min():.4f} m")

P = np.array([v.position for v in cloth.vertices])
estir = max(np.linalg.norm(s.v1.position - s.v2.position) / s.rest_length
            for s in cloth.springs if s.type == SpringType.STRUCTURAL)
print(f"  apos {PASSOS} passos (t={PASSOS * DT_KANGCHO:.2f}s): "
      f"z em [{P[:, 2].min():.3f}, {P[:, 2].max():.3f}] m, "
      f"estiramento estrutural maximo = {estir:.3f}x")

# ---- Decomposicao das forcas em um vertice (item 1) -----------------------
v = cloth.vertices[cloth.index(5, 5)]
print(f"\nDecomposicao das forcas no vertice {v.id} "
      f"(i={v.i}, j={v.j}, tipo={v.tipo}) -- componentes (x, y, z):")
for nome, f in v.forces.items():
    print(f"  {nome:>13}: {f.round(5)}")
print(f"  {'TOTAL':>13}: {v.force_total.round(5)}")
print(f"\nPosicao final do vertice {v.id}: {v.position.round(4)}")

print("\nVisualizacao (animacao 3D):")
print("  python visualize.py            -> Kang e Cho (implicito, dt=0,002)")
print("  python visualize.py explicito  -> Euler explicito (dt=0,0002, p/ comparar)")
print("  python visualize.py semi       -> Euler semi-implicito")
