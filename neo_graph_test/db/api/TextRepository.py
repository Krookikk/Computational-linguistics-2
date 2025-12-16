import pickle

from db.models import Text

class TextRepository:
    def collect_text(self, text: Text):
        return {
            "id": text.id,
            "name": text.name,
            "description": text.description,
            "content": text.content,
            "corpus_id": text.corpus_id,
            "has_translation": text.has_translation_id,
            "embedding": pickle.loads(text.embedding) if text.embedding else None
        }

    def create(self, data):
        text = Text.objects.create(**data)
        return self.collect_text(text)

    def update(self, text_id, data):
        text = Text.objects.get(id=text_id)
        for k, v in data.items():
            setattr(text, k, v)
        text.save()
        return self.collect_text(text)

    def get(self, text_id):
        return self.collect_text(Text.objects.get(id=text_id))

    def delete(self, text_id):
        Text.objects.filter(id=text_id).delete()
        return text_id