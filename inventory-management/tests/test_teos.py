
# CISC 227 - Assignment 2
# Teos Vaccaro - Supplier and Purchase Order Tests

def create_supplier(client):
    response = client.post("/suppliers", json={
        "name": "ABC Supplies",
        "contact_email": "abc@example.com"
    })
    assert response.status_code == 201
    return response.get_json()["id"]


def create_product(client):
    response = client.post("/products", json={
        "name": "Warehouse Box",
        "sku": "BOX-001",
        "unit_price": 10.0,
        "quantity_on_hand": 5,
        "reorder_level": 2
    })
    assert response.status_code == 201
    return response.get_json()["id"]


# 1. List suppliers
def test_list_suppliers(client):
    supplier_id = create_supplier(client)
    response = client.get("/suppliers")

    assert response.status_code == 200
    suppliers = response.get_json()
    assert len(suppliers) == 1
    assert suppliers[0]["id"] == supplier_id
    assert suppliers[0]["name"] == "ABC Supplies"


# 2. Create supplier
def test_create_supplier(client):
    response = client.post("/suppliers", json={
        "name": "New Supplier",
        "contact_email": "new@example.com"
    })

    assert response.status_code == 201
    supplier = response.get_json()
    assert supplier["name"] == "New Supplier"
    assert supplier["contact_email"] == "new@example.com"

    saved = client.get(f'/suppliers/{supplier["id"]}')
    assert saved.get_json()["name"] == "New Supplier"


# 3. Retrieve supplier
def test_get_supplier(client):
    supplier_id = create_supplier(client)
    response = client.get(f"/suppliers/{supplier_id}")

    assert response.status_code == 200
    assert response.get_json()["id"] == supplier_id

    missing = client.get("/suppliers/9999")
    assert missing.status_code == 404


# 4. Update supplier
def test_update_supplier(client):
    supplier_id = create_supplier(client)

    response = client.put(f"/suppliers/{supplier_id}", json={
        "name": "Updated Supplier"
    })

    assert response.status_code == 200
    assert response.get_json()["name"] == "Updated Supplier"

    saved = client.get(f"/suppliers/{supplier_id}")
    assert saved.get_json()["name"] == "Updated Supplier"
    assert saved.get_json()["contact_email"] == "abc@example.com"


# 5. Delete supplier
def test_delete_supplier(client):
    supplier_id = create_supplier(client)

    response = client.delete(f"/suppliers/{supplier_id}")
    assert response.status_code == 204

    missing = client.get(f"/suppliers/{supplier_id}")
    assert missing.status_code == 404


# 6. List products associated with supplier
def test_supplier_products(client):
    supplier_id = create_supplier(client)
    product_id = create_product(client)

    transaction = client.post("/transactions", json={
        "product_id": product_id,
        "supplier_id": supplier_id,
        "type": "IN",
        "quantity": 10
    })
    assert transaction.status_code == 201

    response = client.get(f"/suppliers/{supplier_id}/products")
    assert response.status_code == 200

    products = response.get_json()
    assert len(products) == 1
    assert products[0]["id"] == product_id


def create_purchase_order(client):
    supplier_id = create_supplier(client)
    product_id = create_product(client)

    response = client.post("/purchase-orders", json={
        "supplier_id": supplier_id,
        "product_id": product_id,
        "quantity_ordered": 20
    })
    assert response.status_code == 201
    return response.get_json(), product_id


# 7. List purchase orders
def test_list_purchase_orders(client):
    order, _ = create_purchase_order(client)

    response = client.get("/purchase-orders")
    assert response.status_code == 200

    orders = response.get_json()
    assert len(orders) == 1
    assert orders[0]["id"] == order["id"]


# 8. Create purchase order
def test_create_purchase_order(client):
    order, _ = create_purchase_order(client)

    assert order["quantity_ordered"] == 20
    assert order["status"] == "pending"

    response = client.get(f'/purchase-orders/{order["id"]}')
    assert response.status_code == 200
    assert response.get_json()["quantity_ordered"] == 20


# 9. Retrieve purchase order
def test_get_purchase_order(client):
    order, _ = create_purchase_order(client)

    response = client.get(f'/purchase-orders/{order["id"]}')
    assert response.status_code == 200
    assert response.get_json()["id"] == order["id"]

    missing = client.get("/purchase-orders/9999")
    assert missing.status_code == 404


# 10. Receive purchase order
def test_receive_purchase_order(client):
    order, _ = create_purchase_order(client)
    order_id = order["id"]

    response = client.put(f"/purchase-orders/{order_id}/receive")

    assert response.status_code == 200
    assert response.get_json()["status"] == "received"
    assert response.get_json()["received_date"] is not None

    transactions = client.get("/transactions").get_json()
    assert any(
        t["type"] == "IN" and t["quantity"] == 20
        for t in transactions
    )


# 11. Cannot receive the same order twice
def test_cannot_receive_order_twice(client):
    order, _ = create_purchase_order(client)
    order_id = order["id"]

    first = client.put(f"/purchase-orders/{order_id}/receive")
    assert first.status_code == 200

    second = client.put(f"/purchase-orders/{order_id}/receive")
    assert second.status_code == 400

    transactions = client.get("/transactions").get_json()
    assert len(transactions) == 1


# 12. Receiving order should update inventory
# This test exposes the documented existing bug.
def test_receiving_order_updates_stock(client):
    order, product_id = create_purchase_order(client)

    before = client.get(
        f"/products/{product_id}/stock-level"
    ).get_json()["quantity_on_hand"]

    response = client.put(
        f'/purchase-orders/{order["id"]}/receive'
    )
    assert response.status_code == 200

    after = client.get(
        f"/products/{product_id}/stock-level"
    ).get_json()["quantity_on_hand"]

    assert after == before + 20


# Helper function for purchase order tests
def create_purchase_order(client):
    supplier_id = create_supplier(client)
    product_id = create_product(client)

    response = client.post("/purchase-orders", json={
        "supplier_id": supplier_id,
        "product_id": product_id,
        "quantity_ordered": 20
    })

    assert response.status_code == 201
    return response.get_json(), product_id


# Test listing purchase orders
def test_list_purchase_orders(client):
    order, _ = create_purchase_order(client)

    response = client.get("/purchase-orders")
    assert response.status_code == 200
    assert len(response.get_json()) == 1
    assert response.get_json()[0]["id"] == order["id"]


# Test creating a purchase order
def test_create_purchase_order(client):
    order, _ = create_purchase_order(client)

    assert order["quantity_ordered"] == 20
    assert order["status"] == "pending"


# Test retrieving a purchase order
def test_get_purchase_order(client):
    order, _ = create_purchase_order(client)

    response = client.get(f'/purchase-orders/{order["id"]}')
    assert response.status_code == 200
    assert response.get_json()["id"] == order["id"]


# Test receiving a purchase order
def test_receive_purchase_order(client):
    order, _ = create_purchase_order(client)

    response = client.put(
        f'/purchase-orders/{order["id"]}/receive'
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "received"

    saved = client.get(
        f'/purchase-orders/{order["id"]}'
    ).get_json()

    assert saved["status"] == "received"


# Test receiving the same purchase order twice
def test_cannot_receive_order_twice(client):
    order, _ = create_purchase_order(client)
    order_id = order["id"]

    first = client.put(f"/purchase-orders/{order_id}/receive")
    assert first.status_code == 200

    second = client.put(f"/purchase-orders/{order_id}/receive")
    assert second.status_code == 400

def test_purchase_order_invalid_supplier(client):
    product_id = create_product(client)

    response = client.post("/purchase-orders", json={
        "supplier_id": 9999,
        "product_id": product_id,
        "quantity_ordered": 10
    })

    assert response.status_code == 404

