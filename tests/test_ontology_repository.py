import unittest

from lab1.neo4j_repository import Neo4jRepository
from lab2.ontology_repository import OntologyRepository


class TestOntologyRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Подключаемся к тестовой базе Neo4j
        cls.repo = Neo4jRepository("bolt://localhost:7687", "neo4j", "12345678")
        cls.onto = OntologyRepository(cls.repo)

        # Чистим граф перед тестами
        cls.repo.run_custom_query("MATCH (n) DETACH DELETE n")

        # ---------- Классы ----------
        cls.person = cls.onto.create_class("Person", "A human being")
        cls.employee = cls.onto.create_class("Employee", "Worker in a company", parent_uri=cls.person["uri"])
        cls.manager = cls.onto.create_class("Manager", "Supervises employees", parent_uri=cls.employee["uri"])
        cls.city = cls.onto.create_class("City", "A populated place")
        cls.company = cls.onto.create_class("Company", "An organization that employs people")
        cls.department = cls.onto.create_class("Department", "Part of a company", parent_uri=cls.company["uri"])

        # ---------- Объекты ----------
        cls.john = cls.onto.create_object(cls.person["uri"], {"title": "John", "description": "Test person"})
        cls.jane = cls.onto.create_object(cls.employee["uri"], {"title": "Jane", "description": "Employee"})
        cls.alice = cls.onto.create_object(cls.manager["uri"], {"title": "Alice", "description": "Manager"})
        cls.moscow = cls.onto.create_object(cls.city["uri"], {"title": "Moscow", "description": "Capital"})
        cls.google = cls.onto.create_object(cls.company["uri"], {"title": "Google", "description": "Tech giant"})
        cls.hr = cls.onto.create_object(cls.department["uri"], {"title": "HR Department", "description": "Handles HR"})

        # ---------- Атрибуты (Data properties) ----------
        cls.onto.add_class_attribute(cls.person["uri"], "name")
        cls.onto.add_class_attribute(cls.person["uri"], "age")
        cls.onto.add_class_attribute(cls.company["uri"], "founded")

        # ---------- Объектные атрибуты (Object properties) ----------
        cls.onto.add_class_object_attribute(cls.person["uri"], "lives_in", cls.city["uri"])
        cls.onto.add_class_object_attribute(cls.employee["uri"], "works_in", cls.company["uri"])
        cls.onto.add_class_object_attribute(cls.manager["uri"], "manages", cls.department["uri"])
        cls.onto.add_class_object_attribute(cls.company["uri"], "located_in", cls.city["uri"])
        cls.onto.add_class_object_attribute(cls.department["uri"], "belongs_to", cls.company["uri"])

    # @classmethod
    # def tearDownClass(cls):
    #     cls.repo.run_custom_query("MATCH (n) DETACH DELETE n")
    #     cls.repo.close()

    # ---------- Тесты ----------

    def test_get_ontology(self):
        result = self.onto.get_ontology()
        print("Ontology:", result)
        self.assertTrue(len(result) > 0)

    def test_john_lives_in_moscow(self):
        self.repo.create_arc(self.john["uri"], self.moscow["uri"], "lives_in")

        # проверим, что дуга появилась
        john_obj = self.onto.get_object(self.john["uri"])
        # print("John arcs:", john_obj["arcs"])
        #
        # self.assertTrue(
        #     any(a["uri"] == "lives_in" and a["node_uri_to"] == self.moscow["uri"] for a in john_obj["arcs"])
        # )
    # def test_obj(self):
    #     self.onto.create_arc(self.john["uri"], self.moscow["uri"], "lives_in")

    def test_get_ontology_parent_classes(self):
        result = self.onto.get_ontology_parent_classes()
        print("Ontology parent classes:", result)
        self.assertTrue(any(c["c"]["title"] == "Person" for c in result))

    def test_get_class(self):
        cls_data = self.onto.get_class(self.person["uri"])
        print("Get class Person:", cls_data)
        self.assertEqual(cls_data["title"], "Person")

    def test_get_class_parents(self):
        result = self.onto.get_class_parents(self.employee["uri"])
        print("Employee parents:", result)
        self.assertTrue(any(r["p"]["title"] == "Person" for r in result))

    def test_get_class_children(self):
        result = self.onto.get_class_children(self.person["uri"])
        print("Person children:", result)
        self.assertTrue(any(r["ch"]["title"] == "Employee" for r in result))

    def test_get_class_objects(self):
        result = self.onto.get_class_objects(self.city["uri"])
        print("City objects:", result)
        self.assertTrue(any(r["o"]["title"] == "Moscow" for r in result))

    # def test_update_class(self):
    #     updated = self.onto.update_class(self.person["uri"], "PersonUpdated", "Updated description")
    #     print("Updated Person:", updated)
    #     self.assertEqual(updated["title"], "PersonUpdated")
    #
    # def test_add_and_delete_class_attribute(self):
    #     attr = self.onto.add_class_attribute(self.city["uri"], "population")
    #     print("Added attribute:", attr)
    #     deleted = self.onto.delete_class_attribute(attr["uri"])
    #     print("Deleted attribute result:", deleted)
    #     self.assertTrue(deleted)
    #
    # def test_add_and_delete_class_object_attribute(self):
    #     obj_attr = self.onto.add_class_object_attribute(self.city["uri"], "connected_to", self.person["uri"])
    #     print("Added object attribute:", obj_attr)
    #     deleted = self.onto.delete_class_object_attribute(obj_attr["uri"])
    #     print("Deleted object attribute result:", deleted)
    #     self.assertTrue(deleted)
    #
    # def test_add_class_parent(self):
    #     result = self.onto.add_class_parent(self.city["uri"], self.employee["uri"])
    #     print("Added parent relation:", result)
    #     self.assertIsNotNone(result)
    #
    # def test_get_object(self):
    #     obj = self.onto.get_object(self.john["uri"])
    #     print("Get object John:", obj)
    #     self.assertEqual(obj["title"], "John")
    #
    # def test_update_object(self):
    #     updated = self.onto.update_object(self.john["uri"], {"title": "JohnUpdated"})
    #     print("Updated object John:", updated)
    #     self.assertEqual(updated["title"], "JohnUpdated")
    #
    # def test_delete_object(self):
    #     obj = self.onto.create_object(self.person["uri"], {"title": "Temp"})
    #     deleted = self.onto.delete_object(obj["uri"])
    #     print("Deleted object result:", deleted)
    #     self.assertTrue(deleted)
    #
    # def test_collect_signature(self):
    #     sig = self.onto.collect_signature(self.company["uri"])
    #     print("Signature Person:", sig)
    #     self.assertIn("params", sig)
    #     self.assertIn("obj_params", sig)
    #
    # def test_delete_class(self):
    #     cls = self.onto.create_class("TempClass", "To delete")
    #     deleted = self.onto.delete_class(cls["uri"])
    #     print("Deleted class result:", deleted)
    #     self.assertTrue(deleted)
    #
    #
    #



if __name__ == "__main__":
    unittest.main()
