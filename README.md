# Próximas Etapas do Projeto

Após a implementação inicial do simulador de tecidos baseado no modelo massa-mola, foram definidos novos objetivos para aprimorar o comportamento físico da simulação e aproximá-la de uma implementação mais robusta.

As próximas etapas do desenvolvimento incluem:

* Implementar o cálculo e a visualização das forças atuantes sobre cada vértice da malha, permitindo analisar a contribuição individual das molas e da gravidade no movimento do tecido;
* Identificar e utilizar a vizinhança de cada vértice, considerando as conexões estruturais, de cisalhamento e de flexão;
* Adotar o método de integração numérica de **Euler explícito** para a atualização das posições e velocidades dos vértices ao longo do tempo;
* Incorporar o efeito de **amortecimento (damping)**, reduzindo oscilações excessivas e tornando o comportamento do tecido mais estável e realista;
* Tratar adequadamente os diferentes tipos de vértices da malha, distinguindo vértices internos, de borda e de canto, uma vez que cada um possui conjuntos distintos de vizinhos e, consequentemente, diferentes interações físicas;
* Organizar a implementação com base na planilha de referência adotada no projeto, definindo claramente a ordem de processamento e as condições de vizinhança para cada tipo de vértice.

Essas melhorias têm como objetivo aumentar a fidelidade física da simulação, facilitar a análise do comportamento do sistema massa-mola e fornecer uma base sólida para futuras extensões do projeto.
