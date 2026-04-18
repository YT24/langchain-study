from chains.orchestrator import redact_for_log


def test_redact_for_log_masks_user_id_and_order_no():
    text = "userId=u123456 orderNo=ORD0001 amount=999"
    redacted = redact_for_log(text)
    assert "u123456" not in redacted
    assert "ORD0001" not in redacted
