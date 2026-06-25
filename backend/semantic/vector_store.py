import hashlib
import re

import chromadb


class VectorStore:

    def __init__(

        self,

        namespace="default"
    ):

        self.client = chromadb.PersistentClient(
            path="data/chroma"
        )

        self.namespace = self._normalize_namespace(
            namespace
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=(
                    f"scopesense_{self.namespace}"
                )
            )
        )

    def add_documents(
        self,
        documents,
        embeddings,
        namespace=None
    ):

        ids = [

            self._document_id(
                "doc",
                document,
                index,
                namespace
            )

            for index, document in enumerate(
                documents
            )
        ]

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=[

                {
                    "namespace":
                        namespace
                        or self.namespace,

                    "kind":
                        "document"
                }

                for _ in documents
            ]
        )

    def similarity_search(
        self,
        query_embedding,
        top_k=5
    ):

        results = self.collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=top_k
        )

        return results

    def index_code_chunks(
        self,
        chunks,
        embedding_engine,
        namespace=None
    ):

        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = [
            embedding_engine.generate_embedding(
                text
            )
            for text in texts
        ]

        ids = [

            self._document_id(
                "chunk",
                chunk["content"],
                index,
                namespace
            )

            for index, chunk in enumerate(
                chunks
            )
        ]

        metadatas = [
            {
                "path": chunk["path"],

                "namespace":
                    namespace
                    or self.namespace,

                "kind":
                    "code_chunk",

                "chunk_index":
                    index
            }
            for index, chunk in enumerate(
                chunks
            )
        ]

        print(
            f"[VectorStore] Generating embeddings and indexing {len(chunks)} "
            f"chunks into ChromaDB namespace '{namespace or self.namespace}'..."
        )

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(
            f"[VectorStore] Indexing complete. Upserted {len(chunks)} chunks "
            f"into ChromaDB collection '{self.collection.name}' successfully."
        )

    def semantic_search(
        self,
        query,
        embedding_engine,
        top_k=5,
        namespace=None
    ):

        query_embedding = (
            embedding_engine.generate_embedding(
                query
            )
        )

        where = None

        if namespace:

            where = {

                "namespace":
                    namespace
            }

        query_args = {

            "query_embeddings": [
                query_embedding
            ],

            "n_results":
                top_k
        }

        if where:

            query_args[
                "where"
            ] = where

        results = self.collection.query(
            **query_args
        )

        return self._with_confidence(
            results
        )

    def search_similar_commits(

        self,

        query,

        limit=10,

        namespace=None
    ):

        where = None

        if namespace:

            where = {

                "namespace":
                    namespace
            }

        query_args = {

            "query_texts": [
                query
            ],

            "n_results":
                limit
        }

        if where:

            query_args[
                "where"
            ] = where

        results = self.collection.query(
            **query_args
        )

        return self._with_confidence(
            results
        )

    def _document_id(

        self,

        prefix,

        content,

        index,

        namespace=None
    ):

        selected_namespace = (
            namespace
            or self.namespace
        )

        digest = hashlib.md5(
            str(content).encode()
        ).hexdigest()

        return (
            f"{selected_namespace}_{prefix}_{index}_{digest[:12]}"
        )

    def _normalize_namespace(

        self,

        namespace
    ):

        cleaned = re.sub(
            r"[^a-zA-Z0-9_]",
            "_",
            namespace
        )

        return cleaned[:48] or "default"

    def _with_confidence(

        self,

        results
    ):

        distances = results.get(
            "distances",
            []
        )

        if distances:

            results[
                "confidence"
            ] = [

                [

                    round(
                        max(
                            0,
                            1 - distance
                        ),
                        4
                    )

                    for distance in row
                ]

                for row in distances
            ]

        return results
