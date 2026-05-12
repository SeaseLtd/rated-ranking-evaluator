"""Verify `main()` saves the datastore before re-raising a scoring failure."""
from __future__ import annotations

import types
from pathlib import Path

import pytest

from rre_tools.dataset_generator import main as main_mod
from rre_tools.dataset_generator.config import Config
from rre_tools.dataset_generator.llm import BatchScoringError


class DummyWriter:
    def write(self, output_destination, data_store):
        return None


def _build_cfg(tmp_path: Path) -> Config:
    llm_cfg = tmp_path / "llm_cfg.yaml"
    llm_cfg.write_text("name: mock\nmodel: mock-model\nmax_tokens: 16\n", encoding="utf-8")
    return Config(
        query_template=None,
        search_engine_type="solr",
        collection_name="testcore",
        search_engine_url="http://localhost:8983/solr/",
        documents_filter=None,
        number_of_docs=1,
        doc_fields=["title"],
        queries=None,
        generate_queries_from_documents=False,
        num_queries_needed=1,
        relevance_scale="binary",
        llm_configuration_file=llm_cfg,
        output_format="quepid",
        output_destination=tmp_path,
        save_llm_explanation=False,
        llm_explanation_destination=None,
        id_field=None,
        rre_query_template=None,
        rre_query_placeholder=None,
        verbose=False,
        datastore_autosave_every_n_updates=None,
        enable_cartesian_product=False,
    )


def _patch_factories(monkeypatch, cfg, *, save_recorder, raise_during_topk):
    monkeypatch.setattr(main_mod, "Config", types.SimpleNamespace(load=lambda _p: cfg))
    monkeypatch.setattr(main_mod, "parse_args",
                        lambda: types.SimpleNamespace(config="ignored.yaml", verbose=False))
    monkeypatch.setattr(main_mod, "SearchEngineFactory",
                        types.SimpleNamespace(build=lambda **kw: object()))
    monkeypatch.setattr(main_mod, "LLMConfig",
                        types.SimpleNamespace(load=lambda _p: object()))
    monkeypatch.setattr(main_mod, "LLMServiceFactory",
                        types.SimpleNamespace(build=lambda _cfg: object()))
    monkeypatch.setattr(main_mod, "WriterFactory",
                        types.SimpleNamespace(build=lambda _cfg: DummyWriter()))

    class _RecordingDataStore:
        def __init__(self, *_a, **_kw):
            self.save_calls = 0

        def save(self):
            self.save_calls += 1
            save_recorder.append(self.save_calls)

    monkeypatch.setattr(main_mod, "DataStore", _RecordingDataStore)
    monkeypatch.setattr(main_mod, "add_cartesian_product_scores",
                        lambda *_a, **_kw: None)

    def _raise(*_a, **_kw):
        raise raise_during_topk

    monkeypatch.setattr(main_mod, "expand_docset_with_search_engine_top_k", _raise)


def test_main__batch_scoring_error_during_scoring__triggers_save_then_reraises(
    tmp_path, monkeypatch,
):
    cfg = _build_cfg(tmp_path)
    save_calls: list[int] = []
    err = BatchScoringError(
        query_id="q1", asked_doc_ids=["d1"], attempts=4, reason="missing doc_id(s)",
    )
    _patch_factories(monkeypatch, cfg, save_recorder=save_calls, raise_during_topk=err)

    with pytest.raises(BatchScoringError):
        main_mod.main()

    # save() was called before the exception propagated.
    assert save_calls == [1]


def test_main__plain_exception_during_scoring__also_triggers_save_then_reraises(
    tmp_path, monkeypatch,
):
    cfg = _build_cfg(tmp_path)
    save_calls: list[int] = []
    err = RuntimeError("search engine timeout")
    _patch_factories(monkeypatch, cfg, save_recorder=save_calls, raise_during_topk=err)

    with pytest.raises(RuntimeError, match="search engine timeout"):
        main_mod.main()

    assert save_calls == [1]


def test_main__failing_save_does_not_mask_original_scoring_error(
    tmp_path, monkeypatch,
):
    cfg = _build_cfg(tmp_path)
    _patch_factories(monkeypatch, cfg, save_recorder=[],
                     raise_during_topk=RuntimeError("scoring blew up"))

    # Replace DataStore with one whose save() always raises.
    class _BrokenSaveDataStore:
        def __init__(self, *_a, **_kw):
            pass

        def save(self):
            raise OSError("disk full")

    monkeypatch.setattr(main_mod, "DataStore", _BrokenSaveDataStore)

    with pytest.raises(RuntimeError, match="scoring blew up"):
        main_mod.main()


def _patch_factories_with_failing_step(monkeypatch, cfg, *, failing_step_name, err, save_recorder):
    """Patch main_mod factories and make ``failing_step_name`` raise.

    Covers the contract: any failure during the work phase (query sources,
    seed fetch, query generation, scoring) triggers save-before-reraise.
    """
    monkeypatch.setattr(main_mod, "Config", types.SimpleNamespace(load=lambda _p: cfg))
    monkeypatch.setattr(main_mod, "parse_args",
                        lambda: types.SimpleNamespace(config="ignored.yaml", verbose=False))
    monkeypatch.setattr(main_mod, "SearchEngineFactory",
                        types.SimpleNamespace(build=lambda **kw: object()))
    monkeypatch.setattr(main_mod, "LLMConfig",
                        types.SimpleNamespace(load=lambda _p: object()))
    monkeypatch.setattr(main_mod, "LLMServiceFactory",
                        types.SimpleNamespace(build=lambda _cfg: object()))
    monkeypatch.setattr(main_mod, "WriterFactory",
                        types.SimpleNamespace(build=lambda _cfg: DummyWriter()))

    class _RecordingDataStore:
        def __init__(self, *_a, **_kw):
            self.save_calls = 0

        def save(self):
            self.save_calls += 1
            save_recorder.append(self.save_calls)

    monkeypatch.setattr(main_mod, "DataStore", _RecordingDataStore)

    # No-op stubs for the steps we don't want to exercise. The failing
    # step is monkeypatched last so it wins.
    for name in (
        "add_user_queries",
        "add_category_queries",
        "fetch_and_add_seed_documents",
        "generate_and_add_queries_from_documents",
        "add_cartesian_product_scores",
        "expand_docset_with_search_engine_top_k",
    ):
        monkeypatch.setattr(main_mod, name, lambda *_a, **_kw: None)

    def _raise(*_a, **_kw):
        raise err

    monkeypatch.setattr(main_mod, failing_step_name, _raise)


@pytest.mark.parametrize("failing_step", [
    "add_user_queries",
    "add_category_queries",
    "fetch_and_add_seed_documents",
    "generate_and_add_queries_from_documents",
])
def test_main__failure_in_any_work_phase_step__triggers_save_then_reraises(
    tmp_path, monkeypatch, failing_step,
):
    """Save-on-failure must cover the entire work phase, not just scoring.

    Regression for the case where ``generate_and_add_queries_from_documents``
    raised after earlier seed-doc responses had already been applied — those
    in-memory queries and pre-ratings used to vanish on the exception.
    """
    cfg = _build_cfg(tmp_path)
    # Enable enough of the pipeline that the patched step is actually reached.
    cfg.generate_queries_from_documents = True
    cfg.enable_cartesian_product = True

    save_calls: list[int] = []
    err = RuntimeError(f"{failing_step} blew up")
    _patch_factories_with_failing_step(
        monkeypatch, cfg, failing_step_name=failing_step, err=err, save_recorder=save_calls,
    )

    with pytest.raises(RuntimeError, match=f"{failing_step} blew up"):
        main_mod.main()

    assert save_calls == [1], (
        f"save() was not invoked on failure in {failing_step}. The work-phase "
        f"try/except in main() must cover this step or partial in-memory state is lost."
    )
