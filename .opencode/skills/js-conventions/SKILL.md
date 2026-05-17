---
name: js-conventions
description: Elite Frappe JavaScript patterns — form lifecycle, child table management, list view customization, API interaction, DOM discipline.
---

## Core Principle: Never Touch the DOM

Frappe manages the DOM. You manage the model. Always use Frappe APIs to read and write data.

| What you want to do | How to do it |
|---------------------|-------------|
| Set a field value | `frm.set_value("field", value)` |
| Set a child table field | `frappe.model.set_value(cdt, cdn, "field", value)` |
| Get a field value | `frm.doc.field_name` |
| Trigger a handler | `frm.trigger("handler_name")` |
| Refresh child table | `frm.refresh_field("table_fieldname")` |

## Form Event Architecture

Bind events at the module level, never inside another callback:

```javascript
// DocType-level events
frappe.ui.form.on("KNAPS DocType", {
    refresh: function(frm) { /* runs on every form load */ },
    field_name: function(frm) { /* runs when field_name changes */ },
});

// Child table events — bind on the CHILD DocType name
frappe.ui.form.on("KNAPS Child DocType", {
    child_field: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];  // NOT frm.doc.children.find(...)
        frappe.model.set_value(cdt, cdn, "other_field", value);
    },
});
```

Use `frm.trigger()` to invoke named handlers. This keeps the code readable and testable.

## Child Table Helpers — Module Level

Extract reusable logic to module-level functions, not inside event handlers:

```javascript
function enforce_single_primary(rows, cdt, cdn, field) {
    if (!rows) return;
    rows.forEach((row) => {
        if (row.name !== cdn && row[field]) {
            frappe.model.set_value(cdt, row.name, field, 0);
        }
    });
}

function auto_mark_first_as_primary(rows, cdt, cdn, field) {
    if (!rows) return;
    const row = rows.find((r) => r.name === cdn);
    if (row && !row[field]) {
        const hasPrimary = rows.some((r) => r.name !== cdn && r[field]);
        if (!hasPrimary) {
            frappe.model.set_value(cdt, cdn, field, 1);
        }
    }
}
```

## List View Customization

```javascript
frappe.listview_settings["KNAPS DocType"] = {
    add_fields: ["status", "field1", "field2"],
    hide_name_column: true,
    get_indicator: function(doc) {
        const colors = { Active: "green", Inactive: "orange", Deceased: "red" };
        return [__(doc.status), colors[doc.status], "status,=," + doc.status];
    },
    formatters: {
        pan: function(val) {
            return val ? "XXXXXX" + val.slice(-4) : "";
        },
    },
};
```

## API Calls

```javascript
frappe.call({
    method: "knaps.api.method_name",
    args: { key: value },
    callback: function(r) {
        if (r.message) { /* handle success */ }
    },
    error: function(r) {
        frappe.msgprint(__("An error occurred: ") + r.message);
    },
});

// For simple queries
frappe.db.get_value("DocType", { filters }, "field")
    .then(r => { /* r.message.field */ });
```

## Error Handling in JS

- User-facing errors: `frappe.msgprint(__("message"))`
- Confirmation dialogs: `frappe.confirm(__("Are you sure?"), () => { /* on yes */ })`
- Never use `alert()` or `confirm()` — they block the UI and look unprofessional
- Never suppress errors in callbacks — always show feedback
