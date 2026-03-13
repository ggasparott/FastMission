import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import routes
from app.routes import router
from app.services.item_service import ItemNotFoundException


class DeleteItemEndpointTestCase(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(router, prefix="/api")
        self.app.dependency_overrides[routes.get_db] = lambda: None
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    @patch("app.routes.ItemService")
    def test_delete_item_returns_204_no_content(self, mock_item_service):
        item_id = str(uuid4())
        mock_item_service.return_value.deletar_item.return_value = True

        response = self.client.delete(f"/api/itens/{item_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.text, "")
        mock_item_service.return_value.deletar_item.assert_called_once_with(item_id)

    @patch("app.routes.ItemService")
    def test_delete_item_not_found_returns_404(self, mock_item_service):
        item_id = str(uuid4())
        mock_item_service.return_value.deletar_item.side_effect = ItemNotFoundException("Item não encontrado")

        response = self.client.delete(f"/api/itens/{item_id}")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Item não encontrado", response.text)


if __name__ == "__main__":
    unittest.main()
