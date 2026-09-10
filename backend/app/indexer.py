import hashlib

from openai import OpenAI
from pgvector.psycopg import register_vector

from app.config import settings
from app.database import get_connection
from app.rag import load_documents, chunk_text


def calculate_document_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def index_knowledge_base():
    client = OpenAI(api_key=settings.openai_api_key)

    documents = load_documents()

    with get_connection() as connection:
        register_vector(connection)

        with connection.cursor() as cursor:
            for document in documents:
                source_name = document["source_name"]
                content = document["content"]

                current_hash = calculate_document_hash(content)

                cursor.execute(
                    """
                    SELECT document_hash
                    FROM indexed_documents
                    WHERE source_name = %s;
                    """,
                    (source_name,),
                )

                row = cursor.fetchone()

                if row is not None and row[0] == current_hash:
                    print(f"Skipping unchanged document: {source_name}")
                    continue

                cursor.execute(
                    """
                    DELETE FROM document_chunks
                    WHERE source_name = %s;
                    """,
                    (source_name,),
                )

                chunks = chunk_text(content)

                for chunk in chunks:
                    response = client.embeddings.create(
                        model=settings.embedding_model,
                        input=chunk,
                    )

                    embedding = response.data[0].embedding

                    cursor.execute(
                        """
                        INSERT INTO document_chunks (
                            source_name,
                            source_type,
                            content,
                            access_level,
                            embedding
                        )
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (
                            source_name,
                            document["source_type"],
                            chunk,
                            document["access_level"],
                            embedding,
                        ),
                    )

                cursor.execute(
                    """
                    INSERT INTO indexed_documents (
                        source_name,
                        document_hash,
                        last_indexed_at
                    )
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (source_name)
                    DO UPDATE SET
                        document_hash = EXCLUDED.document_hash,
                        last_indexed_at = NOW();
                    """,
                    (
                        source_name,
                        current_hash,
                    ),
                )

                print(f"Indexed document: {source_name}")

        connection.commit()