#!/usr/bin/env python3
import argparse
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
import requests

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class ColumnGuess:
    description: str
    amount: Optional[str]


def guess_columns(df: pd.DataFrame) -> ColumnGuess:
    description_candidates = [
        col for col in df.columns if "desc" in col.lower() or "hist" in col.lower()
    ]
    description = description_candidates[0] if description_candidates else df.columns[0]

    amount_candidates = [
        col
        for col in df.columns
        if any(token in col.lower() for token in ["valor", "amount", "importe", "credito", "debito"])
    ]
    amount = amount_candidates[0] if amount_candidates else None

    if amount is None:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                amount = col
                break

    return ColumnGuess(description=description, amount=amount)


def normalize_amount(value: object) -> Optional[float]:
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace(".", "").replace(",", ".")
    raw = raw.replace("R$", "").replace("$", "").strip()
    try:
        return float(raw)
    except ValueError:
        return None


def heuristic_classification(description: str, amount: Optional[float]) -> str:
    desc_lower = (description or "").lower()
    if amount is not None:
        if amount < 0:
            return "gasto"
        if amount > 0:
            return "recebido"

    received_keywords = [
        "salario",
        "salário",
        "pix recebido",
        "transferencia recebida",
        "transferência recebida",
        "deposito",
        "depósito",
        "estorno",
        "reembolso",
        "credito",
        "crédito",
    ]
    if any(keyword in desc_lower for keyword in received_keywords):
        return "recebido"

    return "gasto"


def build_ai_payload(items: Sequence[Tuple[int, str]], model: str) -> Dict[str, object]:
    system_prompt = (
        "Você é um classificador de transações bancárias. "
        "Retorne 'gasto' para despesas e 'recebido' para créditos. "
        "Responda em JSON válido com a lista de rótulos na mesma ordem."
    )
    user_lines = [f"{idx}: {text}" for idx, text in items]
    user_prompt = "\n".join(user_lines)

    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }


def call_openai_classifier(
    items: Sequence[Tuple[int, str]],
    api_key: str,
    model: str = DEFAULT_MODEL,
) -> Dict[int, str]:
    payload = build_ai_payload(items, model)
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    labels = parsed.get("labels")
    if not isinstance(labels, list):
        raise ValueError("Resposta da IA não contém 'labels' como lista.")

    result: Dict[int, str] = {}
    for (idx, _), label in zip(items, labels):
        result[idx] = str(label).strip().lower()
    return result


def classify_transactions(
    df: pd.DataFrame,
    description_col: str,
    amount_col: Optional[str],
    use_ai: bool,
    model: str,
) -> List[str]:
    api_key = os.getenv("OPENAI_API_KEY")
    descriptions = df[description_col].fillna("").astype(str).tolist()
    amounts = [
        normalize_amount(value) if amount_col else None
        for value in (df[amount_col] if amount_col else [None] * len(df))
    ]

    if use_ai and api_key:
        items = [(idx, text) for idx, text in enumerate(descriptions)]
        ai_labels = call_openai_classifier(items, api_key, model=model)
        return [ai_labels.get(idx, "gasto") for idx in range(len(descriptions))]

    return [
        heuristic_classification(desc, amt)
        for desc, amt in zip(descriptions, amounts)
    ]


def summarize(amounts: Sequence[Optional[float]], labels: Sequence[str]) -> Dict[str, float]:
    totals = {"gasto": 0.0, "recebido": 0.0}
    for amount, label in zip(amounts, labels):
        if amount is None:
            continue
        if label not in totals:
            totals[label] = 0.0
        totals[label] += amount
    return totals


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filtra um extrato em Excel e classifica gastos vs recebidos usando IA."
    )
    parser.add_argument("input", help="Caminho para o arquivo Excel (.xlsx)")
    parser.add_argument(
        "--description-column",
        help="Nome da coluna com a descrição da transação",
    )
    parser.add_argument(
        "--amount-column",
        help="Nome da coluna com o valor da transação",
    )
    parser.add_argument(
        "--output",
        help="Caminho para salvar o Excel com a coluna 'classificacao'",
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        help="Força o uso da IA (requer OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Modelo OpenAI (padrão: {DEFAULT_MODEL})",
    )

    args = parser.parse_args()

    df = pd.read_excel(args.input)
    guesses = guess_columns(df)
    description_col = args.description_column or guesses.description
    amount_col = args.amount_column or guesses.amount

    labels = classify_transactions(
        df,
        description_col=description_col,
        amount_col=amount_col,
        use_ai=args.use_ai,
        model=args.model,
    )
    df["classificacao"] = labels

    amounts = [
        normalize_amount(value) if amount_col else None
        for value in (df[amount_col] if amount_col else [None] * len(df))
    ]
    totals = summarize(amounts, labels)

    print("Resumo:")
    print(f"  Gastos: {totals.get('gasto', 0.0):.2f}")
    print(f"  Recebidos: {totals.get('recebido', 0.0):.2f}")

    if args.output:
        df.to_excel(args.output, index=False)
        print(f"Arquivo com classificação salvo em: {args.output}")


if __name__ == "__main__":
    main()
