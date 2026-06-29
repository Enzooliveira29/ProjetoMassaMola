# Simulador de Tecido — Modelo Massa-Mola

Simulação de um tecido (cloth) usando o modelo massa-mola: a malha é um
conjunto de vértices (massas) conectados por molas de três tipos
(estruturais, de cisalhamento e de flexão), sob ação da gravidade, da
resistência do ar e de amortecimento. A integração no tempo pode ser feita
por **Euler explícito**, **Euler semi-implícito** ou pelo **Euler implícito de
Kang e Cho** (2004).

O cenário padrão é a **Simulação 1** da dissertação de referência (Carvalho,
2012): tecido quadrado de **2 m × 2 m**, grade **10×10**, na **horizontal**,
preso em **dois cantos do mesmo lado** (a aresta do topo: (0,0) e (0,9)) e
caindo apenas pela gravidade (Figura 5.1).

## Etapas implementadas

| # | Objetivo | Onde |
|---|----------|------|
| 1 | Cálculo **e visualização** das forças por vértice (gravidade, ar e cada tipo de mola) | `vertex.py` (`forces`), `spring.py` |
| 2 | Vizinhança de cada vértice (estrutural, cisalhamento, flexão) | `cloth.py` (`OFFSETS_BY_TYPE`, `build_neighborhoods`) |
| 3 | Integração por **Euler explícito**, **semi-implícito** e **implícito (Kang e Cho)** | `cloth.py` (`integrate`, `integrate_kangcho`) |
| 4 | **Amortecimento** (damping) + **resistência do ar** | `spring.py` (`apply_force`), `cloth.py` (`compute_forces`) |
| 5 | Tipos de vértice: interno, borda e canto (vizinhanças, massa e arrasto distintos) | `cloth.py` (`classify`, massa por área) |
| 6 | **Planilha de referência** de vizinhança + visualização | `cloth.py` (`export_reference_table`), `planilha.py` |
| 7 | **Euler implícito de Kang e Cho** (Seção 4.2.2.1) + parâmetros físicos da Tabela 5.1 | `cloth.py` (`integrate_kangcho`), `spring.py` (`jacobians`) |

## Estrutura do projeto

```
vertex.py      Vértice: posição, velocidade, massa, tipo, vizinhança e
               decomposição das forças (gravidade / estrutural / cisalhamento
               / flexão / amortecimento).
spring.py      Mola (lei de Hooke + amortecimento) e os três tipos de mola.
cloth.py       Malha: construção, vizinhança, forças e integração numérica.
main.py        Demonstração no terminal (planilha + decomposição de forças).
visualize.py   Animação do tecido (com modo de vetores de força).
planilha.py    Gera e visualiza a planilha de vizinhança.
```

## Como executar

```bash
pip install -r requirements.txt

python main.py                 # demonstração no terminal (parâmetros + forças) + exporta vizinhanca.csv
python visualize.py            # animação 3D — Euler implícito de Kang e Cho (dt=0,002)
python visualize.py explicito  # animação 3D — Euler explícito (dt=0,0002, para comparação)
python visualize.py semi       # animação 3D — Euler semi-implícito
python planilha.py             # gera a planilha de vizinhança + visualizações
```

`planilha.py` produz:
- `vizinhanca.csv` — a planilha completa (um vértice por linha);
- `planilha_diagramas.png` — mapa de tipos de vértice + diagramas de vizinhança;
- `planilha_tabela.png` — tabela das assinaturas distintas de vizinhança.

## Planilha de vizinhança (resumo)

Contagem de vizinhos por tipo de vértice (malha suficientemente grande):

| Tipo | Estruturais | Cisalhamento | Flexão | Total |
|------|:-----------:|:------------:|:------:|:-----:|
| Interno | 4 | 4 | 4 | 12 |
| Borda   | 3 | 2 | 3 |  8 |
| Canto   | 2 | 1 | 2 |  5 |

> Observação: como as molas de flexão alcançam vértices a **duas** células de
> distância, vértices internos ou de borda situados a uma célula da margem têm
> menos molas de flexão (assinaturas 11, 10 e 7). A planilha gerada captura
> todas essas variações automaticamente.

## Parâmetros físicos (Tabela 5.1 da dissertação)

Todos os parâmetros da Simulação 1 estão centralizados em `cloth.py` e são
usados por padrão em `build_grid`:

| Parâmetro | Valor |
|-----------|-------|
| Densidade do tecido (ρ) | 2050 kg/m³ |
| Espessura do tecido (ε) | 0,0001 m |
| Rigidez das molas estruturais (k) | **2000 N/m** |
| Rigidez das molas de cisalhamento (k) | 100 N/m |
| Rigidez das molas de flexão (k) | 0,001 N/m |
| Amortecimento estrutural (kᵈ) | 2,0 N·s/m |
| Amortecimento de cisalhamento (kᵈ) | 1,0 N·s/m |
| Amortecimento de flexão (kᵈ) | 0,001 N·s/m |
| Arrasto do ar (Cʳᵉˢ): canto / borda / interno | 0,005 / 0,01 / 0,02 |
| Gravidade (g) | (0, 0, −9,81) m/s² |

A **massa de cada partícula** é obtida pela área da sua região de influência
(Eqs. 4.7–4.8): `m = ρ · ε · A`, com A = 1 célula no interior, ½ na borda e ¼
no canto. A massa total resulta exatamente em `ρ · ε · (2 m)² = 0,82 kg`.

A rigidez estrutural alta (2000 N/m) é a estratégia da Seção 4.3 para evitar a
**superelasticidade**: o tecido estica só ~1,3 % em vez de se esticar como
borracha.

## Métodos de integração

| Método | `metodo=` | dt típico | Estabilidade |
|--------|-----------|-----------|--------------|
| Euler explícito | `"explicito"` | 0,0002 s | condicional (`dt ≤ c/k`) |
| Euler semi-implícito | `"semi"` | 0,002 s | bem mais estável |
| **Euler implícito (Kang e Cho)** | `"kangcho"` | **0,002 s** | estável com passo grande |

### Euler implícito de Kang e Cho (Seção 4.2.2.1)

O Euler implícito atualiza o estado usando as forças no **próximo** instante.
Expandindo essas forças por Taylor (Eq. 4.22), o passo recai no sistema linear
esparso (Eq. 4.25):

```
(M − dt²·∂f/∂x − dt·∂f/∂v) · Δv = dt · (f + dt·∂f/∂x·v)
```

**Kang e Cho (2004)** decompõem esse sistema em *m* equações 3×3 (uma por
partícula) e o resolvem pelo esquema iterativo de **Jacobi**. Eles observaram
que **uma única iteração** já produz resultados estáveis e plausíveis
(Eq. 4.31) — é exatamente o que `integrate_kangcho` faz:

1. monta, por partícula, o bloco diagonal `A_ii = m_i·I + dt·Cʳᵉˢ·I + Σⱼ(dt²·J + dt·D)` e o lado direito `b_i = dt·f̃_i`;
2. estimativa inicial `p_i = A_ii⁻¹·b_i`;
3. uma iteração de Jacobi: `Δv_i = A_ii⁻¹·(b_i + Σⱼ(dt²·J + dt·D)·p_j)`;
4. `v ← v + Δv` e `x ← x + dt·v`.

As Jacobianas das molas (`J = ∂f/∂x`, Eqs. 4.33/4.34) e do amortecimento
(`D = ∂fᵈ/∂v`, Eq. 4.35) estão em `Spring.jacobians()`.

**Por que implícito?** No mesmo passo `dt = 0,002 s`, o **Euler explícito
diverge** (estoura em ~0,09 s), enquanto o **Kang e Cho permanece estável** —
reproduzindo a razão de 10× entre os passos da Tabela 5.x da dissertação
(explícito 0,0002 s × implícito 0,002 s). O explícito só fica estável com
`dt = 0,0002 s`.
