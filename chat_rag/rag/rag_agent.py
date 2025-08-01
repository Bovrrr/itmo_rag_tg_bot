import json
import os
from typing import Any, Dict, Union

from dotenv import load_dotenv
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory
from langchain.schema import Document
from langchain_openai import ChatOpenAI

from chat_rag.rag.courses_recommender import CoursesRecommender
from chat_rag.rag.retriever import RetrieverTool
from chat_rag.rag.prompts import AGENT_SYSTEM_PROMPT

load_dotenv()


# Load knowledge base documents
def load_documents():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    chunks_dir = os.path.join(base_dir, "data", "chunks")
    paths = [
        os.path.join(chunks_dir, "ai_chunks.json"),
        os.path.join(chunks_dir, "ai_product_chunks.json"),
    ]
    docs = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                if "question" in item and "answer" in item:
                    text = f"Q: {item['question']}\nA: {item['answer']}"
                else:
                    text = item.get("text", "")
                metadata = {
                    k: v
                    for k, v in item.items()
                    if k not in ("text", "question", "answer")
                }
                docs.append(Document(page_content=text, metadata=metadata))
        except Exception as e:
            print(f"Error loading {path}: {e}")
    return docs


# Initialize tools and agent
_docs = load_documents()
retriever_tool = RetrieverTool(docs=_docs)
courses_tool = CoursesRecommender()
_tools = [retriever_tool, courses_tool]
_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.0,
)

# Инициализация агента один раз
agent = initialize_agent(
    tools=_tools,
    llm=_llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=None,
    verbose=True,
    agent_kwargs={"system_message": AGENT_SYSTEM_PROMPT},
)


def process_message(
    user_message: str,
    memory: Union[ConversationBufferMemory, ConversationBufferWindowMemory],
) -> str:
    agent.memory = memory
    return agent.run(input=user_message)


# Example entry point for CLI testing
if __name__ == "__main__":
    print("Telegram RAG Agent. Type your message below.")
    memory = ConversationBufferMemory()
    while True:
        msg = input("User: ")
        resp = process_message(msg, memory)
        print("Agent:", resp)
