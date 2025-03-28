from dotenv import load_dotenv
from langchain_mistralai.chat_models import ChatMistralAI
from langchain.schema import HumanMessage
import os

load_dotenv()

class MistralClient:
    def __init__(self):
        self.llm = ChatMistralAI(
            model="mistral-large-latest",
            api_key=os.getenv("MISTRAL_API_KEY")
        )
    
    def generate_response(self, prompt):
        """Génère une réponse à partir du prompt donné"""
        message = HumanMessage(content=prompt)
        response = self.llm([message])
        return response.content