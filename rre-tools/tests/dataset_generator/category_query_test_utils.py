"""Shared helpers for category-query and main() wiring tests (not collected by pytest)."""

from __future__ import annotations

import types
from pathlib import Path
from types import SimpleNamespace
from typing import List

from rre_tools.dataset_generator import main as main_mod
from rre_tools.dataset_generator.config import Config
from rre_tools.shared.models import Document


def llm_cfg(tmp_path: Path) -> Path:
    p = tmp_path / "llm_cfg.yaml"
    p.write_text("name: mock\nmodel: mock-model\nmax_tokens: 16\n", encoding="utf-8")
    return p


def genre_query_template(tmp_path: Path) -> Path:
    p = tmp_path / "genre_query.tmpl"
    p.write_text("$query movies\n", encoding="utf-8")
    return p


def make_config(tmp_path: Path, **overrides) -> Config:
    base = dict(
        query_template=None,
        search_engine_type="solr",
        collection_name="testcore",
        search_engine_url="http://localhost:8983/solr/",
        documents_filter=None,
        number_of_docs=2,
        doc_fields=["title", "genres"],
        queries=None,
        generate_queries_from_documents=True,
        num_queries_needed=10,
        relevance_scale="graded",
        llm_configuration_file=llm_cfg(tmp_path),
        output_format="quepid",
        output_destination=tmp_path,
        save_llm_explanation=False,
        llm_explanation_destination=None,
        id_field=None,
        rre_query_template=None,
        rre_query_placeholder=None,
        verbose=False,
        datastore_autosave_every_n_updates=None,
        enable_cartesian_product=True,
    )
    base.update(overrides)
    return Config(**base)


class FakeSearchEngine:
    def __init__(self, docs: List[Document]):
        self._docs = docs
        self.fetch_calls = 0

    def fetch_for_query_generation(self, documents_filter, number_of_docs, doc_fields):
        self.fetch_calls += 1
        return list(self._docs)

    def fetch_field_values(self, values_query_template, field):
        raise AssertionError(
            "fetch_field_values should not be called for explicit-values configs"
        )


class FakeLLMService:
    def __init__(self, queries_per_doc=None, score=2):
        self._queries_per_doc = queries_per_doc or {}
        self._score = score
        self.generate_queries_calls = []
        self.generate_score_calls = []

    def generate_queries(self, doc, num_queries_per_doc, max_query_terms):
        self.generate_queries_calls.append(doc.id)
        queries = self._queries_per_doc.get(doc.id, [f"q-from-{doc.id}"])
        return SimpleNamespace(get_queries=lambda: queries)

    def generate_score(self, document, query, relevance_scale, explanation=False):
        self.generate_score_calls.append((document.id, query))
        score = self._score
        return SimpleNamespace(score=score, explanation=None, get_score=lambda: score)


class DummyWriter:
    def write(self, output_destination, data_store):
        return None


def patch_main_dependencies(monkeypatch, cfg, search_engine, llm_service, *,
                             stub_cartesian: bool = True):
    monkeypatch.setattr(main_mod, "Config", types.SimpleNamespace(load=lambda _path: cfg))
    monkeypatch.setattr(
        main_mod, "parse_args",
        lambda: types.SimpleNamespace(config="ignored.yaml", verbose=False),
    )
    monkeypatch.setattr(
        main_mod, "SearchEngineFactory",
        types.SimpleNamespace(build=lambda **kwargs: search_engine),
    )
    monkeypatch.setattr(main_mod, "LLMConfig", types.SimpleNamespace(load=lambda _path: object()))
    monkeypatch.setattr(
        main_mod, "LLMServiceFactory",
        types.SimpleNamespace(build=lambda _cfg: object()),
    )
    monkeypatch.setattr(main_mod, "LLMService", lambda chat_model: llm_service)
    monkeypatch.setattr(
        main_mod, "WriterFactory",
        types.SimpleNamespace(build=lambda _cfg: DummyWriter()),
    )
    if stub_cartesian:
        monkeypatch.setattr(main_mod, "add_cartesian_product_scores", lambda *a, **kw: None)
    monkeypatch.setattr(main_mod, "expand_docset_with_search_engine_top_k", lambda *a, **kw: None)


class ValueDiscoveryEngine:
    """Engine fake exposing only `fetch_field_values` (value-discovery path)."""

    def __init__(self, values_by_field=None):
        self._values_by_field = values_by_field or {}
        self.calls = []

    def fetch_field_values(self, values_query_template, field):
        self.calls.append((values_query_template, field))
        return list(self._values_by_field.get(field, []))


def empty_solr_facet_template(tmp_path: Path) -> Path:
    p = tmp_path / "facet_solr.json"
    p.write_text('{"q": "*:*", "facet": "true", "facet.field": "genres", "rows": 0}\n', encoding="utf-8")
    return p
