# clone-tabnews

## Filtro de extratos bancários com IA

Este projeto fornece um **notebook Jupyter** que lê um arquivo Excel de extrato bancário, classifica as transações como **gasto** ou **recebido** e mostra os totais. Quando a variável `OPENAI_API_KEY` estiver configurada, o notebook pode usar IA para fazer a classificação.

### Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Como usar o notebook

1. Abra `bank_ai_filter.ipynb` no Jupyter (JupyterLab, VS Code, etc.).
2. Preencha o caminho do Excel e as opções de classificação na célula de configurações.
3. Execute as células para obter o resumo e, se desejar, salvar o arquivo classificado.

### Observações

- O notebook tenta detectar automaticamente as colunas de descrição e valor quando elas não são informadas.
- Para usar IA, defina `OPENAI_API_KEY` no ambiente antes de abrir o notebook.
