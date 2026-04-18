from memory.conversation_memory import ConversationMemoryManager


def test_trim_history_keeps_latest_message_pairs():
    manager = ConversationMemoryManager(max_token_limit=2000)
    for idx in range(6):
        manager.add_user_message(f"u{idx}", "u1")
        manager.add_ai_message(f"a{idx}", "u1")

    manager.trim_history(user_id="u1", keep_last_pairs=2)
    history = manager.get_history("u1")

    assert "u5" in history
    assert "u4" in history
    assert "u0" not in history
