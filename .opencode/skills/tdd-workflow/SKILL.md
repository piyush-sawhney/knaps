---
name: tdd-workflow
description: Test-Driven Development methodology for Frappe applications. How to think about testing, structure tests, and achieve meaningful coverage.
---

## Testing Philosophy

You test rules, not fields. Every validation rule has exactly one positive test (it passes when conditions are met) and at least one negative test (it fails when conditions are violated).

## Test Structure

Every test class follows this pattern:
- `setUp`: Create savepoint, initialize shared test data
- `tearDown`: Rollback savepoint
- Test methods: Independent, ordered from simple to complex
- Helper functions: Module-level factories that accept overridable defaults

```python
import frappe
from frappe.tests import IntegrationTestCase

EXTRA_TEST_RECORD_DEPENDENCIES = ["Salutation", "Gender"]

def create_knaps_entity(**kwargs):
    doc = frappe.get_doc({
        "doctype": "KNAPS Some DocType",
        "field": kwargs.get("field", "default_value"),
    })
    if kwargs.get("save", True):
        doc.insert()
    return doc

class IntegrationTestKNAPSDocType(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.db.savepoint("knaps_doctype_sp")

    def tearDown(self):
        frappe.db.rollback(save_point="knaps_doctype_sp")
        super().tearDown()
```

## Test Categories (in this order)

1. **Computed / Derived Fields** — auto-calculated values match expectations
2. **Validation — Required** — missing required field fails
3. **Validation — Unique** — duplicate value fails across records
4. **Validation — Format** — invalid format fails (PAN, email, phone)
5. **Validation — Cross-Field** — conflicting field values fail
6. **Validation — Range** — out-of-range values fail (negative amount, future DOB)
7. **Sync / Side Effects** — changes propagate correctly to linked records
8. **Edge Cases** — empty child tables, whitespace in string fields, null values
9. **Deletion Cleanup** — deleting a parent cleans up linked data
10. **Integration** — full workflow with all fields populated

## What to Test for Financial DocTypes

Every financial document must have tests for:
- Null or zero amount rejected
- Negative unit count rejected
- Invalid date rejected (future start date, end before start)
- Required provider/scheme links validated
- Nominee percentage sum does not exceed 100
- Valid creation with complete data succeeds

## Assertion Patterns

```python
# Expect a validation error
self.assertRaises(frappe.ValidationError, doc.insert)

# Check error message content
with self.assertRaises(frappe.ValidationError) as cm:
    doc.insert()
self.assertIn("expected phrase", str(cm.exception).lower())

# Assert field values after save
self.assertEqual(doc.full_name, "Expected Value")
self.assertIsNone(doc.optional_field)

# Check side effects on other documents
self.assertEqual(
    frappe.db.get_value("Linked DocType", linked_name, "field"),
    expected_value
)
```

## Test Independence

- Every test must pass in isolation
- No test depends on the side effects of another test
- No shared mutable state between tests
- Factories always create fresh data
