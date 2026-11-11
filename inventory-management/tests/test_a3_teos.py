
from unittest.mock import patch


def test_low_stock_notification_stub(client, monkeypatch):
    product_response = client.post("/products", json={
        "name": "Test Product",
        "sku": "A3-STUB",
        "quantity_on_hand": 10,
        "reorder_level": 5
    })

    assert product_response.status_code == 201
    product_id = product_response.get_json()["id"]

    monkeypatch.setattr(
        "app.routes.transactions.send_notification",
        lambda recipient, subject, message: True
    )

    response = client.post("/transactions", json={
        "product_id": product_id,
        "type": "OUT",
        "quantity": 6
    })

    assert response.status_code == 201
    assert response.get_json()["notified"] is True

    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 4


def test_low_stock_notification_mock(client):
    product_response = client.post("/products", json={
        "name": "Mock Product",
        "sku": "A3-MOCK",
        "quantity_on_hand": 10,
        "reorder_level": 5
    })

    assert product_response.status_code == 201
    product_id = product_response.get_json()["id"]

    with patch(
        "app.routes.transactions.send_notification",
        return_value=True
    ) as mock_send:

        response = client.post("/transactions", json={
            "product_id": product_id,
            "type": "OUT",
            "quantity": 6
        })

        assert response.status_code == 201
        assert response.get_json()["notified"] is True

        mock_send.assert_called_once_with(
            "inventory-staff",
            "Low Stock Alert",
            f"Product {product_id} (Mock Product) is low on stock."
        )

    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 4


def test_home_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_products_page_displays_product(client):
    create_response = client.post("/products", json={
        "name": "Test Keyboard",
        "sku": "KEY-001",
        "unit_price": 25.0,
        "quantity_on_hand": 10
    })

    assert create_response.status_code == 201

    response = client.get("/ui/products")

    assert response.status_code == 200
    assert b"Test Keyboard" in response.data


def test_products_page_creates_product(client):
    response = client.post("/ui/products", data={
        "name": "Test Mouse",
        "sku": "MOU-001",
        "unit_price": "15.0",
        "quantity_on_hand": "20"
    })

    assert response.status_code == 302
    assert "/ui/products" in response.headers["Location"]

    products_response = client.get("/products")
    assert products_response.status_code == 200

    products = products_response.get_json()
    assert any(
        p["name"] == "Test Mouse"
        and p["sku"] == "MOU-001"
        and p["quantity_on_hand"] == 20
        for p in products
    )


def test_delete_product_page(client):
    create_response = client.post("/products", json={
        "name": "Delete Me",
        "sku": "DEL-001",
        "quantity_on_hand": 5
    })

    assert create_response.status_code == 201
    product_id = create_response.get_json()["id"]

    response = client.post(f"/ui/products/{product_id}/delete")

    assert response.status_code == 302
    assert "/ui/products" in response.headers["Location"]

    get_response = client.get(f"/products/{product_id}")

    assert get_response.status_code == 404
    assert get_response.get_json()["error"] == "Product not found"
