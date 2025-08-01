from typing import Any, ClassVar, Type, Literal
import logging
from pydantic import BaseModel, Field, PrivateAttr

from langchain.tools import BaseTool
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface.embeddings import HuggingFaceEmbeddings


class RetrieverInput(BaseModel):
    query: str = Field(..., min_length=1, description="Краткий запрос (1–3 фразы)")
    program: Literal["ai", "ai_product"] = Field(..., description="Программа")


class RetrieverTool(BaseTool):
    """
    Инструмент для семантического поиска документов с помощью FAISS и HuggingFace embeddings.
    Поддерживает фильтрацию по программе через метаданные.
    docs — список объектов Document, где текст хранится в page_content, а метаинформация (type, source, program) — в metadata.
    """

    name: str = "retriever"
    description: str = "Поиск релевантных документов по семантическому сходству."
    args_schema: ClassVar[Type[BaseModel]] = RetrieverInput  # <-- ВАЖНО
    _retriever: Any = PrivateAttr(default=None)  # <-- чтобы не было полем модели

    def __init__(
        self,
        docs: list[Document],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        name: str = "retriever",
        description: str = "Поиск релевантных документов по семантическому сходству.",
    ):
        """
        Инициализация RetrieverTool.
        docs: список объектов Document для индексации (page_content — текст, metadata — метаинформация)
        model_name: название модели HuggingFace для эмбеддингов
        name: имя инструмента
        description: описание инструмента
        """
        logging.info(
            f"Инициализация RetrieverTool: name={name}, model_name={model_name}, docs_count={len(docs)}"
        )
        super().__init__(name=name, description=description)
        logging.info("Создание эмбеддингов HuggingFace...")
        embeddings = HuggingFaceEmbeddings(model_name=model_name)
        texts = [doc.page_content for doc in docs]
        metadatas = [doc.metadata for doc in docs]
        logging.info(f"Индексация {len(texts)} документов в FAISS...")
        vectorstore = FAISS.from_texts(texts, embedding=embeddings, metadatas=metadatas)
        self._retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        logging.info("RetrieverTool успешно инициализирован.")

    def _run(self, *args, **kwargs):
        """
        Синхронный поиск релевантных документов по запросу.
        Аргументы:
            query: строка запроса (первый аргумент или ключ 'query')
            program: название программы для фильтрации (обязательно)
        Возвращает:
            Строки найденных документов, объединённые через перевод строки.
        """
        query = args[0] if args else kwargs.get("query")
        program = kwargs.get("program")
        # Проверяем обязательные параметры
        if not query:
            raise ValueError("Parameter 'query' is required and cannot be empty.")
        if not program:
            raise ValueError("Parameter 'program' is required and cannot be empty.")
        logging.info(f"Запуск поиска: query='{query}', program='{program}'")
        # Фильтрация по программе задана явно
        if program:
            logging.info(f"Фильтрация по программе: {program}")
            results = self._retriever.invoke(query, filter={"program": program})
        else:
            results = self.retriever.invoke(query)
        logging.info(f"Найдено документов: {len(results)}")
        return "\n".join([doc.page_content for doc in results])

    async def _arun(self, *args, **kwargs):
        """
        Асинхронный поиск релевантных документов по запросу.
        Аргументы:
            query: строка запроса (первый аргумент или ключ 'query')
            program: название программы для фильтрации (обязательно)
        Возвращает:
            Строки найденных документов, объединённые через перевод строки.
        """
        query = args[0] if args else kwargs.get("query")
        program = kwargs.get("program")
        # Проверяем обязательные параметры в асинхронном режиме
        if not query:
            raise ValueError("Parameter 'query' is required and cannot be empty.")
        if not program:
            raise ValueError("Parameter 'program' is required and cannot be empty.")
        logging.info(f"[async] Запуск поиска: query='{query}', program='{program}'")
        return self._run(query, program=program)
