import pickle
from typing import List, Union

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingUtils:
    """
    Утилиты для работы с эмбеддингами текстов
    """

    _model = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """
        Lazy-loading модели эмбеддингов
        (чтобы не загружать её несколько раз)
        """
        if cls._model is None:
            cls._model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
            )
        return cls._model

    # -------------------------
    # Разбиение текста
    # -------------------------
    """
    Разбивает текст на фрагменты (чанки)

    :param text: исходный текст
    :param chunk_size: количество слов в чанке
    :param overlap: перекрытие между чанками
    """
    @staticmethod
    def get_chunks(
        text: str,
        chunk_size: int = 50,
        overlap: int = 10
    ) -> List[str]:

        if not text:
            return []

        words = text.split()
        chunks = []

        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    # -------------------------
    # Генерация эмбеддингов
    # -------------------------
    @classmethod
    def get_embedding(cls, text: str) -> np.ndarray:
        """
        Генерирует эмбеддинг одного текста
        """
        model = cls.get_model()
        return model.encode(text)

    @classmethod
    def get_embeddings(cls, texts: List[str]) -> np.ndarray:
        """
        Генерирует эмбеддинги для списка текстов
        """
        model = cls.get_model()
        return model.encode(texts)

    # -------------------------
    # Сериализация для БД
    # -------------------------
    @staticmethod
    def serialize(vector: np.ndarray) -> bytes:
        """
        Преобразует embedding в bytes для хранения в БД
        """
        return pickle.dumps(vector)

    @staticmethod
    def deserialize(data: bytes) -> np.ndarray:
        """
        Восстанавливает embedding из bytes
        """
        return pickle.loads(data)

    # -------------------------
    # Косинусное сходство
    # -------------------------
    """
    Вычисляет косинусное сходство между двумя эмбеддингами
    """
    @staticmethod
    def cos_compare(
        vec1: Union[np.ndarray, bytes],
        vec2: Union[np.ndarray, bytes]
    ) -> float:

        if isinstance(vec1, bytes):
            vec1 = EmbeddingUtils.deserialize(vec1)

        if isinstance(vec2, bytes):
            vec2 = EmbeddingUtils.deserialize(vec2)

        return float(
            cosine_similarity(
                [np.array(vec1)],
                [np.array(vec2)]
            )[0][0]
        )
