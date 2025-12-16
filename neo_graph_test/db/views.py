from django.shortcuts import render
from django.http import StreamingHttpResponse, HttpResponseRedirect, HttpResponse
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import datetime
from django.db.models import Q

from.onthology_namespace import *
from .models import Test, Text, Corpus, embedding_model
from core.settings import *

# API IMPORTS
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

# REPO IMPORTS
from db.api.TestRepository import TestRepository
from db.api.OntologyRepository import OntologyRepository
from db.api.DriverRepository import DriverRepository
from db.api.CorpusRepository import CorpusRepository
from db.api.TextRepository import TextRepository
from db.api.EmbeddingUtils import EmbeddingUtils

# driver_repo = DriverRepository()
text_repo = TextRepository()

@api_view(['GET', ])
@permission_classes((AllowAny,))
def getTest(request):
    id = request.GET.get('id', None)
    if id is None:
        return HttpResponse(status=400)

    testRepo = TestRepository()
    result = testRepo.getTest(id = id)
    return Response(result)

@api_view(['POST', ])
@permission_classes((IsAuthenticated,))
def postTest(request):
    data = json.loads(request.body.decode('utf-8'))
    testRepo = TestRepository()
    test = testRepo.postTest(test_data = data)
    return JsonResponse(test)

@api_view(['DELETE', ])
@permission_classes((AllowAny,))
def deleteTest(request):
    id = request.GET.get('id', None)
    if id is None:
        return HttpResponse(status=400)

    testRepo = TestRepository()
    result = testRepo.deleteTest(id = id)
    return Response(result)
# ------------------------------------------

@api_view(['POST'])
@permission_classes((AllowAny,))
def create_corpus(request):
    data = request.data

    required_fields = ('name', 'description', 'genre')
    missing = [f for f in required_fields if not data.get(f)]

    if missing:
        return Response(
            {"error": f"Missing fields: {', '.join(missing)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    repo = CorpusRepository()

    try:
        corpus = repo.create({
            "name": data["name"],
            "description": data["description"],
            "genre": data["genre"]
        })
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(corpus, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_corpus(request):
    corpus_id = request.GET.get("id")

    if not corpus_id:
        return Response(
            {"error": "Missing 'id' query parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    repo = CorpusRepository()

    try:
        corpus = repo.get(corpus_id)
    except Corpus.DoesNotExist:
        return Response(
            {"error": "Corpus not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(corpus)

@api_view(['PUT'])
@permission_classes((AllowAny,))
def update_corpus(request):
    data = request.data
    corpus_id = data.get("id")

    if not corpus_id:
        return Response(
            {"error": "Missing 'id' field"},
            status=status.HTTP_400_BAD_REQUEST
        )

    allowed_fields = {"name", "description", "genre"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not update_data:
        return Response(
            {"error": "No fields to update"},
            status=status.HTTP_400_BAD_REQUEST
        )

    repo = CorpusRepository()

    try:
        corpus = repo.update(corpus_id, update_data)
    except Corpus.DoesNotExist:
        return Response(
            {"error": "Corpus not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(corpus)

@api_view(['DELETE'])
@permission_classes((AllowAny,))
def delete_corpus(request):
    corpus_id = request.GET.get("id")

    if not corpus_id:
        return Response(
            {"error": "Missing 'id' query parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    repo = CorpusRepository()

    deleted = repo.delete(corpus_id)
    if not deleted:
        return Response(
            {"error": "Corpus not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({"deleted_id": corpus_id})

# ------------------------------

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_ontology(request):
    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        data = repo.get_ontology()
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_ontology_parent_classes(request):
    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        data = repo.get_ontology_parent_classes()
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_class(request):
    class_uri = request.GET.get("uri")

    if not class_uri:
        return Response(
            {"error": "Missing 'uri' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        cls = repo.get_class(class_uri)

        if not cls:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    finally:
        driver.close()

    return Response(cls, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_class_parents(request):
    class_uri = request.GET.get("uri")

    if not class_uri:
        return Response(
            {"error": "Missing 'uri' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        data = repo.get_class_parents(class_uri)
    finally:
        driver.close()

    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_class_children(request):
    class_uri = request.GET.get("uri")

    if not class_uri:
        return Response(
            {"error": "Missing 'uri' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        data = repo.get_class_children(class_uri)
    finally:
        driver.close()

    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_class_objects(request):
    class_uri = request.GET.get("uri")

    if not class_uri:
        return Response(
            {"error": "Missing 'uri' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        data = repo.get_class_objects(class_uri)
    finally:
        driver.close()

    return Response(data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny,))
def create_class(request):
    data = request.data

    if not data.get("title") or not data.get("description"):
        return Response(
            {"error": "Missing 'title' or 'description'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        cls = repo.create_class(
            title=data["title"],
            description=data["description"],
            parent_uri=data.get("parent_uri")
        )
    finally:
        driver.close()

    return Response(cls, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes((AllowAny,))
def update_class(request):
    data = request.data

    if not data.get("uri"):
        return Response(
            {"error": "Missing 'uri'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        cls = repo.update_class(
            data["uri"],
            data.get("title", ""),
            data.get("description", "")
        )

        if not cls:
            return Response(
                {"error": "Class not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    finally:
        driver.close()

    return Response(cls, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes((AllowAny,))
def delete_class(request):
    class_uri = request.GET.get("uri")

    if not class_uri:
        return Response(
            {"error": "Missing 'uri' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        repo.delete_class(class_uri)
    finally:
        driver.close()

    return Response({"deleted": class_uri}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny,))
def add_class_attribute(request):
    data = request.data

    class_uri = data.get("class_uri")
    title = data.get("title")

    if not class_uri or not title:
        return Response(
            {"error": "Missing 'class_uri' or 'title'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        prop = repo.add_class_attribute(class_uri, title)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    return Response(prop, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes((AllowAny,))
def delete_class_attribute(request):
    property_uri = request.GET.get("id")

    if not property_uri:
        return Response(
            {"error": "Missing 'id' query parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        deleted = repo.delete_class_attribute(property_uri)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    if not deleted:
        return Response(
            {"error": "Attribute not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({"deleted": property_uri})

@api_view(['POST'])
@permission_classes((AllowAny,))
def add_class_object_attribute(request):
    data = request.data

    class_uri = data.get("class_uri")
    attr_name = data.get("attr_name")
    range_class_uri = data.get("range_class_uri")

    if not class_uri or not attr_name or not range_class_uri:
        return Response(
            {"error": "Missing 'class_uri', 'attr_name' or 'range_class_uri'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        prop = repo.add_class_object_attribute(
            class_uri, attr_name, range_class_uri
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    return Response(prop, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes((AllowAny,))
def delete_class_object_attribute(request):
    object_property_uri = request.GET.get("id")

    if not object_property_uri:
        return Response(
            {"error": "Missing 'id' query parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        deleted = repo.delete_class_object_attribute(object_property_uri)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    if not deleted:
        return Response(
            {"error": "ObjectProperty not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({"deleted": object_property_uri})

@api_view(['POST'])
@permission_classes((AllowAny,))
def add_class_parent(request):
    data = request.data

    parent_uri = data.get("parent_uri")
    target_uri = data.get("target_uri")

    if not parent_uri or not target_uri:
        return Response(
            {"error": "Missing 'parent_uri' or 'target_uri'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        arc = repo.add_class_parent(parent_uri, target_uri)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    return Response(arc, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_object(request):
    object_uri = request.GET.get("id")

    if not object_uri:
        return Response(
            {"error": "Missing 'id' query parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        obj = repo.get_object(object_uri)
    finally:
        driver.close()

    if not obj:
        return Response(
            {"error": "Object not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(obj)

@api_view(['DELETE'])
@permission_classes((AllowAny,))
def delete_object(request):
    object_uri = request.GET.get("id")

    if not object_uri:
        return Response(
            {"error": "Missing 'id' query parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        deleted = repo.delete_object(object_uri)
    finally:
        driver.close()

    if not deleted:
        return Response(
            {"error": "Object not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response({"deleted": object_uri})

@api_view(['POST'])
@permission_classes((AllowAny,))
def create_object(request):
    data = request.data

    class_uri = data.get("class_uri")
    props = data.get("props")

    if not class_uri or not isinstance(props, dict):
        return Response(
            {"error": "Missing 'class_uri' or invalid 'props'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    obj_params = data.get("obj_params")

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        obj = repo.create_object(class_uri, props, obj_params)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    return Response(obj, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes((AllowAny,))
def update_object(request):
    data = request.data

    object_uri = data.get("object_uri")
    props = data.get("props")

    if not object_uri or not isinstance(props, dict):
        return Response(
            {"error": "Missing 'object_uri' or invalid 'props'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    obj_params = data.get("obj_params")

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        obj = repo.update_object(object_uri, props, obj_params)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        driver.close()

    if not obj:
        return Response(
            {"error": "Object not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(obj)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_class_signature(request):
    class_uri = request.GET.get("uri")

    if not class_uri:
        return Response(
            {"error": "Missing 'uri' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    driver = DriverRepository(
        settings.DB_URI,
        settings.DB_USER,
        settings.DB_PASSWORD
    )

    try:
        repo = OntologyRepository(driver)
        data = repo.collect_signature(class_uri)
    finally:
        driver.close()

    return Response(data, status=status.HTTP_200_OK)



# ----------------------------------


@api_view(['GET'])
@permission_classes((AllowAny,))
def get_text(request):
    text_id = request.GET.get('id')

    if not text_id:
        return Response(
            {"error": "Missing 'id' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        text = text_repo.get(text_id)
        return Response(text, status=status.HTTP_200_OK)
    except Text.DoesNotExist:
        return Response(
            {"error": "Text not found"},
            status=status.HTTP_404_NOT_FOUND
        )


# ---------- CREATE TEXT ----------
@api_view(['POST'])
@permission_classes((AllowAny,))
def create_text(request):
    data = request.data

    required_fields = ['name', 'description', 'content', 'corpus_id']
    for field in required_fields:
        if field not in data:
            return Response(
                {"error": f"Missing field: {field}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    if not isinstance(data.get('name'), str):
        return Response(
            {"error": "Field 'name' must be a string"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        text = text_repo.create(data)
        return Response(text, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ---------- UPDATE TEXT ----------
@api_view(['PUT'])
@permission_classes((AllowAny,))
def update_text(request):
    data = request.data
    text_id = data.get('id')

    if not text_id:
        return Response(
            {"error": "Missing 'id' field"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        text = text_repo.update(text_id, data)
        return Response(text, status=status.HTTP_200_OK)
    except Text.DoesNotExist:
        return Response(
            {"error": "Text not found"},
            status=status.HTTP_404_NOT_FOUND
        )


# ---------- DELETE TEXT ----------
@api_view(['DELETE'])
@permission_classes((AllowAny,))
def delete_text(request):
    text_id = request.GET.get('id')

    if not text_id:
        return Response(
            {"error": "Missing 'id' parameter"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        text_repo.delete(text_id)
        return Response(
            {"deleted": text_id},
            status=status.HTTP_200_OK
        )
    except Text.DoesNotExist:
        return Response(
            {"error": "Text not found"},
            status=status.HTTP_404_NOT_FOUND
        )

# -------------------------
# GET CHUNKS
# -------------------------
@api_view(['POST'])
@permission_classes((AllowAny,))
def get_chunks(request):
    data = request.data
    content = data.get("content")
    chunk_size = data.get("chunk_size")
    overlap = data.get("overlap")

    if not content:
        return Response({"error": "Missing 'content'"}, status=400)

    chunks = EmbeddingUtils.get_chunks(content, chunk_size=chunk_size, overlap=overlap)

    return Response({"chunks": chunks}, status=200)

# -------------------------
# GET EMBEDDINGS
# -------------------------


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_embeddings(request):
    """
    Генерирует эмбеддинги для текста или списка текстов
    """
    data = request.data
    texts = data.get("texts") or ([data.get("content")] if data.get("content") else None)
    text_id = data.get("text_id")

    # Получаем текст из базы, если передан text_id
    if text_id:
        try:
            text_obj = Text.objects.get(id=text_id)
            texts = [text_obj.content]
        except Text.DoesNotExist:
            return Response({"error": "Text not found"}, status=404)

    if not texts:
        return Response({"error": "Missing 'texts' or 'text_id'"}, status=400)

    embeddings = EmbeddingUtils.get_embeddings(texts)
    serialized = [EmbeddingUtils.serialize(vec).hex() for vec in embeddings]  # Для JSON удобнее хранить как hex
    return Response({"embeddings": serialized}, status=200)


# -------------------------
# COSINE SIMILARITY
# -------------------------
    """
    Вычисляет косинусное сходство между двумя эмбеддингами или текстами
    """
@api_view(['POST'])
@permission_classes((AllowAny,))
def cos_compare(request):
    data = request.data
    vec1 = data.get("vec1")
    vec2 = data.get("vec2")
    text1_id = data.get("text1_id")
    text2_id = data.get("text2_id")

    # Получаем эмбеддинги из текстов в базе, если переданы text_id
    if text1_id:
        try:
            text_obj = Text.objects.get(id=text1_id)
            vec1 = text_obj.embedding
        except Text.DoesNotExist:
            return Response({"error": "Text1 not found"}, status=404)

    if text2_id:
        try:
            text_obj = Text.objects.get(id=text2_id)
            vec2 = text_obj.embedding
        except Text.DoesNotExist:
            return Response({"error": "Text2 not found"}, status=404)

    if vec1 is None or vec2 is None:
        return Response({"error": "Missing vectors or text_ids"}, status=400)

    # Если в hex, нужно перевести обратно в bytes
    if isinstance(vec1, str):
        vec1 = bytes.fromhex(vec1)
    if isinstance(vec2, str):
        vec2 = bytes.fromhex(vec2)

    similarity = EmbeddingUtils.cos_compare(vec1, vec2)
    return Response({"cosine_similarity": similarity}, status=200)