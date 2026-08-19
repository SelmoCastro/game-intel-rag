import hashlib
import math
import re

EMBEDDING_DIMENSIONS = 256


class EmbeddingService:
    """Embedding local determinístico para testes e primeira versão.

    A dimensão é fixa para manter compatibilidade com pgvector. Um provedor
    semântico externo pode substituir esta classe sem alterar o repositório.
    """

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIMENSIONS
        tokens = re.findall(r"[\wÀ-ÿ]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
            sign = 1.0 if digest[4] % 2 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [round(value / norm, 8) for value in vector]

    @staticmethod
    def as_pgvector(values: list[float]) -> str:
        return "[" + ",".join(str(value) for value in values) + "]"
