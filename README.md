# Simulador de Tecido — Modelo Massa-Mola

Simulação de um tecido (cloth) usando o modelo massa-mola: a malha é um
conjunto de vértices (massas) conectados por molas de três tipos
(estruturais, de cisalhamento e de flexão), sob ação da gravidade e de
amortecimento, integrada no tempo por Euler.

## Etapas implementadas

| # | Objetivo | Onde |
|---|----------|------|
| 1 | Cálculo **e visualização** das forças por vértice (contribuição individual da gravidade e de cada tipo de mola) | `vertex.py` (`forces`), `spring.py`, `visualize.py forces` |
| 2 | Vizinhança de cada vértice (estrutural, cisalhamento, flexão) | `cloth.py` (`OFFSETS_BY_TYPE`, `build_neighborhoods`) |
| 3 | Integração por **Euler explícito** (e semi-implícito para comparação) | `cloth.py` (`integrate`) |
| 4 | **Amortecimento** (damping) | `spring.py` (`apply_force`) |
| 5 | Tipos de vértice: interno, borda e canto (vizinhanças e massa distintas) | `cloth.py` (`classify`, massa por área) |
| 6 | **Planilha de referência** de vizinhança + visualização | `cloth.py` (`export_reference_table`), `planilha.py` |

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

python main.py                 # demonstração no terminal + exporta vizinhanca.csv
python visualize.py            # animação do tecido (Euler explícito)
python visualize.py forces     # animação com vetores de força (verde=gravidade, laranja=molas)
python visualize.py semi       # usa Euler semi-implícito (comparação)
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

## Nota sobre o integrador (Euler explícito × semi-implícito)

O enunciado pede **Euler explícito** (a posição é atualizada com a velocidade
*antiga*). Esse método é apenas condicionalmente estável: para uma mola
amortecida de rigidez `k` e amortecimento `c`, a análise de estabilidade leva a

```
dt ≤ c / k
```

ou seja, **sem amortecimento o Euler explícito é sempre instável**. Por isso o
amortecimento não é só estético: é necessário para estabilizar a integração.

Parâmetros padrão: `k = 80`, `c = 0,8`, `dt = 0,005` → `c/k = 0,01`, com margem
de segurança de 2×. O `integrate` também oferece o **Euler semi-implícito**
(`metodo="semi"`), que é muito mais estável — útil para comparar os dois
métodos no relatório.
