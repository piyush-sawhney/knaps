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

function maskPhone(val) {
	if (!val) return "";
	if (val.length <= 7) return `<span>${val}</span>`;
	return `<span>${val.slice(0, 5)}${"X".repeat(val.length - 7)}${val.slice(-2)}</span>`;
}

function maskEmail(val) {
	if (!val) return "";
	const parts = val.split("@");
	if (parts.length !== 2) return `<span>${val}</span>`;
	const local = parts[0];
	if (local.length <= 4) return `<span>${val}</span>`;
	return `<span>${local.slice(0, 2)}XXXXX${local.slice(-2)}@${parts[1]}</span>`;
}

function maskPAN(val) {
	if (!val) return "";
	return "XXXXXX" + val.slice(-4);
}
