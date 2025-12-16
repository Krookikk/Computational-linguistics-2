from django.urls import path

from db.views import (
    # ---- Test ----
    getTest,
    postTest,
    deleteTest,

    # ---- Corpus ----
    create_corpus,
    get_corpus,
    update_corpus,
    delete_corpus,

    # ---- Ontology (general) ----
    get_ontology,
    get_ontology_parent_classes,

    # ---- Ontology: classes ----
    get_class,
    get_class_parents,
    get_class_children,
    get_class_objects,
    create_class,
    update_class,
    delete_class,
    add_class_parent,
    get_class_signature,

    # ---- Ontology: class attributes ----
    add_class_attribute,
    delete_class_attribute,
    add_class_object_attribute,
    delete_class_object_attribute,

    # ---- Ontology: objects ----
    get_object,
    create_object,
    update_object,
    delete_object,

    # ---- Text ----
    create_text,
    get_text,
    update_text,
    delete_text,

    get_chunks,
    get_embeddings,
    cos_compare,
)

urlpatterns = [
    # =======================
    # Test
    # =======================
    path('getTest', getTest, name='getTest'),
    path('postTest', postTest, name='postTest'),
    path('deleteTest', deleteTest, name='deleteTest'),

    # =======================
    # Corpus
    # =======================
    path('corpus/create', create_corpus, name='createCorpus'),
    path('corpus/get', get_corpus, name='getCorpus'),
    path('corpus/update', update_corpus, name='updateCorpus'),
    path('corpus/delete', delete_corpus, name='deleteCorpus'),

    # =======================
    # Ontology (general)
    # =======================
    path('ontology/get', get_ontology, name='getOntology'),
    path('ontology/parent-classes', get_ontology_parent_classes, name='getOntologyParentClasses'),

    # =======================
    # Ontology: classes
    # =======================
    path('ontology/class/get', get_class, name='getClass'),
    path('ontology/class/parents', get_class_parents, name='getClassParents'),
    path('ontology/class/children', get_class_children, name='getClassChildren'),
    path('ontology/class/objects', get_class_objects, name='getClassObjects'),

    path('ontology/class/create', create_class, name='createClass'),
    path('ontology/class/update', update_class, name='updateClass'),
    path('ontology/class/delete', delete_class, name='deleteClass'),
    path('ontology/class/add-parent', add_class_parent, name='addClassParent'),

    path('ontology/class/signature', get_class_signature, name='getClassSignature'),

    # =======================
    # Ontology: class attributes
    # =======================
    path(
        'ontology/class/attribute/add',
        add_class_attribute,
        name='addClassAttribute'
    ),
    path(
        'ontology/class/attribute/delete',
        delete_class_attribute,
        name='deleteClassAttribute'
    ),
    path(
        'ontology/class/object-attribute/add',
        add_class_object_attribute,
        name='addClassObjectAttribute'
    ),
    path(
        'ontology/class/object-attribute/delete',
        delete_class_object_attribute,
        name='deleteClassObjectAttribute'
    ),

    # =======================
    # Ontology: objects
    # =======================
    path('ontology/object/get', get_object, name='getObject'),
    path('ontology/object/create', create_object, name='createObject'),
    path('ontology/object/update', update_object, name='updateObject'),
    path('ontology/object/delete', delete_object, name='deleteObject'),

    # =======================
    # Text
    # =======================
    path('text/create', create_text, name='createText'),
    path('text/get', get_text, name='getText'),
    path('text/update', update_text, name='updateText'),
    path('text/delete', delete_text, name='deleteText'),

    # =======================
    # Embeddings / Chunks
    # =======================
    path('text/get-chunks', get_chunks, name='getChunks'),
    path('text/get-embeddings', get_embeddings, name='getEmbeddings'),
    path('text/cos-compare', cos_compare, name='cosCompare'),

]
