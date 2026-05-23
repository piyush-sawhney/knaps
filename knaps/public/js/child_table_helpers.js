// Shared helpers for child table row management
// Loaded via app_include_js hook

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
		const hasExistingPrimary = rows.some((r) => r.name !== cdn && r[field]);
		if (!hasExistingPrimary) {
			frappe.model.set_value(cdt, cdn, field, 1);
		}
	}
}
