import pytest

from mkmchat.http_server import _compact_chat_history, _sanitize_chat_messages


class _AssistantStub:
    pass


def test_sanitize_chat_messages_filters_invalid_payloads():
    payload = [
        {"role": "user", "content": "  hi  "},
        {"role": "assistant", "content": "ok"},
        {"role": "system", "content": "skip"},
        {"role": "user", "content": "   "},
        "invalid",
    ]

    result = _sanitize_chat_messages(payload)

    assert result == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "ok"},
    ]


@pytest.mark.asyncio
async def test_compact_chat_history_keeps_recent_without_trigger(monkeypatch):
    monkeypatch.setenv("MKM_CHAT_KEEP_RECENT_MESSAGES", "4")
    monkeypatch.setenv("MKM_CHAT_COMPACT_TRIGGER_MESSAGES", "20")

    messages = [{"role": "user", "content": f"m{i}"} for i in range(8)]

    summary, summary_count, recent = await _compact_chat_history(
        assistant=_AssistantStub(),
        use_model="llama3.2:3b",
        messages=messages,
        existing_summary="",
        existing_summary_count=0,
    )

    assert summary in (None, "")
    assert summary_count == 0
    assert recent == messages


@pytest.mark.asyncio
async def test_compact_chat_history_summarizes_older_messages(monkeypatch):
    monkeypatch.setenv("MKM_CHAT_KEEP_RECENT_MESSAGES", "3")
    monkeypatch.setenv("MKM_CHAT_COMPACT_TRIGGER_MESSAGES", "6")

    async def _fake_summary(assistant, use_model, existing_summary, messages_to_summarize):
        assert len(messages_to_summarize) == 5
        return "Compacted summary"

    monkeypatch.setattr("mkmchat.http_server._summarize_messages", _fake_summary)

    messages = [{"role": "user", "content": f"m{i}"} for i in range(8)]

    summary, summary_count, recent = await _compact_chat_history(
        assistant=_AssistantStub(),
        use_model="llama3.2:3b",
        messages=messages,
        existing_summary="existing",
        existing_summary_count=2,
    )

    assert summary == "Compacted summary"
    assert summary_count == 7
    assert recent == messages[-3:]
