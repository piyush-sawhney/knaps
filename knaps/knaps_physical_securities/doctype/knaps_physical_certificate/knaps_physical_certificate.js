// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Physical Certificate", {
	distinctive_number_from: function (frm, cdt, cdn) {
		update_quantity(frm, cdt, cdn);
	},
	distinctive_number_to: function (frm, cdt, cdn) {
		update_quantity(frm, cdt, cdn);
	},
});

function update_quantity(frm, cdt, cdn) {
	let row = frappe.get_doc(cdt, cdn);
	if (row.distinctive_number_from && row.distinctive_number_to) {
		let from_num = parseInt(row.distinctive_number_from, 10);
		let to_num = parseInt(row.distinctive_number_to, 10);
		if (!isNaN(from_num) && !isNaN(to_num) && from_num <= to_num) {
			frappe.model.set_value(cdt, cdn, "quantity", to_num - from_num + 1);
		}
	}
}
