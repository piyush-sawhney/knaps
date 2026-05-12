// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Lead", {
	refresh: function(frm) {
		if(!frm.doc.__islocal) {
  		frappe.contacts.render_address_and_contact(frm);
    } else {
  		frappe.contacts.clear_address_and_contact(frm);
	}}
});
