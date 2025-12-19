import os
import json
import numpy as np
import requests
from difflib import SequenceMatcher

from db.api.EmbeddingUtils import EmbeddingUtils


# ========== НАСТРОЙКИ ==========
GRAPH_PATH = "graph.json"

YANDEX_API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
MODEL_URI = "gpt://""b1g5ripc3uv89hkrjo85""/yandexgpt-lite"

YANDEX_API_KEY = "" #ключ

TOP_N = 8
TOP_M = 5

# сколько связей (соседей) добавлять в текст узла
MAX_NEIGHBORS_OUT = 12
MAX_NEIGHBORS_IN = 6


# ========== УТИЛИТЫ ==========
def strip_lang(label: str) -> str:
    # "признается в любви@ru" -> "признается в любви"
    return label.split("@", 1)[0].strip()


def get_node_label(node: dict) -> str:
    params = node.get("data", {}).get("params_values", {}) or {}
    labels = params.get("http://www.w3.org/2000/01/rdf-schema#label") or []
    if isinstance(labels, list) and labels:
        return strip_lang(labels[0])
    if isinstance(labels, str) and labels:
        return strip_lang(labels)
    # fallback
    uri = params.get("uri") or node.get("id") or "unknown"
    return str(uri)


def get_node_comment(node: dict) -> str:
    params = node.get("data", {}).get("params_values", {}) or {}
    comment = params.get("http://www.w3.org/2000/01/rdf-schema#comment")
    if isinstance(comment, str) and comment.strip():
        return comment.strip()
    return ""


def cosine_topk(query_vec: np.ndarray, X: np.ndarray, k: int) -> np.ndarray:
    q = query_vec.astype(np.float32)
    X = X.astype(np.float32)

    q_norm = np.linalg.norm(q) + 1e-12
    X_norm = np.linalg.norm(X, axis=1) + 1e-12

    sims = (X @ q) / (X_norm * q_norm)
    top_idx = np.argsort(sims)[::-1][:k]
    return top_idx


# ========== 1) ЗАГРУЗКА ==========
def load_graph(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ========== 2) ИНДЕКСЫ ГРАФА (nodes + arcs) ==========
def build_graph_index(graph_json: dict):
    nodes = graph_json.get("nodes", [])
    arcs = graph_json.get("arcs", [])

    node_by_uri = {}
    all_labels = []

    for n in nodes:
        uri = (n.get("data", {}).get("params_values", {}) or {}).get("uri") or n.get("id")
        if uri:
            node_by_uri[str(uri)] = n
        all_labels.append(get_node_label(n))

    out_arcs = {}
    in_arcs = {}

    for a in arcs:
        s = str(a.get("source"))
        t = str(a.get("target"))
        out_arcs.setdefault(s, []).append(a)
        in_arcs.setdefault(t, []).append(a)

    return node_by_uri, out_arcs, in_arcs, all_labels


def arc_relation_label(arc: dict, node_by_uri: dict) -> str:
    data = arc.get("data", {}) or {}
    rel_uri = data.get("uri")
    if rel_uri and str(rel_uri) in node_by_uri:
        return get_node_label(node_by_uri[str(rel_uri)])

    # fallback: если не нашли node свойства
    labels = data.get("labels") or []
    if isinstance(labels, list) and labels:
        return strip_lang(str(labels[0]))
    return "связь"


# ========== 3) ТРАНСФОРМАЦИЯ УЗЛА В ТЕКСТ (с добавлением связей) ==========
def node_to_text(node: dict, node_by_uri: dict, out_arcs: dict, in_arcs: dict) -> str:
    params = node.get("data", {}).get("params_values", {}) or {}
    uri = str(params.get("uri") or node.get("id") or "")

    lines = []

    name = get_node_label(node)
    if name:
        lines.append(f"Название: {name}")

    comment = get_node_comment(node)
    if comment:
        lines.append(f"Описание: {comment}")

    # datatype params (кроме label/comment/uri)
    for k, v in params.items():
        if k.endswith("#label") or k.endswith("#comment") or k == "uri":
            continue

        if isinstance(v, list):
            vv = ", ".join(map(str, v[:10]))
        elif isinstance(v, dict):
            vv = json.dumps(v, ensure_ascii=False)[:500]
        else:
            vv = str(v)

        lines.append(f"{k}: {vv}")

    outs = out_arcs.get(uri, [])[:MAX_NEIGHBORS_OUT]
    if outs:
        lines.append("Связи (исходящие):")
        for a in outs:
            rel = arc_relation_label(a, node_by_uri)
            tgt_uri = str(a.get("target"))
            tgt_node = node_by_uri.get(tgt_uri)
            tgt_name = get_node_label(tgt_node) if tgt_node else tgt_uri
            lines.append(f"- {rel}: {tgt_name}")

    # добавляем входящие связи: neighbor --rel--> node
    ins = in_arcs.get(uri, [])[:MAX_NEIGHBORS_IN]
    if ins:
        lines.append("Связи (входящие):")
        for a in ins:
            rel = arc_relation_label(a, node_by_uri)
            src_uri = str(a.get("source"))
            src_node = node_by_uri.get(src_uri)
            src_name = get_node_label(src_node) if src_node else src_uri
            lines.append(f"- {src_name} -> {rel}")

    return "\n".join(lines).strip()


# ========== 4) КОРПУС ==========
def build_corpus(graph_json: dict):
    node_by_uri, out_arcs, in_arcs, all_labels = build_graph_index(graph_json)

    texts = []
    nodes = []

    for node in graph_json.get("nodes", []):
        text = node_to_text(node, node_by_uri, out_arcs, in_arcs)
        if text:
            texts.append(text)
            nodes.append(node)

    return texts, nodes, all_labels


# ========== 5) ЭМБЕДДИНГИ ==========
def embed_texts(texts):
    return np.vstack([np.asarray(EmbeddingUtils.get_embedding(t), dtype=np.float32) for t in texts])


# ========== 6) РАСШИРЕНИЕ ЗАПРОСА (чтобы лучше доставать нужные узлы) ==========
def expand_question(question: str, all_labels: list[str], top_add: int = 6) -> str:
    q = question.lower().strip()

    q = q.replace("вощвращ", "возвращ")

    # добавляем несколько наиболее похожих label'ов
    scored = []
    for lb in all_labels:
        s = strip_lang(lb).lower()
        if not s:
            continue
        ratio = SequenceMatcher(a=q, b=s).ratio()
        scored.append((ratio, lb))

    scored.sort(reverse=True, key=lambda x: x[0])
    extra = [strip_lang(lb) for _, lb in scored[:top_add]]

    return question + "\nПохожие термины из онтологии: " + "; ".join(extra)


# ========== 7) YANDEX GPT ==========
def yandex_gpt(prompt: str) -> str:
    if not YANDEX_API_KEY:
        raise RuntimeError("Не найден YANDEX_API_KEY. Установи переменную окружения YANDEX_API_KEY.")

    payload = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.2,
            "maxTokens": 2000
        },
        "messages": [
            {"role": "user", "text": prompt}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }

    r = requests.post(YANDEX_API_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()["result"]["alternatives"][0]["message"]["text"]


# ========== 8) RAG PIPELINE ==========
def rag_answer(question: str):
    graph = load_graph(GRAPH_PATH)
    texts, nodes, all_labels = build_corpus(graph)

    corpus_embeddings = embed_texts(texts)

    # ---- ФАЗА 1 ----
    expanded_q = expand_question(question, all_labels, top_add=6)
    q_emb = np.asarray(EmbeddingUtils.get_embedding(expanded_q), dtype=np.float32)

    top_n_idx = cosine_topk(q_emb, corpus_embeddings, TOP_N)
    context_n = "\n\n".join(texts[int(i)] for i in top_n_idx)

    prompt_1 = (
        "Ответь на вопрос, используя ТОЛЬКО факты из текста.\n"
        "Если в тексте нет прямого факта — так и скажи.\n\n"
        f"Вопрос:\n{question}\n\n"
        f"Текст:\n{context_n}\n"
    )
    answer_1 = yandex_gpt(prompt_1)

    # ---- ФАЗА 2 ----
    a_emb = np.asarray(EmbeddingUtils.get_embedding(answer_1), dtype=np.float32)
    top_m_idx = cosine_topk(a_emb, corpus_embeddings, TOP_M)

    all_idx = list(dict.fromkeys([int(i) for i in top_n_idx] + [int(i) for i in top_m_idx]))
    context_nm = "\n\n".join(texts[i] for i in all_idx)

    prompt_2 = (
        "Дай финальный ответ на вопрос, используя ТОЛЬКО факты из текста.\n"
        "Старайся отвечать прямо: имя/объект + нужная связь.\n\n"
        f"Вопрос:\n{question}\n\n"
        f"Текст:\n{context_nm}\n"
    )
    final_answer = yandex_gpt(prompt_2)
    return final_answer


if __name__ == "__main__":
    q = "к какой эпохе относится Война и мир"
    print("ВОПРОС:", q)
    print("ОТВЕТ:", rag_answer(q))
