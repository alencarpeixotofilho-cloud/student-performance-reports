# Relatório Individual de Desempenho

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green?style=flat-square) ![Status](https://img.shields.io/badge/status-em%20constru%C3%A7%C3%A3o-orange?style=flat-square)

> Automatiza a geração de um relatório por participante a partir de uma série de simulados.

## 📌 Visão geral

Consolida os resultados de vários simulados e gera, para cada participante, uma planilha/relatório com evolução ao longo do tempo, desempenho por área e tema, fragilidades prioritárias e cruzamento com a matriz de competências do exame. Inclui também a visão agregada da turma.

## ✨ Funcionalidades

- Trajetória do participante ao longo dos simulados
- Desempenho por área, tema e competência
- Ranking de fragilidades com sugestão de prioridade de estudo
- Análise questão a questão
- Visão consolidada da turma
- Saída em Excel formatado e PDF

## 🗂️ Estrutura do repositório

```text
relatorio-individual-desempenho/
├── src/            # consolidação, indicadores e geração das saídas
├── modelos/        # modelos de planilha e relatório
├── exemplos/       # turma e simulados sintéticos
├── LICENSE
└── README.md
```

## 🚀 Como usar

```bash
python exemplos/gerar_dados_exemplo.py --participantes 50 --simulados 7
python -m src.build --entrada exemplos/ --saida saida/
```

## 🔒 Dados e privacidade

Este repositório **não contém dados reais** de estudantes, docentes ou instituições.
Todos os exemplos usam **dados sintéticos** gerados pelo próprio projeto
(`exemplos/gerar_dados_exemplo`), com identificadores fictícios (`Estudante 001`, `Item 001`…).
Os itens de prova usados nos exemplos são inventados para fins de demonstração.

## 🛣️ Roadmap

- [ ] Dados sintéticos de turma
- [ ] Consolidação dos simulados
- [ ] Planilha individual
- [ ] Visão da turma
- [ ] Relatório em PDF

## 📄 Licença

Distribuído sob a licença MIT. Veja [`LICENSE`](LICENSE).
