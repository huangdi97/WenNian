"""Tests for knowledge retrieval module."""

import pytest
from src.knowledge import LiteratureRetriever, SimpleVectorStore, LITERATURE_ABSTRACTS


class TestSimpleVectorStore:
    def test_add_and_search(self):
        store = SimpleVectorStore()
        store.add_documents([
            {"abstract": "免疫衰老与T细胞功能衰退", "keywords": ["免疫", "T细胞"]},
            {"abstract": "表观遗传时钟与DNA甲基化", "keywords": ["表观遗传", "DNA"]},
        ])
        results = store.search("免疫 T细胞", top_k=2)
        assert len(results) > 0

    def test_empty_search(self):
        store = SimpleVectorStore()
        results = store.search("anything", top_k=5)
        assert results == []

    def test_chinese_tokenization(self):
        store = SimpleVectorStore()
        store.add_documents([
            {"abstract": "血管衰老是全身衰老的先锋", "keywords": ["血管"]},
        ])
        results = store.search("血管衰老", top_k=3)
        assert len(results) > 0


class TestLiteratureRetriever:
    @pytest.fixture
    def retriever(self):
        return LiteratureRetriever()

    def test_has_abstracts(self, retriever):
        assert len(LITERATURE_ABSTRACTS) >= 20

    def test_retrieve(self, retriever):
        results = retriever.retrieve("免疫衰老 T细胞", top_k=3)
        assert len(results) > 0
        assert any(r.get("dimension") == "immune" for r in results)

    def test_dimension_filter(self, retriever):
        results = retriever.retrieve("aging", top_k=5, dimension_filter="immune")
        for r in results:
            assert r.get("dimension") == "immune"

    def test_get_by_dimension(self, retriever):
        results = retriever.get_by_dimension("organ")
        assert len(results) > 0
        for r in results:
            assert r.get("dimension") == "organ"

    def test_search_by_keyword(self, retriever):
        results = retriever.search_by_keyword("RUNX1", top_k=5)
        assert len(results) > 0
        assert any("RUNX1" in str(r.get("abstract", "")) for r in results)

    def test_retrieve_empty_query(self, retriever):
        results = retriever.retrieve("", top_k=3)
        assert isinstance(results, list)
