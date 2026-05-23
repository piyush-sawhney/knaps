// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Non Individual", "refresh", function (frm) {
	if (!frm.doc.__islocal) {
		frappe.contacts.render_address_and_contact(frm);
	} else {
		frappe.contacts.clear_address_and_contact(frm);
	}

	if (frm.doc.entity_profile) {
		frm.add_custom_button(__("Open Profile"), function () {
			frappe.set_route("Form", "KNAPS Non Individual Profile", frm.doc.entity_profile);
		});
	} else {
		frm.add_custom_button(__("Create Profile"), function () {
			frappe.new_doc("KNAPS Non Individual Profile", {
				non_individual_entity: frm.doc.name,
			});
		});
	}
});

// Phone Numbers - Primary validation
frappe.ui.form.on("KNAPS Phone Number", {
	is_primary: function (frm, cdt, cdn) {
		enforce_single_primary(frm.doc.phone_numbers, cdt, cdn, "is_primary");
	},

	number: function (frm, cdt, cdn) {
		auto_mark_first_as_primary(frm.doc.phone_numbers, cdt, cdn, "is_primary");
	},
});

// Email Addresses - Primary validation
frappe.ui.form.on("KNAPS Email", {
	is_primary: function (frm, cdt, cdn) {
		enforce_single_primary(frm.doc.email_addresses, cdt, cdn, "is_primary");
	},

	email_address: function (frm, cdt, cdn) {
		auto_mark_first_as_primary(frm.doc.email_addresses, cdt, cdn, "is_primary");
	},
});

// Entity Contacts - Single primary enforcement
frappe.ui.form.on("KNAPS Entity Contact", {
	is_primary_contact: function (frm, cdt, cdn) {
		enforce_single_primary(frm.doc.contacts, cdt, cdn, "is_primary_contact");
	},
});
