// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Lead", {
	salutation: function(frm) {
		frm.trigger("update_lead_name");
	},
	first_name: function(frm) {
		frm.trigger("update_lead_name");
	},
	middle_name: function(frm) {
		frm.trigger("update_lead_name");
	},
	last_name: function(frm) {
		frm.trigger("update_lead_name");
	},
	update_lead_name: function(frm) {
		const parts = [];
		if (frm.doc.salutation) parts.push(frm.doc.salutation);
		if (frm.doc.first_name) parts.push(frm.doc.first_name);
		if (frm.doc.middle_name) parts.push(frm.doc.middle_name);
		if (frm.doc.last_name) parts.push(frm.doc.last_name);
		frm.set_value("lead_name", parts.join(" ").trim());
	},
	refresh: function(frm) {
		if(!frm.doc.__islocal) {
  		frappe.contacts.render_address_and_contact(frm);
    } else {
  		frappe.contacts.clear_address_and_contact(frm);
	}
		frm.trigger("update_lead_name");
	}
});
