def test_list_products_initially_empty(client):
    response = client.get("/products")

    assert response.status_code == 200
    assert response.get_json() == []


def test_create_product(client):
    response = client.post(
        "/products",
        json={
            "name": "Keyboard",
            "sku": "KEY-001",
            "unit_price": 49.99,
            "quantity_on_hand": 10,
            "reorder_level": 2,
        },
    )

    assert response.status_code == 201
    product = response.get_json()
    assert product["name"] == "Keyboard"
    assert product["sku"] == "KEY-001"
    assert product["unit_price"] == 49.99
    assert product["quantity_on_hand"] == 10
    assert product["reorder_level"] == 2


def test_retrieve_existing_product(client):
    created = client.post(
        "/products",
        json={
            "name": "Mouse",
            "sku": "MOU-001",
            "unit_price": 19.99,
            "quantity_on_hand": 5,
            "reorder_level": 1,
        },
    )
    product_id = created.get_json()["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.get_json()["name"] == "Mouse"


def test_retrieve_nonexistent_product_returns_404(client):
    response = client.get("/products/9999")

    assert response.status_code == 404


def test_update_product(client):
    created = client.post(
        "/products",
        json={
            "name": "Monitor",
            "sku": "MON-001",
            "unit_price": 199.99,
            "quantity_on_hand": 4,
            "reorder_level": 1,
        },
    )
    product_id = created.get_json()["id"]

    response = client.put(
        f"/products/{product_id}",
        json={"quantity_on_hand": 8},
    )

    assert response.status_code == 200
    assert response.get_json()["quantity_on_hand"] == 8
    assert response.get_json()["name"] == "Monitor"


def test_delete_product(client):
    created = client.post(
        "/products",
        json={
            "name": "Webcam",
            "sku": "WEB-001",
            "unit_price": 39.99,
            "quantity_on_hand": 3,
            "reorder_level": 1,
        },
    )
    product_id = created.get_json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 204
    assert client.get(f"/products/{product_id}").status_code == 404