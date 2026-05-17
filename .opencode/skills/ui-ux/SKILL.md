---
name: ui-ux
description: Principles for building user-friendly enterprise interfaces in Frappe — error messages, confirmations, terminology, form design, accessibility.
---

## Error Messages

Every error message must answer two questions: **What happened?** and **What should the user do?**

| Template | Example |
|----------|---------|
| "{field} is required." | "First Name is required." |
| "{value} already exists for {context}." | "PAN ABCPX1234A is already linked to another person." |
| "{field} must be {constraint}." | "Date of Birth must be in the past." |
| "Cannot {action} because {reason}." | "Cannot delete this document because it has linked transactions." |
| "Row #{idx}: {field} is {problem}." | "Row #2: Phone number is a duplicate." |

Rules:
- Start specific, end general. Tell them exactly what is wrong, then what to do.
- Never blame the user: not "You entered an invalid PAN" but "PAN must be 10 alphanumeric characters."
- Never show technical details: not "ForeignKey constraint failed" but "Cannot delete this client because they have active investments."
- Use "must" not "should" for validation rules. "Must" is unambiguous.

## Confirmation Dialogs

Use for:
- Deleting documents
- Changing status to a terminal state (Won, Lost, Cancelled)
- Operations that cannot be undone

```javascript
frappe.confirm(
    __("Are you sure you want to mark this lead as Lost?"),
    function() { /* on confirm */ }
);
```

## Terminology

- Be consistent across the entire application. If you say "Client" in one place, do not say "Customer" in another.
- Use standard financial terminology. "Premium" for insurance, "NAV" for mutual funds, "Folio" for MF investments.
- Avoid internal jargon: not "doctype" in user-facing messages, not "FK" in labels.
- Use the same term for the same concept everywhere. A "holder" on one form should not be called "owner" on another.

## Form Design

- Group related fields into sections with clear section breaks
- Put the most important fields first (name, status, identifier)
- Use column breaks to reduce vertical scrolling on desktop
- Read-only computed fields should be visually distinct (no border, grey background)
- Link fields should have a clear search context (which Doctype to search, how to identify records)
- Required fields must be visually marked. Do not overuse required — only truly mandatory fields

## Accessibility Basics

- Labels must be meaningful without surrounding context. "Name" is ambiguous; "Client Name" is clear.
- All icons must have tooltips or alt text
- Colour alone must not convey meaning. Use text + colour: "Active (green)" and "Inactive (orange)"
- Error messages should appear near the field that caused them when possible

## Messages to Users

| Type | Style | Example |
|------|-------|---------|
| Success | Confirm action completed | "Lead has been converted to Client successfully." |
| Info | Provide useful context | "This client has 3 active investments." |
| Warning | Non-blocking concern | "This PAN is already linked to another client. Please verify." |
| Error | Blocking problem | "Date of Birth cannot be in the future." |
