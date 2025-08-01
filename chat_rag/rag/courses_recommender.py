import json
import logging
import os
from typing import Any, Dict, List, Union, ClassVar, Type, Literal

from langchain.schema import HumanMessage, SystemMessage
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, PrivateAttr


CHUNKS_DIR = "data/chunks"
ai_courses_chunks = os.path.join(CHUNKS_DIR, "ai_courses_chunks.json")
ai_product_courses_chunks = os.path.join(CHUNKS_DIR, "ai_product_courses_chunks.json")


class CoursesRecommenderInput(BaseModel):
    program: Literal["ai", "ai_product"]
    background: str
    interests: str
    goals: str


class CoursesRecommender(BaseTool):
    """
    Tool для рекомендации программы обучения из курсов ИТМО.
    Строит программу из 5 курсов на каждый из 4 семестров.
    """

    name: str = "courses_recommender"
    description: str = "Рекомендует программу обучения из курсов ИТМО на основе профиля абитуриента"
    args_schema: ClassVar[Type[BaseModel]] = CoursesRecommenderInput  # <-- ВАЖНО
    courses: List[Dict[str, Any]] = Field(default_factory=list)
    _llm: Any = PrivateAttr(default=None)
    _logger: logging.Logger = PrivateAttr()

    def __init__(self):
        super().__init__()
        self._llm = ChatOpenAI(model="gpt-4.1-nano", temperature=0.0)
        self._logger = logging.getLogger("CoursesRecommender")
        if not self._logger.hasHandlers():
            logging.basicConfig(level=logging.INFO)
        self._logger.info("Инициализация CoursesRecommender")
        self.load_courses()

    def load_courses(self):
        """
        Загружает все курсы из ai_courses_chunks.json и ai_product_courses_chunks.json.
        """
        chunk_files = [ai_courses_chunks, ai_product_courses_chunks]
        for fpath in chunk_files:
            try:
                with open(fpath, encoding="utf-8") as f:
                    data = json.load(f)
                    assert isinstance(
                        data, list
                    ), "Неверный формат данных. Должен быть список."
                    for item in data:
                        assert (
                            isinstance(item, dict) and "name" in item
                        ), "Неверный формат данных. Каждый элемент должен быть словарем с ключом 'name'."
                        self.courses.append(item)
                self._logger.info(f"Загружено {len(data)} курсов из {fpath}")
            except (OSError, json.JSONDecodeError, AssertionError) as e:
                self._logger.error(f"Ошибка при загрузке {fpath}: {e}")

    def filter_courses_by_program(self, program: str) -> List[Dict[str, Any]]:
        """
        Фильтрует курсы по программе обучения.
        """
        assert program in ["ai", "ai_product"], "Неверная программа обучения"
        filtered = [
            course for course in self.courses if course.get("program") == program
        ]
        self._logger.info(
            f"Фильтрация курсов по программе '{program}': найдено {len(filtered)} курсов"
        )
        return filtered

    def get_courses_for_semester(
        self, courses: List[Dict[str, Any]], semester: int
    ) -> List[Dict[str, Any]]:
        """
        Возвращает курсы, доступные для данного семестра.
        """
        filtered = [
            course for course in courses if semester in course.get("semesters", [])
        ]
        self._logger.info(
            f"Курсы для семестра {semester}: найдено {len(filtered)} курсов"
        )
        return filtered

    def select_courses_for_semester(
        self,
        background: str,
        interests: str,
        goals: str,
        selected_courses: List[Dict[str, Any]],
        candidate_courses: List[Dict[str, Any]],
        semester: int,
    ) -> List[Dict[str, Any]]:
        """
        Выбирает 5 лучших курсов для семестра с помощью LLM.
        """
        self._logger.info(
            f"Выбор курсов для семестра {semester}. Кандидатов: {len(candidate_courses)}"
        )
        if len(candidate_courses) <= 5:
            self._logger.info(
                f"Кандидатов <= 5, возвращаем все курсы для семестра {semester}"
            )
            return candidate_courses

        # Формируем список уже выбранных курсов
        selected_names = [course["name"] for course in selected_courses]

        # Формируем список кандидатов
        candidates_info = []
        for i, course in enumerate(candidate_courses):
            candidates_info.append(
                f"{i+1}. {course['name']} ({course.get('hours', 'Н/Д')} часов)"
            )
        candidates_info_str = "\n".join(candidates_info)

        system_prompt = f"""
Ты эксперт по образовательным программам ИТМО в области ИИ.
Твоя задача - выбрать 5 наиболее подходящих курсов для {semester} семестра.

Профиль студента:
- Бэкграунд: {background}
- Интересы: {interests}
- Цели: {goals}

Уже выбранные курсы: {', '.join(selected_names) if selected_names else 'Нет'}

Кандидаты для {semester} семестра:
{candidates_info_str}

Выбери 5 курсов, которые:
1. Лучше всего соответствуют профилю студента
2. Дополняют уже выбранные курсы
3. Обеспечивают прогрессивное обучение

Ответь строго в формате Python: list[int] — список номеров выбранных курсов, например: [1, 3, 5, 7, 9].
"""

        try:
            self._logger.info(f"Отправка запроса LLM для семестра {semester}")
            response = self._llm.invoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content="Выбери 5 лучших курсов для этого семестра."),
                ]
            )

            response_text = (
                response.content if hasattr(response, "content") else str(response)
            )
            self._logger.info(f"Ответ LLM: {response_text}")
            # Ожидаем ответ строго в формате Python: list[int]
            import ast

            selected_indices = []
            if isinstance(response_text, str):
                try:
                    parsed = ast.literal_eval(response_text.strip())
                    if isinstance(parsed, list):
                        for idx in parsed:
                            if isinstance(idx, int) and 1 <= idx <= len(
                                candidate_courses
                            ):
                                selected_indices.append(idx - 1)
                except (SyntaxError, ValueError) as e:
                    self._logger.error(f"Ошибка парсинга ответа LLM: {e}")

            self._logger.info(f"Выбраны индексы курсов: {selected_indices}")
            return [candidate_courses[i] for i in selected_indices[:5]]

        except (ValueError, TypeError, AttributeError) as e:
            self._logger.error(f"Ошибка при выборе курсов: {e}")
            # Возвращаем первые 5 курсов как fallback
            return candidate_courses[:5]

    def build_learning_program(
        self, program: str, background: str, interests: str, goals: str
    ) -> Union[Dict[str, List[Dict[str, Any]]], Dict[str, str]]:
        """
        Строит программу обучения из 5 курсов на каждый из 4 семестров.
        """
        # Фильтруем курсы по программе
        self._logger.info(
            f"Строим программу обучения: program={program}, background={background}, interests={interests}, goals={goals}"
        )
        program_courses = self.filter_courses_by_program(program)

        if not program_courses:
            self._logger.error(f"Курсы для программы {program} не найдены")
            return {"error": f"Курсы для программы {program} не найдены"}

        learning_program: Dict[str, List[Dict[str, Any]]] = {}
        selected_courses: List[Dict[str, Any]] = []

        # Для каждого семестра выбираем 5 курсов
        for semester in range(1, 5):
            self._logger.info(f"Обработка семестра {semester}")
            # Получаем курсы для текущего семестра
            semester_candidates = self.get_courses_for_semester(
                program_courses, semester
            )

            if not semester_candidates:
                self._logger.info(f"Нет доступных курсов для семестра {semester}")
                learning_program[f"semester_{semester}"] = []
                continue

            # Выбираем 5 курсов для семестра
            selected_for_semester = self.select_courses_for_semester(
                background=background,
                interests=interests,
                goals=goals,
                selected_courses=selected_courses,
                candidate_courses=semester_candidates,
                semester=semester,
            )

            self._logger.info(
                f"Выбрано {len(selected_for_semester)} курсов для семестра {semester}"
            )
            learning_program[f"semester_{semester}"] = selected_for_semester
            selected_courses.extend(selected_for_semester)

        return learning_program

    def _run(self, *args, **kwargs) -> str:
        """
        Основная функция tool'а - строит рекомендованную программу обучения.
        """
        try:
            self._logger.info(f"Вызов _run с аргументами: {kwargs}")
            # Извлекаем параметры из kwargs
            program = kwargs.get("program", "")
            background = kwargs.get("background", "")
            interests = kwargs.get("interests", "")
            goals = kwargs.get("goals", "")

            if not all([program, background, interests, goals]):
                self._logger.error("Ошибка: не все параметры заполнены")
                return "Ошибка: все параметры (program, background, interests, goals) должны быть заполнены"

            # Строим программу обучения
            learning_program = self.build_learning_program(
                program, background, interests, goals
            )

            if "error" in learning_program:
                self._logger.error(f"Ошибка: {learning_program['error']}")
                return str(learning_program["error"])

            # Формируем читаемый ответ
            result = (
                f"Рекомендованная программа обучения для программы '{program}':\n\n"
            )

            for semester_key, courses in learning_program.items():
                if semester_key == "error":
                    continue

                semester_num = semester_key.split("_")[1]
                result += f"Семестр {semester_num}:\n"

                if not courses:
                    result += "  - Нет доступных курсов\n"
                else:
                    for i, course in enumerate(courses, 1):
                        if isinstance(course, dict):
                            result += f"  {i}. {course.get('name', 'Неизвестное название')} ({course.get('hours', 'Н/Д')} часов)\n"
                result += "\n"

            self._logger.info("Результат программы обучения сформирован")
            return result

        except Exception as e:
            self._logger.error(f"Ошибка при построении программы: {str(e)}")
            return f"Ошибка при построении программы: {str(e)}"

    async def _arun(self, *args, **kwargs) -> str:
        """Асинхронная версия."""
        return self._run(*args, **kwargs)
