from neo4j import GraphDatabase
import json
import uuid
from typing import List, Dict, Any, Optional

TNode = Dict[str, Any]
TArc = Dict[str, Any]

class DriverRepository:
    def __init__(self, uri: str, user: str, password: str):
        """Инициализация драйвера Neo4j"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Закрыть соединение с базой"""
        self.driver.close()

    # -----------------------
    # Вспомогательные функции
    # -----------------------
    @staticmethod
    def generate_random_string(length: int = 12) -> str:
        """Генерация уникальной строки для URI узла"""
        return f"node_{uuid.uuid4().hex[:length]}"

    @staticmethod
    def transform_labels(labels: List[str], separator: str = ":") -> str:
        """Преобразовать список меток в строку Cypher"""
        if not labels:
            return ""

        formatted_labels = [f"`{label}`" for label in labels]
        return separator.join(formatted_labels)

    @staticmethod
    def transform_props(props: Dict[str, Any]) -> str:
        """Преобразовать словарь свойств в Cypher map"""
        if not props:
            return "{}"

        formatted_props = []
        for key, value in props.items():
            json_value = json.dumps(value, ensure_ascii=False)
            formatted_props.append(f"`{key}`:{json_value}")

        return "{" + ", ".join(formatted_props) + "}"

    # -----------------------
    # Сборщики (collect)
    # -----------------------
    @staticmethod
    def collect_node(node) -> TNode:
        """Преобразует объект узла в словарь TNode"""
        return {
            "element_id": getattr(node, "element_id", None),
            "uri": node.get("uri") if hasattr(node, "get") else node.get("uri", ""),
            "title": node.get("title", ""),
            "description": node.get("description", ""),
            "arcs": node.get("arcs", [])
        }

    @staticmethod
    def collect_arc(rel) -> TArc:
        """Преобразует объект дуги в словарь TArc"""
        return {
            "id": getattr(rel, "element_id", None),
            "uri": rel.type if hasattr(rel, "type") else rel.get("uri", ""),
            "node_uri_from": rel.start_node.get("uri") if hasattr(rel, "start_node") else rel.get("node_uri_from"),
            "node_uri_to": rel.end_node.get("uri") if hasattr(rel, "end_node") else rel.get("node_uri_to")
        }

    # -----------------------
    # CRUD узлов
    # -----------------------
    def create_node(self, props: Dict[str, Any], labels: Optional[List[str]] = None) -> TNode:
        labels = labels or []
        if "uri" not in props:
            props["uri"] = self.generate_random_string()
        label_part = f":{self.transform_labels(labels)}" if labels else ""
        props_part = self.transform_props(props)
        query = f"CREATE (n{label_part} {props_part}) RETURN n"
        with self.driver.session() as session:
            rec = session.run(query).single()
            return self.collect_node(rec["n"])

    def get_all_nodes(self) -> List[TNode]:
        query = "MATCH (n) RETURN n"
        with self.driver.session() as session:
            res = session.run(query)
            return [self.collect_node(r["n"]) for r in res]

    def get_all_nodes_and_arcs(self) -> List[TNode]:
        query = "MATCH (n)-[r]->(m) RETURN n, r, m"
        with self.driver.session() as session:
            res = session.run(query)
            nodes_map = {}
            for r in res:
                n = r["n"]
                m = r["m"]
                arc = self.collect_arc(r["r"])
                nodes_map[n.get("uri")] = nodes_map.get(n.get("uri"), self.collect_node(n))
                nodes_map[m.get("uri")] = nodes_map.get(m.get("uri"), self.collect_node(m))
                nodes_map[n.get("uri")]["arcs"].append(arc)
            return list(nodes_map.values())

    def get_nodes_by_labels(self, labels: List[str]) -> List[TNode]:
        label_part = f":{self.transform_labels(labels)}" if labels else ""
        query = f"MATCH (n{label_part}) RETURN n"
        with self.driver.session() as session:
            res = session.run(query)
            return [self.collect_node(r["n"]) for r in res]

    def update_node(self, uri: str, props: Dict[str, Any]) -> Optional[TNode]:
        set_str = ", ".join(f"n.`{k}` = ${k}" for k in props.keys())
        query = f"MATCH (n {{`uri`: $uri}}) SET {set_str} RETURN n"
        params = {"uri": uri, **props}
        with self.driver.session() as session:
            rec = session.run(query, **params).single()
            return self.collect_node(rec["n"]) if rec else None

    def delete_node_by_uri(self, uri: str) -> bool:
        query = "MATCH (n {`uri`: $uri}) DETACH DELETE n RETURN COUNT(n) as cnt"
        with self.driver.session() as session:
            rec = session.run(query, uri=uri).single()
            return rec["cnt"] > 0 if rec else False

    # -----------------------
    # CRUD дуг
    # -----------------------
    def create_arc(self, node1_uri: str, node2_uri: str, arc_type: str = "RELATED") -> Optional[TArc]:
        query = f"""
        MATCH (a {{`uri`: $uri1}}), (b {{`uri`: $uri2}})
        CREATE (a)-[r:`{arc_type}`]->(b)
        RETURN r, a, b
        """
        with self.driver.session() as session:
            rec = session.run(query, uri1=node1_uri, uri2=node2_uri).single()
            return self.collect_arc(rec["r"]) if rec else None

    def delete_arc_by_id(self, arc_id: str) -> bool:
        """Удалить дугу по element_id"""
        query = "MATCH ()-[r]-() WHERE elementId(r) = $id DELETE r RETURN COUNT(r) as cnt"
        with self.driver.session() as session:
            rec = session.run(query, id=arc_id).single()
            return rec["cnt"] > 0 if rec else False

    def get_node_by_uri(self, uri: str) -> Optional[TNode]:
        """
        Получить узел по URI вместе со всеми связями (входящими и исходящими).
        Возвращает None, если узел не найден.
        """
        query = """
        MATCH (n {uri: $uri})
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN n, r, m
        """
        arcs = []
        node_obj = None
        with self.driver.session() as session:
            res = session.run(query, uri=uri)
            for record in res:
                # первый раз сохраняем сам объект Node (нативный)
                if node_obj is None:
                    node_obj = record["n"]
                # r может быть None (если у узла нет связей) или Relationship
                r = record.get("r")
                if r is not None:
                    collected = self.collect_arc(r)
                    if collected:
                        # защитимся от дублей по element_id
                        if not any(a.get("id") == collected.get("id") and a.get("uri") == collected.get("uri") for a in
                                   arcs):
                            arcs.append(collected)

        if node_obj is None:
            return None

        result = self.collect_node(node_obj)
        result["arcs"] = arcs
        return result

    # -----------------------
    # Произвольные запросы
    # -----------------------
    def run_custom_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        params = params or {}
        with self.driver.session() as session:
            res = session.run(query, **params)
            return [{k: (v if not hasattr(v, "items") else dict(v.items())) for k, v in dict(r).items()} for r in res]
