from rag.embeddings import EmbeddingManager, _resolve_embedding_dimension


def test_embed_query_uses_configured_embedding_function_once():
    manager = EmbeddingManager(model_name="fake-model")
    calls = []

    def fake_embed(texts):
        calls.append(texts)
        return [[0.1, 0.2] for _ in texts]

    manager._embedding_fn = fake_embed
    result = manager.embed_query("hello")

    assert result == [0.1, 0.2]
    assert calls == [["hello"]]


class ModelWithSentenceEmbeddingDimension:
    def get_sentence_embedding_dimension(self):
        return 768


class ModelWithLegacyEmbeddingDimension:
    def get_embedding_dimension(self):
        return 384


def test_resolve_embedding_dimension_prefers_sentence_transformers_api():
    assert _resolve_embedding_dimension(ModelWithSentenceEmbeddingDimension()) == 768


def test_resolve_embedding_dimension_supports_legacy_api():
    assert _resolve_embedding_dimension(ModelWithLegacyEmbeddingDimension()) == 384


def test_resolve_embedding_dimension_falls_back_to_default():
    assert _resolve_embedding_dimension(object()) == 512
