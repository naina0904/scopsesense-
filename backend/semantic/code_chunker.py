class CodeChunker:

    # Minimum meaningful chunk length (chars) before sending to embeddings.
    # Prevents trivially short or whitespace-only chunks from polluting
    # the vector store with near-zero semantic signal.
    MIN_CHUNK_LENGTH = 20

    def chunk_documents(
        self,
        documents,
        chunk_size=1000
    ):

        chunks = []

        for doc in documents:

            content = doc["content"]

            for i in range(
                0,
                len(content),
                chunk_size
            ):

                chunk = content[i:i + chunk_size]

                # ─────────────────────────────────────────
                # CHUNK SANITATION
                # Binary safety net: skip any chunk that
                # contains null bytes. A valid source file
                # should never contain them; their presence
                # indicates binary content that leaked past
                # the parser (e.g., a compiled artefact with
                # a .py extension). Sending binary chunks to
                # the SentenceTransformer model corrupts the
                # embedding space.
                # ─────────────────────────────────────────
                if "\x00" in chunk:
                    continue

                # Skip trivially short or whitespace-only chunks
                if len(chunk.strip()) < self.MIN_CHUNK_LENGTH:
                    continue

                chunks.append({
                    "path": doc["path"],
                    "content": chunk
                })

        print(
            f"[CodeChunker] Chunking complete. Generated {len(chunks)} "
            f"text chunks (chunk_size={chunk_size}) from {len(documents)} "
            f"input documents."
        )

        return chunks