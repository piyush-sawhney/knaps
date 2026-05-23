// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Client", {
	refresh: function (frm) {
		frm.trigger("add_navigation_buttons");
	},
	add_navigation_buttons: function (frm) {
		frm.clear_custom_buttons();

		if (frm.doc.individual) {
			frm.add_custom_button(__("Open Individual"), function () {
				frappe.set_route("Form", "KNAPS Individual", frm.doc.individual);
			});
		}

		if (frm.doc.non_individual) {
			frm.add_custom_button(__("Open Non Individual"), function () {
				frappe.set_route("Form", "KNAPS Non Individual", frm.doc.non_individual);
			});
		}
	},
});

frappe.ui.form.on("KNAPS Client", "client_type", function (frm) {
	if (frm.doc.client_type !== "Non Individual") {
		if (frm.doc.non_individual) frm.set_value("non_individual", null);
	}
	frm.trigger("add_navigation_buttons");
});
