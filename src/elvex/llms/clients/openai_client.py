import openai

class OpenAIClient:
    def __init__(self, api_key, model):
        openai.api_key = api_key
        self.model = model

    def chat(self, prompt):

        response = openai.ChatCompletion.create(
            model=self.model,
            messages=prompt
        )
        return response['choices'][0]['message']['content']
    