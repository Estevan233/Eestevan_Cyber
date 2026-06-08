from __future__ import annotations

from app.agent import LLMError
from app.settings import Settings


SYSTEM_PROMPT = """你是 Estevan Cyber 个人网站的知识库问答 Agent。
你只能基于给定资料回答；如果资料不足，要直接说明不足。
回答使用简体中文，语气自然、准确、克制。
每个关键结论尽量对应资料来源，不要编造不存在的文章、项目或经历。"""


class MissingKeyLLM:
    def generate(self, *, question: str, context: str, history: list[dict[str, str]]) -> str:
        raise LLMError("DEEPSEEK_API_KEY is not configured")


class StaticLLM:
    def generate(self, *, question: str, context: str, history: list[dict[str, str]]) -> str:
        return "测试模式：已根据本地知识库检索到相关内容。"


class DeepSeekLLM:
    def __init__(self, settings: Settings) -> None:
        if not settings.deepseek_api_key:
            raise LLMError("DEEPSEEK_API_KEY is not configured")

        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise LLMError("LangChain DeepSeek dependencies are not installed") from exc

        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    "历史消息:\n{history}\n\n资料:\n{context}\n\n用户问题:\n{question}\n\n请给出回答，并在回答末尾列出参考来源标题。",
                ),
            ]
        )
        self._model = ChatOpenAI(
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=settings.temperature,
        )
        self._chain = self._prompt | self._model

    def generate(self, *, question: str, context: str, history: list[dict[str, str]]) -> str:
        try:
            response = self._chain.invoke(
                {
                    "question": question,
                    "context": context,
                    "history": _format_history(history),
                }
            )
        except Exception as exc:
            raise LLMError("DeepSeek provider request failed") from exc

        content = getattr(response, "content", response)
        return str(content)


def build_llm(settings: Settings, *, testing: bool = False):
    if testing:
        return StaticLLM()
    if not settings.deepseek_api_key:
        return MissingKeyLLM()
    return DeepSeekLLM(settings)


def _format_history(history: list[dict[str, str]]) -> str:
    if not history:
        return "无"
    return "\n".join(f"{item['role']}: {item['content']}" for item in history)

