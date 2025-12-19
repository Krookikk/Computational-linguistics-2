import pickle

from django.db import models
from db_file_storage.model_utils import delete_file, delete_file_if_needed
from sentence_transformers import SentenceTransformer

from db.api.EmbeddingUtils import EmbeddingUtils

# embedding_model = SentenceTransformer(
#     "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
# )

class Test(models.Model):
    name = models.TextField()

    def __str__(self):
        return self.name  # Returns the value of the 'name' field

class Corpus(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    genre = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Text(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    content = models.TextField()
    corpus = models.ForeignKey(
        Corpus,
        related_name='texts',
        on_delete=models.CASCADE
    )
    has_translation = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    embedding = models.BinaryField(null=True, blank=True)

    def save(self, *args, **kwargs):
        """
        При сохранении текста автоматически вычисляется embedding
        и сохраняется в базе данных
        """
        if self.content:
            vector = EmbeddingUtils.get_embedding(self.content)
            self.embedding = EmbeddingUtils.serialize(vector)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
