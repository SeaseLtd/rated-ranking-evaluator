from pydantic import BaseModel, Field, create_model, conlist, constr


def create_queries_schema(num_queries_generate: int) -> type[BaseModel]:
    """
    Returns a Pydantic model that enforces `queries` to be a list of exactly
    `num_queries_generate` and non-empty strings. Used to validate LLM output.
    """
    cleaned_query = constr(strip_whitespace=True, min_length=1)

    exact_num_queries = conlist(cleaned_query, min_length=num_queries_generate,
                                max_length=num_queries_generate)

    schema = create_model(
        "LLMQueries",
        queries=(exact_num_queries, Field(...,
                                          description=f"Return exactly {num_queries_generate} "
                                                      f"distinct queries as plain strings.")),
    )
    return schema
