---
name: python-conventions
description: Elite Python 3.14 patterns for Frappe controllers — type safety, validation pipelines, cross-document operations, error handling philosophy.
---

## Python 3.14 Features to Use

| Feature | When to Use |
|---------|-------------|
| `TypeVar` / `ParamSpec` | Generic document controllers |
| `Self` return type | Builder patterns, cascading setters |
| `TypeAlias` | Complex union types, DF type aliases |
| Structural pattern matching (`match`/`case`) | Multi-branch validation by entity type |
| `@override` decorator | Overriding Document lifecycle methods |
| `|` for types | `str | None` over `Optional[str]` |

## Controller Lifecycle (Frappe-specific)

```python
class KNAPSDocType(Document):
    def onload(self):
        """Load read-only dynamic data. Runs on every document open."""
        pass

    def validate(self):
        """Main validation pipeline. Runs before every save.
        Order: normalize → validate uniqueness → cross-field → sync → derive."""
        pass

    def before_save(self):
        """Runs after validation, before DB write. For computed fields."""
        pass

    def on_update(self):
        """Runs after DB write. For side effects, notifications, webhooks."""
        pass

    def before_submit(self):
        """Runs before submission for submittable documents."""
        pass

    def on_trash(self):
        """Cleanup linked data before deletion."""
        pass
```

## Validation Pipeline Pattern

Structure the validate method as a clear sequence of private method calls:
1. Normalize (uppercase PAN, strip whitespace, format strings)
2. Validate uniqueness (PAN, email, phone across records)
3. Validate format (regex, length, character set)
4. Validate cross-field rules (entity type + PAN 4th char, investor type + required links)
5. Sync child-to-parent (primary phone → parent field, nomination percentages)
6. Derive computed values (age from DOB, full name from parts)

## Error Handling Philosophy

- Use `frappe.throw()` for user-facing validation errors. It aborts the transaction.
- Use `frappe.msgprint()` for warnings and confirmations. It does not abort.
- Use `frappe.log_error()` for internal errors that need investigation. Do not show stack traces to users.
- Use `frappe.db.rollback()` to undo changes within a savepoint. Never catch and suppress validation errors.
- Error messages must specify WHAT failed and WHY. Never throw a message without context.

## Cross-Document Operations

When updating data in one document based on changes in another:
```python
# For simple field updates (no validation needed)
frappe.db.set_value("Target DocType", target_name, "field", value)

# For complex updates requiring validation
target = frappe.get_doc("Target DocType", target_name)
target.field = value
target.save()  # Triggers target's validate()

# Always guard against infinite loops
if not self.has_value_changed("field_name"):
    return
```

## Frappe-specific Patterns

- `frappe.get_doc()` loads a full document including child tables. Expensive but complete.
- `frappe.db.get_value()` loads a single field. Fast and lightweight.
- `frappe.db.exists()` checks for existence. Perfect for uniqueness validation.
- `frappe.db.set_value()` updates a field without loading the full document.
- `get_doc_before_save()` returns the document state before the current save. Use for change detection.
- `has_value_changed("field")` checks if a specific field was modified. Use to avoid redundant work.

## Imports Order

1. Standard library: `import re`, `from datetime import date`
2. Frappe framework: `import frappe`, `from frappe import _`
3. Frappe model: `from frappe.model.document import Document`
4. Application-specific: `from knaps.utils import helper`
