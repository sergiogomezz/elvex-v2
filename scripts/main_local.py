from elvex.llms.registry import get_llm_client, LLMConfig
# Usa el del .env:
client = get_llm_client()
# O fuerza uno puntual:
# client = get_llm_client(LLMConfig(provider="ollama"))
resp = client.chat(
    messages=[{"role": "user", "content": "Hola"}],
    system_prompt="Sé breve.",
    temperature=0.2,
    max_output_tokens=200,
    tools=None,
)
print(resp.text)
