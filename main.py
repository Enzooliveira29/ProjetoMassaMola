from cloth import Cloth

cloth = Cloth()

cloth.build_grid(
    rows=5,
    cols=5,
    spacing=0.1
)

for step in range(100):

    cloth.update(0.01)

    print(f"\nPasso {step}")

    for vertex in cloth.vertices:
        print(
            f"Vértice {vertex.id}:",
            vertex.position
        )