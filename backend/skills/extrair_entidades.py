import openai
import json, re
def extrair_entidades_llm(pergunta):
    prompt = f"""
Extraia as seguintes entidades do texto abaixo e retorne em JSON:
- UF de origem
- UF de destino
- NCM
- Regime tributário
- CNAE principal

Texto: "{pergunta}"
"""
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    # Tente extrair o JSON da resposta do model
    match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return {}