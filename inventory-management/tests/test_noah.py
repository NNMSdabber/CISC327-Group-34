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

def test_get_stock_level(client):
    created = client.post(
        "/products",
        json={
            "name": "USB Cable",
            "sku": "USB-001",
            "unit_price": 9.99,
            "quantity_on_hand": 12,
            "reorder_level": 3,
        },
    )
    product_id = created.get_json()["id"]

    response = client.get(f"/products/{product_id}/stock-level")

    assert response.status_code == 200
    assert response.get_json()["product_id"] == product_id
    assert response.get_json()["quantity_on_hand"] == 12


def test_stock_level_for_nonexistent_product_returns_404(client):
    response = client.get("/products/9999/stock-level")

    assert response.status_code == 404


def test_low_stock_products(client):
    # Below the reorder level
    client.post(
        "/products",
        json={
            "name": "Low Stock Item",
            "sku": "LOW-001",
            "quantity_on_hand": 2,
            "reorder_level": 5,
        },
    )

    # Exactly at the reorder level
    client.post(
        "/products",
        json={
            "name": "Reorder Item",
            "sku": "LOW-002",
            "quantity_on_hand": 5,
            "reorder_level": 5,
        },
    )

    # Above the reorder level
    client.post(
        "/products",
        json={
            "name": "In Stock Item",
            "sku": "LOW-003",
            "quantity_on_hand": 10,
            "reorder_level": 5,
        },
    )

    response = client.get("/products/low-stock")

    assert response.status_code == 200
    products = response.get_json()
    product_names = [product["name"] for product in products]

    assert "Low Stock Item" in product_names
    assert "Reorder Item" in product_names
    assert "In Stock Item" not in product_names

def test_incoming_transaction_increases_stock(client):
    created = client.post(
        "/products",
        json={
            "name": "Incoming Item",
            "sku": "IN-001",
            "quantity_on_hand": 10,
            "reorder_level": 2,
        },
    )
    product_id = created.get_json()["id"]

    response = client.post(
        "/transactions",
        json={
            "product_id": product_id,
            "type": "IN",
            "quantity": 5,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["type"] == "IN"
    assert response.get_json()["quantity"] == 5

    stock = client.get(f"/products/{product_id}/stock-level")
    assert stock.get_json()["quantity_on_hand"] == 15


def test_outgoing_transaction_decreases_stock(client):
    created = client.post(
        "/products",
        json={
            "name": "Outgoing Item",
            "sku": "OUT-001",
            "quantity_on_hand": 10,
            "reorder_level": 2,
        },
    )
    product_id = created.get_json()["id"]

    response = client.post(
        "/transactions",
        json={
            "product_id": product_id,
            "type": "OUT",
            "quantity": 3,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["type"] == "OUT"

    stock = client.get(f"/products/{product_id}/stock-level")
    assert stock.get_json()["quantity_on_hand"] == 7


def test_list_transactions(client):
    created = client.post(
        "/products",
        json={
            "name": "History Item",
            "sku": "HIST-001",
            "quantity_on_hand": 0,
            "reorder_level": 1,
        },
    )
    product_id = created.get_json()["id"]

    client.post(
        "/transactions",
        json={
            "product_id": product_id,
            "type": "IN",
            "quantity": 8,
        },
    )

    response = client.get("/transactions")

    assert response.status_code == 200
    transactions = response.get_json()
    assert len(transactions) == 1
    assert transactions[0]["product_id"] == product_id
    assert transactions[0]["quantity"] == 8
    assert "transaction_date" in transactions[0]


def test_filter_transactions_by_product(client):
    first = client.post(
        "/products",
        json={
            "name": "First Product",
            "sku": "FILTER-001",
            "quantity_on_hand": 0,
            "reorder_level": 1,
        },
    ).get_json()

    second = client.post(
        "/products",
        json={
            "name": "Second Product",
            "sku": "FILTER-002",
            "quantity_on_hand": 0,
            "reorder_level": 1,
        },
    ).get_json()

    client.post(
        "/transactions",
        json={
            "product_id": first["id"],
            "supplier_id": 101,
            "type": "IN",
            "quantity": 4,
        },
    )
    client.post(
        "/transactions",
        json={
            "product_id": second["id"],
            "supplier_id": 202,
            "type": "IN",
            "quantity": 6,
        },
    )

    response = client.get(f"/transactions?product_id={first['id']}")

    assert response.status_code == 200
    transactions = response.get_json()
    assert len(transactions) == 1
    assert transactions[0]["product_id"] == first["id"]


def test_filter_transactions_by_supplier(client):
    created = client.post(
        "/products",
        json={
            "name": "Supplier Item",
            "sku": "SUP-001",
            "quantity_on_hand": 0,
            "reorder_level": 1,
        },
    )
    product_id = created.get_json()["id"]

    client.post(
        "/transactions",
        json={
            "product_id": product_id,
            "supplier_id": 101,
            "type": "IN",
            "quantity": 4,
        },
    )
    client.post(
        "/transactions",
        json={
            "product_id": product_id,
            "supplier_id": 202,
            "type": "IN",
            "quantity": 6,
        },
    )

    response = client.get("/transactions?supplier_id=101")

    assert response.status_code == 200
    transactions = response.get_json()
    assert len(transactions) == 1
    assert transactions[0]["supplier_id"] == 101



def test_receiving_purchase_order_increases_stock(client):
    supplier_response = client.post(
        "/suppliers",
        json={
            "name": "Test Supplier",
            "contact_email": "supplier@example.com",
        },
    )
    supplier_id = supplier_response.get_json()["id"]

    product_response = client.post(
        "/products",
        json={
            "name": "Delivered Item",
            "sku": "DEL-001",
            "unit_price": 10.0,
            "quantity_on_hand": 5,
            "reorder_level": 2,
        },
    )
    product_id = product_response.get_json()["id"]

    order_response = client.post(
        "/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "product_id": product_id,
            "quantity_ordered": 10,
        },
    )
    assert order_response.status_code == 201
    order_id = order_response.get_json()["id"]

    receive_response = client.put(
        f"/purchase-orders/{order_id}/receive"
    )

    assert receive_response.status_code == 200
    assert receive_response.get_json()["status"] == "received"

    stock_response = client.get(
        f"/products/{product_id}/stock-level"
    )
    assert stock_response.status_code == 200
    assert stock_response.get_json()["quantity_on_hand"] == 15


def test_receiving_purchase_order_records_incoming_transaction(client):
    supplier_response = client.post(
        "/suppliers",
        json={
            "name": "Transaction Supplier",
            "contact_email": "transactions@example.com",
        },
    )
    supplier_id = supplier_response.get_json()["id"]

    product_response = client.post(
        "/products",
        json={
            "name": "Transaction Item",
            "sku": "PO-TRANS-001",
            "unit_price": 8.0,
            "quantity_on_hand": 3,
            "reorder_level": 1,
        },
    )
    product_id = product_response.get_json()["id"]

    order_response = client.post(
        "/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "product_id": product_id,
            "quantity_ordered": 7,
        },
    )
    order_id = order_response.get_json()["id"]

    receive_response = client.put(
        f"/purchase-orders/{order_id}/receive"
    )
    assert receive_response.status_code == 200

    transactions_response = client.get("/transactions")
    assert transactions_response.status_code == 200

    transactions = transactions_response.get_json()
    matching_transactions = [
        transaction
        for transaction in transactions
        if transaction["product_id"] == product_id
        and transaction["supplier_id"] == supplier_id
        and transaction["type"] == "IN"
    ]

    assert len(matching_transactions) == 1
    assert matching_transactions[0]["quantity"] == 7


def test_receiving_purchase_order_twice_does_not_duplicate_stock(client):
    supplier_response = client.post(
        "/suppliers",
        json={
            "name": "Duplicate Test Supplier",
            "contact_email": "duplicate@example.com",
        },
    )
    supplier_id = supplier_response.get_json()["id"]

    product_response = client.post(
        "/products",
        json={
            "name": "Duplicate Test Item",
            "sku": "PO-DUP-001",
            "unit_price": 12.0,
            "quantity_on_hand": 4,
            "reorder_level": 1,
        },
    )
    product_id = product_response.get_json()["id"]

    order_response = client.post(
        "/purchase-orders",
        json={
            "supplier_id": supplier_id,
            "product_id": product_id,
            "quantity_ordered": 6,
        },
    )
    order_id = order_response.get_json()["id"]

    first_receive = client.put(
        f"/purchase-orders/{order_id}/receive"
    )
    second_receive = client.put(
        f"/purchase-orders/{order_id}/receive"
    )

    assert first_receive.status_code == 200
    assert second_receive.status_code == 400

    stock_response = client.get(
        f"/products/{product_id}/stock-level"
    )
    assert stock_response.get_json()["quantity_on_hand"] == 10

    transactions_response = client.get("/transactions")
    transactions = transactions_response.get_json()
    assert len(transactions) == 1
