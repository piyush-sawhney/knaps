// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Client", {
	client_type: function(frm) {
		let is_non_individual = frm.doc.client_type === "Non Individual";
		let is_sole_proprietor = frm.doc.client_type === "Sole Proprietor";

		if (is_non_individual && frm.doc.person) {
			frm.set_value("person", null);
		}
		if (!is_non_individual && frm.doc.non_individual) {
			frm.set_value("non_individual", null);
		}
		if (!is_sole_proprietor && frm.doc.client_name) {
			frm.set_value("client_name", null);
		}
	},
});
