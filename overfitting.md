# O que é Overfitting em Machine Learning?

Overfitting (ou sobreajuste) ocorre quando um modelo de Machine Learning aprende excessivamente os detalhes e ruídos do conjunto de dados de treino, a ponto de prejudicar o seu desempenho ao lidar com dados novos (dados de teste).

Dizemos que o modelo "decorou" os dados em vez de aprender o padrão geral. Ele apresenta alta acurácia no treino, mas péssima capacidade de generalização.

## Como evitar o Overfitting?
- **Mais dados de treino:** Fornecer mais exemplos ajuda o modelo a generalizar melhor.
- **Simplificar o modelo:** Reduzir o número de parâmetros, camadas ou neurônios.
- **Regularização:** Técnicas como L1 (Lasso) ou L2 (Ridge) que penalizam coeficientes muito grandes.
- **Cross-Validation (Validação Cruzada):** Usar K-Fold para garantir que o modelo seja testado em diferentes subconjuntos.
- **Early Stopping (Parada Antecipada):** Interromper o treinamento assim que o erro de validação começar a subir.
