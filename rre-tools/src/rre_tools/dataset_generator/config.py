from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, HttpUrl, Field, field_validator, FilePath, model_validator
import yaml
import logging
from pathlib import Path
from urllib.parse import urljoin

from rre_tools.shared.search_engines import SearchEngineFactory
from rre_tools.shared.writers import WriterConfig

log = logging.getLogger(__name__)


class CategoryQuerySource(BaseModel):
    fields: List[str] = Field(..., min_length=1,
                              description="Fields used to derive category values. Only fields[0] is read.")
    values: Optional[List[str]] = Field(
        None,
        min_length=1,
        description="Explicit list of values used to render category queries. Mutually exclusive with "
                    "values_query_template_file (set exactly one)."
    )
    values_query_template_file: Optional[FilePath] = Field(
        None,
        description="Optional path to an engine-native value-discovery template "
                    "(Solr request-params JSON / ES or OpenSearch JSON request body / Vespa YQL). "
                    "When set, the engine returns the distinct values for fields[0] at run time. "
                    "Mutually exclusive with values (set exactly one)."
    )
    query_text_template_file: Optional[FilePath] = Field(
        None,
        description="Optional path to a plain-text natural-language template. Contents must contain the "
                    "engine's query placeholder ('@kw' for Vespa, '$query' for Solr/Elasticsearch/OpenSearch). "
                    "If omitted, each value is used directly as the query text (e.g. 'comedy', 'action')."
    )

    @field_validator('fields')
    @classmethod
    def check_no_empty_fields(cls, value_field: List[str]) -> List[str]:
        if any(not f.strip() for f in value_field):
            raise ValueError("category_queries.fields cannot contain empty strings.")
        return value_field

    @field_validator('values')
    @classmethod
    def check_no_empty_values(cls, value_field: Optional[List[str]]) -> Optional[List[str]]:
        # Field is now Optional so the validator must accept None — Pydantic still routes
        # None through the field validator on a typed-Optional field.
        if value_field is None:
            return value_field
        if any(not v.strip() for v in value_field):
            raise ValueError("category_queries.values cannot contain empty strings.")
        return value_field

    @model_validator(mode="after")
    def validate_single_field(self) -> "CategoryQuerySource":
        if len(self.fields) > 1:
            raise ValueError(
                "category_queries.fields with more than one entry is not yet supported."
            )
        return self

    @model_validator(mode="after")
    def validate_exactly_one_value_source(self) -> "CategoryQuerySource":
        """Exactly one of `values` (explicit list) or `values_query_template_file`
        (engine value-discovery template) must be set."""
        provided = sum(x is not None for x in (self.values, self.values_query_template_file))
        if provided != 1:
            raise ValueError(
                "category_queries entries must set exactly one of 'values' (explicit list) or "
                "'values_query_template_file' (engine facet/aggregation/grouping template)."
            )
        return self


class Config(BaseModel):
    query_template: Optional[FilePath] = Field(
        None,
        description="Path pointing to a template file for queries with a placeholder for keywords."
    )
    search_engine_type: Literal['solr', 'elasticsearch', 'opensearch', 'vespa']
    collection_name: str = Field(..., description="Name of the index/collection of the search engine")
    vespa_schema: Optional[str] = Field(None, description="Schema name for Vespa search engine")
    search_engine_url: HttpUrl = Field(..., description="Search engine URL")
    documents_filter: Optional[List[Dict[str, List[str]]]] = Field(
        None,
        description="Optional list of filter conditions for documents"
    )
    number_of_docs: int = Field(..., gt=0, description="Number of documents to retrieve from the search engine.")
    doc_fields: List[str] = Field(..., min_length=1, description="Fields used for context and scoring.")
    queries: Optional[FilePath] = Field(None, description="Optional file containing predefined queries.")
    generate_queries_from_documents: bool = True
    category_queries: Optional[List[CategoryQuerySource]] = Field(
        None,
        description="Optional list of category-derived query sources. Each source renders queries from "
                    "values of a configured field through a natural-language template."
    )
    num_queries_needed: int = Field(..., gt=0, description="Total number of queries to generate.")
    relevance_scale: Literal['binary', 'graded']
    llm_configuration_file: FilePath = Field(..., description="Path to the LLM configuration file.")
    max_query_terms: Optional[int] = Field(None, gt=0, description="Max number of query terms in the LLM-generated "
                                                                   "query")
    output_format: Literal['quepid', 'rre', 'mteb']
    output_destination: Path = Field(..., description="Path to save the output dataset.")
    save_llm_explanation: bool = False
    llm_explanation_destination: Optional[Path] = Field(None, description="Path to save the LLM rating explanation")
    id_field: Optional[str] = Field(None, description="ID field for the unique key.")
    rre_query_template: Optional[FilePath] = Field(None, description="Query template for rre evaluator.")
    rre_query_placeholder: Optional[str] = Field(None, description="Key-value pair to substitute in the rre query template.")
    verbose: bool = False
    datastore_autosave_every_n_updates: Optional[int] = Field(None, gt=0,
        description="If set, periodically persist datastore every N successful updates (adds/ratings)."
    )
    enable_cartesian_product: bool = Field(
        True,
        description="Enable cartesian product scoring between queries and documents used to generate queries."
    )

    def build_writer_config(self) -> WriterConfig:
        if self.rre_query_template is not None:
            query_template = self.rre_query_template.name
        else:
            if self.query_template is not None:
                query_template = self.query_template.name
            else:
                query_template = None


        return WriterConfig(
            output_format = self.output_format,
            index = self.collection_name,
            id_field = self.id_field,
            query_template = query_template,
            query_placeholder = self.rre_query_placeholder
        )

    @field_validator('doc_fields')
    @classmethod
    def check_no_empty_fields(cls, value_field: List[str]) -> List[str]:
        if any(not f.strip() for f in value_field):
            log.error("docFields cannot contain empty strings.")
            raise ValueError("docFields cannot contain empty strings.")
        return value_field

    @field_validator('queries')
    @classmethod
    def check_doc_type(cls, value_field: Optional[FilePath]) -> Optional[FilePath]:
        if value_field is not None and value_field.suffix[1:] != "txt" :
            log.error("queries' file must have .txt extension")
            raise ValueError("queries' file must have .txt extension")
        return value_field

    @field_validator('llm_configuration_file')
    @classmethod
    def check_config_type(cls, value_field: Optional[FilePath]) -> Optional[FilePath]:
        if value_field is not None and value_field.suffix[1:] not in {"yaml", "yml"}:
            log.error("LLM_config file must have .yaml extension")
            raise ValueError("LLM_config file must have .yaml extension")
        return value_field

    @model_validator(mode="after")
    def validate_llm_explanation_fields(self) -> "Config":
        if self.save_llm_explanation and self.llm_explanation_destination is None:
            raise ValueError("llm_explanation_destination must be set when save_llm_explanation is set to True.")
        return self

    @property
    def relevance_label_set(self) -> set[int]:
        """
        Returns the set of valid labels based on the relevance scale.
        """
        if self.relevance_scale == "binary":
            return {0, 1}
        elif self.relevance_scale == "graded":
            return {0, 1, 2}
        else:
            error_msg = f"Unknown relevance scale: {self.relevance_scale}"
            log.error(error_msg)
            raise ValueError(error_msg)

    @property
    def search_engine_collection_endpoint(self) -> HttpUrl:
        """
        Returns the collection endpoint URL for the search engine.
        For Vespa: uses vespa_schema in the endpoint, defaulting to collection_name.
        """
        if self.search_engine_type == "vespa":
            schema_name = self.vespa_schema or self.collection_name
            return HttpUrl(urljoin(self.search_engine_url.encoded_string() + "/", schema_name + "/"))
        else:
            # For other engines: use collection_name
            return HttpUrl(urljoin(self.search_engine_url.encoded_string() + "/", self.collection_name + "/"))

    @model_validator(mode="after")
    def check_rre_fields_required(self) -> "Config":
        if self.output_format == "rre" and not self.id_field:
            raise ValueError("id_field is required when output_format='rre'")
        elif self.output_format == "rre" and not self.rre_query_placeholder:
            raise ValueError("rre_query_placeholder is required when output_format='rre'")
        elif self.output_format == "rre" and not self.rre_query_template and not self.query_template:
            raise ValueError("At least one query template is required when output_format='rre'")
        return self

    @model_validator(mode="after")
    def default_vespa_schema_to_collection_name(self) -> "Config":
        if self.search_engine_type == "vespa" and not self.vespa_schema:
            self.vespa_schema = self.collection_name
        return self

    @model_validator(mode="after")
    def validate_category_query_fields_in_doc_fields(self) -> "Config":
        if self.category_queries is None:
            return self
        doc_fields_set = set(self.doc_fields)
        for source in self.category_queries:
            missing = [f for f in source.fields if f not in doc_fields_set]
            if missing:
                raise ValueError(
                    f"category_queries field(s) {missing} must also be present in doc_fields. "
                    f"The LLM scorer only sees fields fetched into the Document."
                )
        return self

    @property
    def category_query_placeholder(self) -> str:
        """Placeholder used inside category-query natural-language templates.

        Reuses the engine class's `QUERY_PLACEHOLDER` so the category template follows the
        same convention as the engine retrieval template ('$query' for Solr/ES/OpenSearch,
        '@kw' for Vespa).
        """
        return SearchEngineFactory.SEARCH_ENGINE_REGISTRY[self.search_engine_type].QUERY_PLACEHOLDER

    # NOTE on validator ordering: Pydantic runs `model_validator(mode="after")` validators in
    # declaration order. All path-collision validators must come BEFORE content-reading
    # validators (e.g. validate_category_query_template_placeholders), so that pointing
    # `query_text_template_file` at a value-discovery JSON file produces the informative
    # "different concepts" error rather than a misleading "missing placeholder" one.

    @model_validator(mode="after")
    def validate_category_template_paths_distinct(self) -> "Config":
        """Reject path collisions between category-source template files and other templates.

        Three rejected collisions per `CategoryQuerySource`:
          1. `query_text_template_file` == top-level `query_template` / `rre_query_template`
             — prevents using the engine retrieval payload as a natural-language template:
             substitution would dump Solr params JSON / Vespa YQL as the query string.
          2. `values_query_template_file` == top-level `query_template` / `rre_query_template`
             — same kind of misuse on the value-discovery side.
          3. `values_query_template_file` == `query_text_template_file` on the same source
             — the two fields cohabit on `CategoryQuerySource`, so swapping them is materially
             more likely than a generic file-path collision.
        """
        if self.category_queries is None:
            return self
        engine_template_paths = {
            p.resolve() for p in (self.query_template, self.rre_query_template) if p is not None
        }
        for source in self.category_queries:
            qt_path = source.query_text_template_file.resolve() if source.query_text_template_file else None
            vq_path = source.values_query_template_file.resolve() if source.values_query_template_file else None

            if qt_path is not None and qt_path in engine_template_paths:
                raise ValueError(
                    f"category_queries.query_text_template_file '{source.query_text_template_file}' "
                    f"points at the same file as the engine retrieval 'query_template' / "
                    f"'rre_query_template'. These are different concepts: the engine template is the "
                    f"retrieval payload (e.g. Vespa YQL, Solr params JSON, ES/OS request body); "
                    f"the category template is a "
                    f"natural-language query string template like '{self.category_query_placeholder} "
                    f"movies'. Create a separate plain-text file containing the placeholder "
                    f"('{self.category_query_placeholder}') and any surrounding wording, and point "
                    f"'query_text_template_file' at that."
                )

            if vq_path is not None and vq_path in engine_template_paths:
                raise ValueError(
                    f"category_queries.values_query_template_file '{source.values_query_template_file}' "
                    f"points at the same file as the engine retrieval 'query_template' / "
                    f"'rre_query_template'. These are different concepts: the engine retrieval "
                    f"template fetches documents for a given keyword, while the value-discovery "
                    f"template runs a facet / aggregation / grouping query that returns a list of "
                    f"distinct values for the configured field."
                )

            if vq_path is not None and qt_path is not None and vq_path == qt_path:
                raise ValueError(
                    f"category_queries.values_query_template_file and category_queries."
                    f"query_text_template_file on the same source point at the same file "
                    f"('{source.values_query_template_file}'). These are different concepts: "
                    f"values_query_template_file is the engine value-discovery payload (Solr "
                    f"params dict / ES or OpenSearch JSON body / Vespa YQL) that returns the list "
                    f"of distinct values; query_text_template_file is a plain-text natural-"
                    f"language template (e.g. '{self.category_query_placeholder} movies') that "
                    f"wraps each value into a query string."
                )
        return self

    @model_validator(mode="after")
    def validate_category_query_template_placeholders(self) -> "Config":
        if self.category_queries is None:
            return self
        placeholder = self.category_query_placeholder
        for source in self.category_queries:
            if source.query_text_template_file is None:
                continue  # bare-value mode: nothing to validate
            content = source.query_text_template_file.read_text(encoding="utf-8")
            if placeholder not in content:
                raise ValueError(
                    f"query_text_template_file '{source.query_text_template_file}' must contain the "
                    f"literal placeholder '{placeholder}' (the convention for "
                    f"search_engine_type='{self.search_engine_type}'). This file is the natural-"
                    f"language query template used to render category queries (e.g. "
                    f"'{placeholder} movies'); it is distinct from the engine retrieval template "
                    f"configured under top-level 'query_template' (Solr params JSON / Vespa YQL / etc.). "
                    f"Omit this field entirely to use each value as the query text directly."
                )
        return self

    @classmethod
    def load(cls, config_path: str) -> "Config":
        """
        Load and validate configuration from a YAML file.

        :param config_path: Path to the YAML config file
        :return: Parsed and validated Config object
        """
        path = Path(config_path)
        with path.open('r') as f:
            raw_config = yaml.safe_load(f)
            log.debug("Dataset Generator configuration file loaded successfully")
        return cls(**raw_config)
