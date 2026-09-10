from openai import OpenAI
from pgvector.psycopg import register_vector

from app.config import settings
from app.database import get_connection
def search_knowledge_base(
    query: str,
    limit: int = 3,
    min_similarity: float = 0.35,
    relative_similarity_ratio: float = 0.75,
) -> list[dict]:
    query = query.strip()

    if not query:
        return []

    client = OpenAI(
        api_key=settings.openai_api_key
    )

    response = client.embeddings.create(
        model=settings.embedding_model,
        input=query,
    )

    query_embedding = response.data[0].embedding

    # Retrieve a slightly larger candidate set first.
    # Final filtering happens below.
    candidate_limit = max(limit * 3, 10)

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    source_name,
                    content,
                    access_level,
                    1 - (embedding <=> %s::vector) AS similarity
                FROM document_chunks
                WHERE access_level = %s
                AND 1 - (embedding <=> %s::vector) >= %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
                """,
                (
                    query_embedding,
                    "general",
                    query_embedding,
                    min_similarity,
                    query_embedding,
                    candidate_limit,
                ),
            )

            rows = cursor.fetchall()

    results = [
        {
            "source_name": row[0],
            "content": row[1],
            "access_level": row[2],
            "similarity": float(row[3]),
        }
        for row in rows
    ]

    if not results:
        return []

    best_similarity = results[0]["similarity"]

    relative_cutoff = max(
        min_similarity,
        best_similarity * relative_similarity_ratio,
    )

    filtered_results = [
        result
        for result in results
        if result["similarity"] >= relative_cutoff
    ]

    return filtered_results[:limit]