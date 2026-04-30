// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Person", {
	first_name: function(frm) {
		frm.trigger("update_full_name");
	},
	middle_name: function(frm) {
		frm.trigger("update_full_name");
	},
	last_name: function(frm) {
		frm.trigger("update_full_name");
	},
	update_full_name: function(frm) {
		const parts = [];
		if (frm.doc.first_name) parts.push(frm.doc.first_name);
		if (frm.doc.middle_name) parts.push(frm.doc.middle_name);
		if (frm.doc.last_name) parts.push(frm.doc.last_name);
		frm.set_value("full_name", parts.join(" ").trim());
	}
});