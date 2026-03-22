import pytest

from mkmchat.http_server import explain_mechanic_json
from mkmchat.llm.ollama import OllamaAssistant


class _FakeDoc:
    def __init__(self, content: str, doc_type: str = "gameplay", metadata: dict | None = None):
        self.content = content
        self.doc_type = doc_type
        self.metadata = metadata or {}


class _FakeRag:
    enabled = True

    def __init__(self, results):
        self._results = results

    def search(self, query, top_k=10, doc_type=None, min_similarity=0.25):
        return self._results[:top_k]


class _AssistantOK:
    enabled = True

    async def explain_mechanic(self, mechanic: str, model=None):
        return {"definition": "  Power drain removes enemy bars.  ", "recommendations": "  "}


class _AssistantError:
    enabled = True

    async def explain_mechanic(self, mechanic: str, model=None):
        return {
            "error": "Model response could not be parsed into mechanic sections.",
            "raw_response": "{ bad json",
        }


def _new_assistant_for_unit_tests() -> OllamaAssistant:
    assistant = OllamaAssistant.__new__(OllamaAssistant)
    assistant.rag_system = None
    return assistant


def test_parse_mechanic_json_strict_object():
    assistant = _new_assistant_for_unit_tests()

    parsed = assistant._parse_mechanic_json('{"definition":"What it is","recommendations":"How to use it"}')

    assert parsed == {
        "definition": "What it is",
        "recommendations": "How to use it",
    }


def test_parse_mechanic_json_fenced_and_capitalized_keys():
    assistant = _new_assistant_for_unit_tests()

    text = """```json
{"Definition": "Def", "Recommendations": ["Tip 1", "Tip 2"]}
```"""
    parsed = assistant._parse_mechanic_json(text)

    assert parsed is not None
    assert parsed["definition"] == "Def"
    assert "Tip 1" in parsed["recommendations"]
    assert "Tip 2" in parsed["recommendations"]


def test_parse_mechanic_json_fallback_sections():
    assistant = _new_assistant_for_unit_tests()

    text = """## Definition
Power drain removes enemy power.

## Recommendations
Use power generation gear to recover quickly."""

    parsed = assistant._parse_mechanic_json(text)

    assert parsed is not None
    assert "Power drain" in parsed["definition"]
    assert "power generation" in parsed["recommendations"]


def test_mechanic_rag_context_respects_budget(monkeypatch):
    assistant = _new_assistant_for_unit_tests()

    docs = [
        (_FakeDoc(content=("A" * 320), doc_type="gameplay", metadata={"i": i}), 0.9 - i * 0.02)
        for i in range(12)
    ]
    assistant.rag_system = _FakeRag(docs)

    monkeypatch.setenv("MKM_MECHANIC_RAG_MAX_PASSAGES", "4")
    monkeypatch.setenv("MKM_MECHANIC_RAG_MAX_CHARS", "900")

    context = assistant._build_mechanic_rag_context("power drain")

    assert "=== RAG" in context
    assert context.count("### [") <= 4
    assert len(context) < 1600


@pytest.mark.asyncio
async def test_explain_mechanic_json_wraps_and_strips(monkeypatch):
    monkeypatch.setattr("mkmchat.http_server.get_rag_system", lambda: object())
    monkeypatch.setattr("mkmchat.http_server.get_ollama_assistant", lambda rag_system=None: _AssistantOK())

    result = await explain_mechanic_json("power drain", model="llama3.2:3b")

    assert "response" in result
    assert result["response"]["definition"] == "Power drain removes enemy bars."
    assert result["response"]["recommendations"] == ""


@pytest.mark.asyncio
async def test_explain_mechanic_json_error_is_sanitized(monkeypatch):
    monkeypatch.setattr("mkmchat.http_server.get_rag_system", lambda: object())
    monkeypatch.setattr("mkmchat.http_server.get_ollama_assistant", lambda rag_system=None: _AssistantError())

    result = await explain_mechanic_json("power drain")

    assert "error" in result
    assert "raw_response" not in result
