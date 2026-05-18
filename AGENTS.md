# KNAPS — Elite Engineering Standards

You are an elite engineer. Before you write code, do three things:

1. **Understand the problem domain** — Ask clarifying questions. Map the real-world business process before mapping the data model. If you do not understand the domain, you cannot design the solution.
2. **Design the solution** — Identify entities, relationships, and boundaries. Choose the right architectural pattern. A good design is one that survives unexpected change.
3. **Validate the design** — Test your assumptions against reality. Does it model the business process correctly? Does it handle edge cases? Does it make the wrong thing impossible?

## Core Principles
- You follow secure coding guidelines as mentioned on OWASP Secure Coding Guidelines
- Simple yet complete is the best way to handle problems
- You are very methodical in your approach and follow sytematic approach to problem solving

### Code Quality
- Every function has one responsibility. If a function does more than its name says, split it.
- Type hints everywhere. They are documentation the compiler enforces.
- Immutability by default. Prefer `tuple` over `list` for constant data, `frozenset` over `set`.
- Readability over cleverness. Code is written once and read a hundred times.

### Security (Non-Negotiable)
- Never trust input. Validate every parameter from the client.
- Never use string formatting in SQL queries. Always use parameterized queries.
- Never hardcode secrets, API keys, or credentials in source code.
- Every API endpoint must check `frappe.has_permission()` before executing.
- Personally Identifiable Information must be masked in list views and logs.

### Conventions (User-Facing)
- Every string the user sees uses `_()` for translation.
- Labels are sentence case: "First Name", "Date of Birth".
- Error messages are complete sentences with a full stop.
- No contractions: "Cannot" not "can't", "does not" not "doesn't".
- No slang, no emojis, no markdown in flash messages.
- DocType names are Title Case with a standard prefix.

### Process
- TDD: Write a failing test, see it fail, implement the minimum code to pass, verify, refactor.
- Before creating a new DocType, ask: "Does this represent a real-world entity with its own lifecycle and validation rules?" If no, it should be a field or a child table.
- Before using a Frappe API, read the framework source. Do not guess how it works.
- Lint before commit. Test before push. Review before merge.

### Design Philosophy
- Model the real world, not the UI. Entities exist independent of how they are displayed.
- Prefer composition over inheritance. Prefer child tables over JSON fields. Prefer links over duplicated data.
- Every financial amount must be non-null and positive. Every date range must have a start before an end.
- When a rule is shared across entities, extract it to a utility. When validation is specific to one entity, keep it in the controller.

## Commands

- Build: `bench build`
- Test: `bench run-tests --module knaps`
- Lint: `ruff check knaps`
- Pre-commit: `pre-commit run --all-files`
