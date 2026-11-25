import os
from uuid import uuid4

from playwright.sync_api import expect


BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:5000")


def test_delete_supplier(page):
    suffix = uuid4().hex[:8]
    supplier_name = f"Teos Supplier {suffix}"
    email = f"{suffix}@example.com"

    page.goto(f"{BASE_URL}/ui/suppliers")
    page.get_by_label("Name", exact=True).fill(supplier_name)
    page.get_by_label("Contact Email").fill(email)
    page.get_by_role("button", name="Add Supplier").click()

    supplier_row = page.get_by_role("row").filter(has_text=supplier_name)
    expect(supplier_row).to_be_visible()
    expect(supplier_row).to_contain_text(email)

    supplier_row.get_by_role("button", name="Delete").click()
    expect(supplier_row).to_have_count(0)
    page.reload()
    expect(supplier_row).to_have_count(0)


def test_stock_movement_rejects_zero_quantity(page):
    sku = f"TEOS-{uuid4().hex[:8]}"
    page.goto(f"{BASE_URL}/ui/products")
    page.get_by_label("Name", exact=True).fill("Teos Stock Test Product")
    page.get_by_label("SKU").fill(sku)
    page.get_by_label("Unit Price").fill("10")
    page.get_by_label("Quantity on Hand").fill("5")
    page.get_by_role("button", name="Add Product").click()

    product_row = page.get_by_role("row").filter(has_text=sku)
    expect(product_row).to_be_visible()
    product_id = product_row.get_by_role("cell").nth(0).inner_text()

    page.goto(f"{BASE_URL}/ui/transactions")
    transaction_rows = page.get_by_role("row")
    original_row_count = transaction_rows.count()

    page.get_by_label("Product ID", exact=True).fill(product_id)
    page.locator('select[name="type"]').select_option("IN")
    quantity = page.get_by_label("Quantity", exact=True)
    quantity.fill("0")
    page.get_by_role("button", name="Record").click()

    assert quantity.evaluate("(input) => input.validity.rangeUnderflow")
    page.reload()
    expect(transaction_rows).to_have_count(original_row_count)

    page.goto(f"{BASE_URL}/ui/products")
    expect(product_row.get_by_role("cell").nth(4)).to_have_text("5")