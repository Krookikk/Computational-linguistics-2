from typing import List, Dict, Any, Optional

from db.api.DriverRepository import DriverRepository


class OntologyRepository:
    def __init__(self, repo: DriverRepository):
        self.repo = repo

    # -----------------------
    # Получение онтологии
    # -----------------------
    def get_ontology(self) -> List[Dict[str, Any]]:
        """Получить всю онтологию (узлы + дуги)"""
        return self.repo.get_all_nodes_and_arcs()

    def get_ontology_parent_classes(self) -> List[Dict[str, Any]]:
        """Получить классы онтологии без родителей"""
        query = """
        MATCH (c:Class)
        WHERE NOT (c)-[:SUBCLASS_OF]->(:Class)
        RETURN c
        """
        return self.repo.run_custom_query(query)

    # -----------------------
    # Работа с классами
    # -----------------------
    def get_class(self, class_uri: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_node_by_uri(class_uri)

    def get_class_parents(self, class_uri: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (c:Class {uri: $uri})-[:SUBCLASS_OF]->(p:Class)
        RETURN p
        """
        return self.repo.run_custom_query(query, {"uri": class_uri})

    def get_class_children(self, class_uri: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (c:Class {uri: $uri})<-[:SUBCLASS_OF]-(ch:Class)
        RETURN ch
        """
        return self.repo.run_custom_query(query, {"uri": class_uri})

    def get_class_objects(self, class_uri: str) -> List[Dict[str, Any]]:
        query = """
        MATCH (c:Class {uri: $uri})<-[:INSTANCE_OF]-(o:Object)
        RETURN o
        """
        return self.repo.run_custom_query(query, {"uri": class_uri})

    def update_class(self, class_uri: str, title: str, description: str) -> Optional[Dict[str, Any]]:
        return self.repo.update_node(class_uri, {"title": title, "description": description})

    def create_class(self, title: str, description: str, parent_uri: Optional[str] = None) -> Dict[str, Any]:
        new_class = self.repo.create_node({"title": title, "description": description}, ["Class"])
        if parent_uri:
            self.repo.create_arc(new_class["uri"], parent_uri, "SUBCLASS_OF")
        return new_class

    def delete_class(self, class_uri: str) -> bool:
        query = """
        MATCH (c:Class {uri: $uri})
        OPTIONAL MATCH (c)<-[:SUBCLASS_OF*]-(sub:Class)
        OPTIONAL MATCH (c)<-[:INSTANCE_OF*]-(o:Object)
        OPTIONAL MATCH (c)<-[:DOMAIN|RANGE]-(prop)
        DETACH DELETE c, sub, o, prop
        """
        self.repo.run_custom_query(query, {"uri": class_uri})
        return True

    # -----------------------
    # Атрибуты классов
    # -----------------------
    def add_class_attribute(self, class_uri: str, title: str) -> Dict[str, Any]:
        """Добавить DatatypeProperty"""
        prop = self.repo.create_node({"title": title}, ["DatatypeProperty"])
        self.repo.create_arc(prop["uri"], class_uri, "DOMAIN")
        return prop

    def delete_class_attribute(self, property_uri: str) -> bool:
        return self.repo.delete_node_by_uri(property_uri)

    def add_class_object_attribute(self, class_uri: str, attr_name: str, range_class_uri: str) -> Dict[str, Any]:
        """Добавить ObjectProperty"""
        prop = self.repo.create_node({"title": attr_name}, ["ObjectProperty"])
        self.repo.create_arc(prop["uri"], class_uri, "DOMAIN")
        self.repo.create_arc(prop["uri"], range_class_uri, "RANGE")
        return prop

    def delete_class_object_attribute(self, object_property_uri: str) -> bool:
        return self.repo.delete_node_by_uri(object_property_uri)

    def add_class_parent(self, parent_uri: str, target_uri: str) -> Dict[str, Any]:
        return self.repo.create_arc(target_uri, parent_uri, "SUBCLASS_OF")

    # -----------------------
    # Работа с объектами
    # -----------------------
    def get_object(self, object_uri: str) -> Optional[Dict[str, Any]]:
        return self.repo.get_node_by_uri(object_uri)

    def delete_object(self, object_uri: str) -> bool:
        return self.repo.delete_node_by_uri(object_uri)

    def create_object(self, class_uri: str, props: Dict[str, Any], obj_params: Optional[List[Dict[str, Any]]] = None) -> \
    Dict[str, Any]:
        obj = self.repo.create_node(props, ["Object"])
        self.repo.create_arc(obj["uri"], class_uri, "INSTANCE_OF")

        if obj_params:
            for param in obj_params:
                target = param.get("target_uri")
                arc_type = param.get("type", "RELATED")
                if target:
                    self.repo.create_arc(obj["uri"], target, arc_type)

        return obj

    def update_object(self, object_uri: str, props: Dict[str, Any],
                      obj_params: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        obj = self.repo.update_node(object_uri, props)
        if obj and obj_params:
            for param in obj_params:
                target = param.get("target_uri")
                arc_type = param.get("type", "RELATED")
                if target:
                    self.repo.create_arc(object_uri, target, arc_type)
        return obj

    # -----------------------
    # Signature
    # -----------------------
    def collect_signature(self, class_uri: str) -> Dict[str, Any]:
        query = """
        MATCH (c:Class {uri: $uri})
        OPTIONAL MATCH (c)<-[:DOMAIN]-(dp:DatatypeProperty)
        OPTIONAL MATCH (c)<-[:DOMAIN]-(op:ObjectProperty)-[:RANGE]->(rc:Class)
        OPTIONAL MATCH (c)<-[:RANGE]-(op2:ObjectProperty)-[:DOMAIN]->(rc2:Class)
        RETURN c, 
               collect(dp) AS dps, 
               collect({op: op, rc: rc, direction: 1}) + collect({op: op2, rc: rc2, direction: -1}) AS ops
        """
        res = self.repo.run_custom_query(query, {"uri": class_uri})
        if not res:
            return {}

        d = res[0]

        seen_dp = set()
        params = []
        for dp in d["dps"]:
            if dp:
                key = (dp["title"], dp["uri"])
                if key not in seen_dp:
                    seen_dp.add(key)
                    params.append({"title": dp["title"], "uri": dp["uri"]})

        seen_op = set()
        obj_params = []
        for op in d["ops"]:
            if op and op.get("op"):
                key = (op["op"]["title"], op["op"]["uri"], op["rc"]["uri"] if op["rc"] else None)
                if key not in seen_op:
                    seen_op.add(key)
                    obj_params.append({
                        "title": op["op"]["title"],
                        "uri": op["op"]["uri"],
                        "target_class_uri": op["rc"]["uri"] if op["rc"] else None,
                        "direction": op.get("direction", 0)  # 1 или -1
                    })

        return {
            "params": params,
            "obj_params": obj_params
        }
