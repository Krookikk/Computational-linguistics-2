import unittest
from neo4j_repository import Neo4jRepository


class TestNeo4jRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Открываем соединение с Neo4j перед всеми тестами"""
        cls.repo = Neo4jRepository("bolt://localhost:7687", "neo4j", "12345678")

    @classmethod
    def tearDownClass(cls):
        """Закрываем соединение после всех тестов"""
        cls.repo.close()

    def setUp(self):
        """Перед каждым тестом — очищаем базу"""
        self.repo.run_custom_query("MATCH (n) DETACH DELETE n")

    def test_create_and_get_node(self):
        node = self.repo.create_node({"title": "Alice", "description": "Test user"})
        self.assertIsNotNone(node)
        self.assertIn("uri", node)

        fetched = self.repo.get_node_by_uri(node["uri"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["title"], "Alice")

    def test_update_node(self):
        node = self.repo.create_node({"title": "Bob"})
        updated = self.repo.update_node(node["uri"], {"description": "New desc"})
        self.assertEqual(updated["description"], "New desc")

    def test_delete_node(self):
        node = self.repo.create_node({"title": "Charlie"})
        deleted = self.repo.delete_node_by_uri(node["uri"])
        self.assertTrue(deleted)

        fetched = self.repo.get_node_by_uri(node["uri"])
        self.assertIsNone(fetched)

    def test_create_arc_and_fetch(self):
        n1 = self.repo.create_node({"title": "Node1"})
        n2 = self.repo.create_node({"title": "Node2"})
        arc = self.repo.create_arc(n1["uri"], n2["uri"], "CONNECTED")

        self.assertIsNotNone(arc)
        self.assertEqual(arc["node_uri_from"], n1["uri"])
        self.assertEqual(arc["node_uri_to"], n2["uri"])

        nodes = self.repo.get_all_nodes_and_arcs()
        node1 = [n for n in nodes if n["uri"] == n1["uri"]][0]
        self.assertEqual(len(node1["arcs"]), 1)
        self.assertEqual(node1["arcs"][0]["uri"], "CONNECTED")

    def test_delete_arc(self):
        n1 = self.repo.create_node({"title": "N1"})
        n2 = self.repo.create_node({"title": "N2"})
        arc = self.repo.create_arc(n1["uri"], n2["uri"], "REL")

        deleted = self.repo.delete_arc_by_id(arc["id"])
        self.assertTrue(deleted)

    def test_get_nodes_by_labels(self):
        self.repo.create_node({"title": "Test1"}, labels=["Person"])
        self.repo.create_node({"title": "Test2"}, labels=["Person"])
        people = self.repo.get_nodes_by_labels(["Person"])
        self.assertEqual(len(people), 2)

    def test_run_custom_query(self):
        self.repo.create_node({"title": "Custom"})
        res = self.repo.run_custom_query("MATCH (n {title:$title}) RETURN n", {"title": "Custom"})
        self.assertEqual(len(res), 1)


if __name__ == "__main__":
    unittest.main()
