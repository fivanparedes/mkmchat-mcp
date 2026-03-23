import pytest

from mkmchat import server


@pytest.mark.asyncio
async def test_call_tool_dispatches_to_registered_handler(monkeypatch):
    async def fake_get_character_info(character_name: str):
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"character={character_name}",
                }
            ]
        }

    monkeypatch.setattr(server, "get_character_info", fake_get_character_info)

    result = await server.call_tool("get_character_info", {"character_name": "Scorpion"})

    assert result["content"][0]["text"] == "character=Scorpion"


@pytest.mark.asyncio
async def test_call_tool_returns_error_for_unknown_tool():
    result = await server.call_tool("nonexistent_tool", {})

    assert "content" in result
    assert result["content"][0]["type"] == "text"
    assert "Unknown tool" in result["content"][0]["text"]
