---
name: english-grammar
description: Rules for writing clear, professional, grammatically correct English in enterprise financial software — labels, errors, messages, documentation.
---

## General Rules

1. Every user-facing string uses `_("...")` for translation
2. Complete sentences with proper punctuation
3. No contractions: "Cannot" not "can't", "does not" not "doesn't", "is not" not "isn't", "will not" not "won't"
4. No slang, no informal language, no emojis
5. No markdown formatting in flash messages or error toasts

## Capitalisation

| Context | Style | Example |
|---------|-------|---------|
| Field labels | Sentence case | "First Name", "Date of Birth", "Primary Phone" |
| Section headers | Sentence case | "Contact Details", "Nominee Information" |
| DocType names | Title Case with prefix | "KNAPS Person", "KNAPS Lead" |
| Select options | Title Case | "Active", "Passive", "Deceased" |
| Error messages | Sentence case | "PAN must be exactly 10 characters." |
| Buttons | Sentence case | "Save", "Submit", "Create New" |
| Page titles | Title Case | "Lead Dashboard", "Client Portfolio" |

## Error Message Structure

Every error message follows: **[What failed] [Why it failed] [What to do].**

```
"PAN ABCPX1234A is already linked to another person."
"Cannot add a deceased person as a household member."
"Date of birth cannot be in the future."
"At least one phone number must be marked as primary."
```

- Do not start with "Error:" or "ValidationError:" — the UI already shows it is an error.
- Do not end with an exclamation mark unless it is a genuine emergency.
- Do not use passive voice: "Duplicate PAN was found" → "PAN already exists."

## Grammar Rules for Messages

### Articles (a/an/the)
- "a" before consonant sounds: a lead, a person, a unique identifier
- "an" before vowel sounds: an opportunity, an entity, an HUF (aitch — consonant sound? Actually "an HUF" because H is pronounced "aitch" which starts with a vowel sound)
- "an" before "hour" (vowel sound)

### Subject-Verb Agreement
- Singular: "The lead HAS been converted." "The client DOES not have an active policy."
- Plural: "The leads HAVE been imported." "These fields ARE required."

### Prepositions
- linked TO (not linked WITH)
- associated WITH (not associated TO)
- belongs TO (not belongs WITH)
- different FROM (not different THAN)
- consists OF (not consists WITH)

### Tense
- Present tense for current state: "This account is active."
- Past tense for completed actions: "The lead has been converted to a client."
- Future tense for confirmations: "This will delete all linked transactions."
- Imperative for instructions: "Enter a valid 10-character PAN."

## Common Mistakes to Avoid

| Incorrect | Correct |
|-----------|---------|
| "can't be primary" | "Cannot be set as primary." |
| "already exists in this opportunity" | "already exists in this opportunity." (full stop) |
| "Row #1 — Phone is inactive" | "Row #1: Phone +911234567890 is inactive." |
| "returning back" | "returning" (redundant) |
| "reason why" | "reason" (redundant) |
| "the same is attached" | "the document is attached" (avoid "the same") |
| "please revert back" | "please reply" |
| "PAN no." | "PAN" (PAN is an acronym, no need for "no.") |

## Validation Error Templates

```python
# Field-level
frappe.throw(_("{field} is required.").format(field=_("First Name")))

# Uniqueness
frappe.throw(_("{value} is already linked to another {entity}.").format(
    value=doc.pan, entity=_("person")
))

# Cross-field conflict
frappe.throw(_("Cannot set {field_a} to {value_a} when {field_b} is {value_b}.").format(...))

# Row-level (child tables)
frappe.throw(_("Row #{idx}: {field} {value} is {problem}.").format(
    idx=row.idx, value=row.number, problem=_("a duplicate")
))

# Permission
frappe.throw(_("You do not have permission to {action} this document.").format(
    action=_("delete")
), frappe.PermissionError)
```
