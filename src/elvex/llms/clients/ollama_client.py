import subprocess, json, textwrap, os, shutil
from config import settings as cfg
from ollama import chat

class LocalLLMClient:
    def __init__(self, model):
        if not shutil.which("ollama"):
            raise RuntimeError("Ollama is not installed or is not in PATH")
        self.model = model

    def chat(self, messages):
        reply = chat(model=self.model, messages=messages)
        return reply.message.content