import json

import pytest

from mkmchat.http_server import build_structured_context, suggest_team_json


class _FakeDoc:
    def __init__(self, content: str, doc_type: str, metadata: dict | None = None):
        self.content = content
        self.doc_type = doc_type
        self.metadata = metadata or {}


class _FakeRag:
    enabled = True

    def __init__(self, by_type, documents):
        self._by_type = by_type
        self.documents = documents

    def search(self, query, top_k=5, doc_type=None, min_similarity=0.3):
        if doc_type is None:
            merged = []
            for values in self._by_type.values():
                merged.extend(values)
            return merged[:top_k]
        return self._by_type.get(doc_type, [])[:top_k]


class _AssistantStub:
    enabled = True
    base_url = "http://fake-ollama"

    def _resolve_model_name(self, model):
        return model or "llama3.2:3b"


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeAsyncClient:
    payload = {"response": "{}"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, timeout=None):
        return _FakeResponse(200, self.payload)


def _build_rag_fixture():
    char_doc = _FakeDoc(
        content="Character: Klassic Scorpion\nPassive: Applies fire damage over time.",
        doc_type="character",
        metadata={"name": "Klassic Scorpion", "rarity": "Diamond", "tier": "S"},
    )
    equip_doc = _FakeDoc(
        content="Equipment: Wrath Hammer\nEffect: Start with power",
        doc_type="equipment",
        metadata={"name": "Wrath Hammer", "type": "Weapon", "tier": "A"},
    )
    glossary_doc = _FakeDoc(
        content="Power drain removes enemy power bars.",
        doc_type="glossary",
    )
    gameplay_doc = _FakeDoc(
        content="Open with power drain to deny enemy specials.",
        doc_type="gameplay",
    )

    by_type = {
        "character": [(char_doc, 0.96)],
        "equipment": [(equip_doc, 0.88)],
        "glossary": [(glossary_doc, 0.83)],
        "gameplay": [(gameplay_doc, 0.81)],
    }
    return _FakeRag(by_type=by_type, documents=[char_doc])


def test_build_structured_context_uses_query_driven_glossary_and_gameplay():
    rag = _build_rag_fixture()

    context = build_structured_context(rag, "power drain control")

    assert "(rel=" in context["glossary"]
    assert "Power drain removes enemy power bars" in context["glossary"]
    assert "(rel=" in context["gameplay"]
    assert "Open with power drain" in context["gameplay"]


@pytest.mark.asyncio
async def test_suggest_team_json_rejects_non_structured_output(monkeypatch):
    rag = _build_rag_fixture()

    monkeypatch.setattr("mkmchat.http_server.get_rag_system", lambda: rag)
    monkeypatch.setattr("mkmchat.http_server.get_ollama_assistant", lambda rag_system=None: _AssistantStub())
    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)

    _FakeAsyncClient.payload = {"response": "Use Scorpion with any gear you like."}
    result = await suggest_team_json("aggressive", model="llama3.2:3b")

    assert "error" in result
    assert "response" not in result


@pytest.mark.asyncio
async def test_suggest_team_json_accepts_required_schema(monkeypatch):
    rag = _build_rag_fixture()

    monkeypatch.setattr("mkmchat.http_server.get_rag_system", lambda: rag)
    monkeypatch.setattr("mkmchat.http_server.get_ollama_assistant", lambda rag_system=None: _AssistantStub())
    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)

    payload = {
        "char1": {
            "name": "Klassic Scorpion",
            "rarity": "Diamond",
            "passive": "Applies fire damage.",
            "equipment": [
                {"slot": "weapon", "name": "Wrath Hammer", "effect": "Start with power"},
                {"slot": "armor", "name": "Hockey Mask", "effect": "Block break resist"},
                {"slot": "accessory", "name": "Soul Medallion", "effect": "Power generation"},
            ],
        },
        "char2": {
            "name": "Klassic Sub-Zero",
            "rarity": "Gold",
            "passive": "Applies freeze.",
            "equipment": [
                {"slot": "weapon", "name": "Wrath Hammer", "effect": "Start with power"},
                {"slot": "armor", "name": "Hockey Mask", "effect": "Block break resist"},
                {"slot": "accessory", "name": "Soul Medallion", "effect": "Power generation"},
            ],
        },
        "char3": {
            "name": "Klassic Raiden",
            "rarity": "Gold",
            "passive": "Power drain on tag-in.",
            "equipment": [
                {"slot": "weapon", "name": "Wrath Hammer", "effect": "Start with power"},
                {"slot": "armor", "name": "Hockey Mask", "effect": "Block break resist"},
                {"slot": "accessory", "name": "Soul Medallion", "effect": "Power generation"},
            ],
        },
        "strategy": "Control enemy power then finish with burst specials.",
    }

    _FakeAsyncClient.payload = {"response": json.dumps(payload)}
    result = await suggest_team_json("aggressive", model="llama3.2:3b")

    assert "response" in result
    assert result["response"]["char1"]["name"] == "Klassic Scorpion"
    assert result["response"]["char1"]["equipment"][0]["slot"] == "weapon"
    assert result["response"]["strategy"]
