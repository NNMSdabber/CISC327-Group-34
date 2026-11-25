
from playwright.sync_api import expect


BASE_URL = "http://127.0.0.1:5000"


def test_successfully_add_product(page):
    """Verify that a user can successfully add a product."""

    page.goto(f"{BASE_URL}/ui/products")

    page.get_by_label("Name").fill("Playwright Test Product")
    page.get_by_label("SKU").fill("PW-TEST-001")
    page.get_by_label("Unit Price").fill("19.99")
    page.get_by_label("Quantity on Hand").fill("25")

    page.get_by_role("button", name="Add Product").click()

    # Find the product row using its unique SKU.
    product_row = page.locator("table tr").filter(
        has_text="PW-TEST-001"
    )

    # Verify the product was successfully added.
    expect(product_row).to_be_visible()
    expect(product_row).to_contain_text("Playwright Test Product")
    expect(product_row).to_contain_text("19.99")
    expect(product_row).to_contain_text("25")


def test_product_creation_rejects_missing_name(page):
    """Verify that the browser blocks submission when Name is missing."""

    page.goto(f"{BASE_URL}/ui/products")

    name_field = page.get_by_label("Name")

    page.get_by_label("SKU").fill("PW-INVALID-001")
    page.get_by_label("Unit Price").fill("19.99")
    page.get_by_label("Quantity on Hand").fill("10")

    page.get_by_role("button", name="Add Product").click()

    # Verify that the required Name field is invalid.
    assert name_field.evaluate("(element) => element.validity.valueMissing") is True

    # Verify that the invalid product was not added.
    product_row = page.locator("table tr").filter(
        has_text="PW-INVALID-001"
    )
    expect(product_row).to_have_count(0)
