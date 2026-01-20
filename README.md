# clone-tabnews

## Filtro de extratos bancários com IA

Este projeto fornece um script que lê um arquivo Excel de extrato bancário, classifica as transações como **gasto** ou **recebido** e mostra os totais. Quando a variável `OPENAI_API_KEY` estiver configurada, o script pode usar IA para fazer a classificação.

### Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Uso básico

```bash
python bank_ai_filter.py caminho/para/extrato.xlsx --output extrato_classificado.xlsx
```

### Usar IA (OpenAI)

```bash
export OPENAI_API_KEY="sua-chave"
python bank_ai_filter.py caminho/para/extrato.xlsx --use-ai
```

### Parâmetros úteis

- `--description-column`: nome da coluna com a descrição da transação.
- `--amount-column`: nome da coluna com o valor da transação.
- `--output`: caminho para salvar o Excel com a coluna `classificacao`.
- `--model`: modelo OpenAI usado na classificação.

O script tenta detectar automaticamente as colunas de descrição e valor quando elas não são informadas.
