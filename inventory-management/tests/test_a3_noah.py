from app import store


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_products_page_get(client):
    response = client.get("/ui/products")
    assert response.status_code == 200


def test_create_product(client):
    response = client.post(
        "/ui/products",
        data={
            "name": "Test Product",
            "sku": "TEST-001",
            "unit_price": "12.50",
            "quantity_on_hand": "10",
        },
    )

    assert response.status_code == 302
    assert len(store.products) == 1

    product = store.products[1]
    assert product.name == "Test Product"
    assert product.sku == "TEST-001"
    assert product.unit_price == 12.50
    assert product.quantity_on_hand == 10


def test_delete_product(client):
    client.post(
        "/ui/products",
        data={
            "name": "Test Product",
            "sku": "TEST-001",
            "unit_price": "12.50",
            "quantity_on_hand": "10",
        },
    )

    response = client.post("/ui/products/1/delete")

    assert response.status_code == 302
    assert 1 not in store.products


def test_delete_nonexistent_product(client):
    response = client.post("/ui/products/999/delete")

    assert response.status_code == 302
    assert store.products == {}


def test_suppliers_page_get(client):
    response = client.get("/ui/suppliers")
    assert response.status_code == 200


def test_create_supplier(client):
    response = client.post(
        "/ui/suppliers",
        data={
            "name": "Test Supplier",
            "contact_email": "supplier@example.com",
        },
    )

    assert response.status_code == 302
    assert len(store.suppliers) == 1

    supplier = store.suppliers[1]
    assert supplier.name == "Test Supplier"
    assert supplier.contact_email == "supplier@example.com"


def test_delete_supplier(client):
    client.post(
        "/ui/suppliers",
        data={
            "name": "Test Supplier",
            "contact_email": "supplier@example.com",
        },
    )

    response = client.post("/ui/suppliers/1/delete")

    assert response.status_code == 302
    assert 1 not in store.suppliers


def test_delete_nonexistent_supplier(client):
    response = client.post("/ui/suppliers/999/delete")

    assert response.status_code == 302
    assert store.suppliers == {}


def test_transactions_page_get(client):
    response = client.get("/ui/transactions")
    assert response.status_code == 200


def test_stock_in_transaction(client):
    client.post(
        "/ui/products",
        data={
            "name": "Test Product",
            "sku": "TEST-001",
            "unit_price": "12.50",
            "quantity_on_hand": "10",
        },
    )

    response = client.post(
        "/ui/transactions",
        data={
            "product_id": "1",
            "type": "IN",
            "quantity": "5",
        },
    )

    assert response.status_code == 302
    assert store.products[1].quantity_on_hand == 15
    assert len(store.transactions) == 1
    assert store.transactions[1].supplier_id is None


def test_stock_out_transaction(client):
    client.post(
        "/ui/products",
        data={
            "name": "Test Product",
            "sku": "TEST-001",
            "unit_price": "12.50",
            "quantity_on_hand": "10",
        },
    )

    response = client.post(
        "/ui/transactions",
        data={
            "product_id": "1",
            "type": "OUT",
            "quantity": "3",
        },
    )

    assert response.status_code == 302
    assert store.products[1].quantity_on_hand == 7
    assert len(store.transactions) == 1


def test_transaction_with_supplier(client):
    client.post(
        "/ui/products",
        data={
            "name": "Test Product",
            "sku": "TEST-001",
            "unit_price": "12.50",
            "quantity_on_hand": "10",
        },
    )

    client.post(
        "/ui/suppliers",
        data={
            "name": "Test Supplier",
            "contact_email": "supplier@example.com",
        },
    )

    response = client.post(
        "/ui/transactions",
        data={
            "product_id": "1",
            "type": "IN",
            "quantity": "5",
            "supplier_id": "1",
        },
    )

    assert response.status_code == 302
    assert store.transactions[1].supplier_id == 1


def test_transaction_for_nonexistent_product(client):
    response = client.post(
        "/ui/transactions",
        data={
            "product_id": "999",
            "type": "IN",
            "quantity": "5",
        },
    )

    assert response.status_code == 302
    assert store.transactions == {}
    assert store.products == {}


def test_low_stock_notification_failure(client, monkeypatch):
    """Stock update succeeds even when notification delivery fails."""
    product_response = client.post("/products", json={
        "name": "Failure Test Product",
        "sku": "A3-FAIL",
        "quantity_on_hand": 10,
        "reorder_level": 5
    })

    assert product_response.status_code == 201
    product_id = product_response.get_json()["id"]

    # Stub notification delivery to simulate failure.
    monkeypatch.setattr(
        "app.routes.transactions.send_notification",
        lambda recipient, subject, message: False
    )

    response = client.post("/transactions", json={
        "product_id": product_id,
        "type": "OUT",
        "quantity": 6
    })

    assert response.status_code == 201
    assert response.get_json()["notified"] is False

    # Verify that the stock update succeeded despite notification failure.
    stock_response = client.get(f"/products/{product_id}/stock-level")
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 4
