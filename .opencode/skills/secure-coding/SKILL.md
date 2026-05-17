---
name: secure-coding
description: Security principles for Frappe web applications — threat modelling, input validation, SQL injection prevention, permission checks, PII protection.
---

## Security Mindset

Security is not a feature. It is a property of the entire system. Every input is an attack vector. Every output is a potential leak.

## Core Principles

### Principle 1: Never Trust Input
Validate every parameter from the client for: type, length, format, allowed values, range.
- String inputs: strip whitespace, enforce max length, validate against regex
- Numeric inputs: cast to expected type, check non-negative where applicable
- Date inputs: validate format, check not in future for birth dates
- Link inputs: verify the linked document exists and is active

### Principle 2: Always Parameterize SQL
```python
# INSECURE — string interpolation is SQL injection
frappe.db.sql(f"SELECT name FROM tabDocType WHERE field = '{value}'")

# SECURE — parameterized query
frappe.db.sql("SELECT name FROM `tabDocType` WHERE field = %s", value)

# BEST — use Frappe ORM (always parameterized)
frappe.db.exists("DocType", {"field": value})
```

The Frappe ORM methods are always parameterized:
- `frappe.db.exists()`
- `frappe.db.get_value()`
- `frappe.db.get_all()`
- `frappe.get_doc()`
- `frappe.db.set_value()`

Avoid raw SQL unless you cannot express the query in the ORM. When you must use raw SQL, always use `%s` placeholders.

### Principle 3: Check Permissions on Every Entry Point
Every `@frappe.whitelist()` method must check permissions:
```python
@frappe.whitelist()
def my_api_method(docname):
    if not frappe.has_permission("KNAPS DocType", ptype="read", doc=docname):
        frappe.throw(_("You do not have permission to access this document."), frappe.PermissionError)
```

### Principle 4: Mask Personally Identifiable Information
- PAN: Show only last 4 characters: `XXXXXX1234`
- Phone: Show only first 2 and last 2 digits: `91XXXXXX10`
- Email: Show only first character and domain: `j***@example.com`
- Mask PII in list views, logs, and API responses for non-audit roles

### Principle 5: Defence in Depth
- Client-side validation is for UX. Server-side validation is for security.
- Frappe handles CSRF automatically for `frappe.call()` — never use raw `fetch()` or `XMLHttpRequest`.
- Never expose internal document names or IDs to unauthorized users.
- Log security-relevant events: failed login attempts, permission violations, data export.

## Common Vulnerability Patterns in Frappe

| Pattern | Risk | Mitigation |
|---------|------|------------|
| String formatting in SQL | SQL injection | Parameterized queries |
| Unvalidated `frappe.form_dict` | Type confusion, injection | Cast to expected type |
| No permission check in whitelisted method | Authorization bypass | `frappe.has_permission()` |
| Direct DOM manipulation in JS | XSS if input contains HTML | `frappe.model.set_value()` |
| PII in logs or API responses | Data leak | Mask before logging |
| Hardcoded secrets in source | Credential leak | `frappe.conf` or environment |
