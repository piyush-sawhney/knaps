---
name: design-system
description: Architectural patterns for Frappe applications — deciding what to build, entity vs child table, controller vs doc_events, state machines, modelling financial domains.
---

## The First Decision: DocType or Not

Before creating any DocType, ask these questions:

| Question | If Yes | If No |
|----------|--------|-------|
| Does this have its own lifecycle (create → update → delete / submit → cancel)? | Create a DocType | Use a field or child table |
| Does this have its own validation rules? | Create a DocType | Attach to parent's validate |
| Does this need its own permissions? | Create a DocType | Inherit from parent |
| Does this need its own list view or reporting? | Create a DocType | Use a child table |
| Is this a type/category/label for another entity? | Use a Link field or Select | Create a child table |

## Entity vs Child Table

**Create a DocType when:**
- The entity exists independently (a Person exists whether or not they are a Client)
- Multiple parents reference the same instance (a Nominee can be on multiple policies)
- The entity has its own permissions or workflow

**Use a Child Table when:**
- The data belongs exclusively to its parent (Phone numbers belong to the Person)
- The data has no independent lifecycle (a Payment only exists as part of an Investment)
- The data is a simple list of values (Tags, Interests)

## Controller vs doc_events

**Use controller methods (validate, on_update, on_trash) when:**
- The logic is inherent to the entity itself
- The logic runs on every insert/update/delete
- The logic sets fields on the same document

**Use doc_events in hooks.py when:**
- The logic spans multiple DocTypes
- The logic should run for a DocType you do not own
- The logic is a cross-cutting concern (audit logging, notification)

## State Machines and Workflow

- Use Select fields for simple state (3-6 states, no transitions)
- Use Frappe Workflow when transitions need permissions and notifications
- Use custom state validation for complex state machines with side effects

Every state machine should define:
1. Valid states (Select options)
2. Valid transitions (which state can go to which)
3. Side effects on transition (what happens when status changes to Won)

## Modelling Financial Domains

### The Provider Pattern
Financial products refer to external institutions (AMCs, insurers, banks, depositories). These should be:
- A single DocType with a type discriminator, not one DocType per provider type
- Linked to a party (Non Individual) for legal identity
- Representatives as a reusable child table

### The Party Pattern
People and organisations in financial systems typically play multiple roles.
- An Individual entity: personal data, PAN, DOB, contact details
- A Non Individual entity: legal name, registration, PAN
- A Client: the role an entity plays when engaging with financial services
- A Lead: a potential client before qualification
- An Opportunity: An existing client sales opportunity

Each has different validation rules and lifecycles. Do not merge them into one.

## Naming Conventions for DocTypes

- Prefix all custom DocTypes consistently
- Singular nouns: "Person" not "People", "Policy" not "Policies"
- Descriptive but concise: "Client" not "CustomerInformationRecord"
- Child tables: named after the entity they represent: "Phone Number", "Email", "Nominee"
- Reference data: named by what they categorise: "Product Category", "Lead Source", "Entity Type"

## Validation Order for Financial Documents

1. Normalize: uppercase PAN, strip whitespace, format dates
2. Required fields: ensure all mandatory fields are present
3. Format validation: PAN regex, email regex, phone format
4. Range validation: amounts > 0, dates not in future, age in valid range
5. Uniqueness: PAN, account numbers, folio numbers must be unique
6. Cross-field: nominee percentages sum to 100, end date after start date
7. Link validation: referenced documents exist and are active
8. Derived values: compute full name, age, maturity amount
