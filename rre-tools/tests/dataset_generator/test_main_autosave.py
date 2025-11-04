import types
from pathlib import Path


from rre_tools.dataset_generator import main as main_mod
from rre_tools.dataset_generator.config import Config


class DummyWriter:
    def write(self, output_destination, data_store):
        # no-op writer
        return None


def test_main_passes_autosave_option_to_datastore(monkeypatch, tmp_path: Path):
    # Prepare a minimal valid LLM config file (so Config validation can pass if needed)
    llm_cfg = tmp_path / "llm_cfg.yaml"
    llm_cfg.write_text("""
name: mock
model: mock-model
max_tokens: 16
""".strip())

    # Build a valid Config object programmatically
    cfg = Config(
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
        relevance_scale="graded",
        llm_configuration_file=llm_cfg,
        output_format="quepid",
        output_destination=tmp_path,
        save_llm_explanation=False,
        llm_explanation_destination=None,
        id_field=None,
        rre_query_template=None,
        rre_query_placeholder=None,
        verbose=False,
        datastore_autosave_every_n_updates=7,
    )

    # Patch Config.load to return our in-memory cfg (bypass reading from disk)
    monkeypatch.setattr(main_mod, "Config", types.SimpleNamespace(load=lambda _path: cfg))

    # Patch parse_args to avoid CLI dependency
    monkeypatch.setattr(main_mod, "parse_args", lambda: types.SimpleNamespace(config="ignored.yaml", verbose=False))

    # Patch factories to avoid network / heavy dependencies
    monkeypatch.setattr(main_mod, "SearchEngineFactory", types.SimpleNamespace(build=lambda **kwargs: object()))
    monkeypatch.setattr(main_mod, "LLMConfig", types.SimpleNamespace(load=lambda _path: object()))
    monkeypatch.setattr(main_mod, "LLMServiceFactory", types.SimpleNamespace(build=lambda _cfg: object()))
    monkeypatch.setattr(main_mod, "WriterFactory", types.SimpleNamespace(build=lambda _cfg: DummyWriter()))

    # No-op the heavy flow functions to keep the test focused on wiring
    monkeypatch.setattr(main_mod, "generate_and_add_queries", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_mod, "add_cartesian_product_scores", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_mod, "expand_docset_with_search_engine_top_k", lambda *args, **kwargs: None)

    # Replace DataStore with a dummy that captures the autosave parameter
    class DummyDataStore:
        captured_autosave = None

        def __init__(self, *args, **kwargs):
            DummyDataStore.captured_autosave = kwargs.get("autosave_every_n_updates")

        def save(self):
            return None

    monkeypatch.setattr(main_mod, "DataStore", DummyDataStore)

    # Execute main and verify the autosave option is passed through
    main_mod.main()

    assert DummyDataStore.captured_autosave == 7
