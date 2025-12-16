from db.models import Corpus

class CorpusRepository:
    def collect_corpus(self, corpus: Corpus):
        return {
            "id": corpus.id,
            "name": corpus.name,
            "description": corpus.description,
            "genre": corpus.genre,
            "texts": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description
                } for t in corpus.texts.all()
            ]
        }

    def create(self, data):
        corpus = Corpus.objects.create(**data)
        return self.collect_corpus(corpus)

    def update(self, corpus_id, data):
        corpus = Corpus.objects.get(id=corpus_id)
        for k, v in data.items():
            setattr(corpus, k, v)
        corpus.save()
        return self.collect_corpus(corpus)

    def get(self, corpus_id):
        corpus = Corpus.objects.get(id=corpus_id)
        return self.collect_corpus(corpus)

    def delete(self, corpus_id):
        Corpus.objects.filter(id=corpus_id).delete()
        return corpus_id
