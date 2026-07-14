from watsonx_client import call_model
import json

SYSTEM_PROMPT = """You are a Global Funding Discovery Agent.

TASK: Given matched funding opportunity names and the full funding database, return details for each matched opportunity as a JSON array. Return at most 6 items.

Each object in the array must have exactly these fields:
- "name": full opportunity name
- "category": funding category (e.g. Government Grant, Accelerator, VC, Non-Dilutive Grant, Corporate VC, Impact VC)
- "geography": geography or region where this funding applies
- "administered_by": which organisation, fund, or body manages it
- "funding_amount": how much money or support is available
- "funding_type": grant, equity investment, non-dilutive credits, blended, etc.
- "deadline": application deadline or "Rolling" if ongoing
- "required_documents": array of strings, maximum 4 items, each under 8 words
- "how_to_apply": one sentence, maximum 20 words
- "source_url": official website link

GUARDRAILS:
- Only use data explicitly present in the provided funding database.
- Do not invent, estimate, or add any information not present in the data.
- Keep all string values concise — under 30 words each.
- Write all values in plain language without markdown, asterisks, backticks, or symbols.
- Output only the JSON array. No extra text before or after.
"""

def run(matched_scheme_names):
    with open("data/schemes.json", "r") as f:
        schemes = json.load(f)
    user_message = f"Matched funding opportunity names: {matched_scheme_names}\n\nFull funding database:\n{json.dumps(schemes)}"
    return call_model(SYSTEM_PROMPT, user_message)
