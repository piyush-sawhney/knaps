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
		if (frm.doc.phone_numbers) {
			frm.doc.phone_numbers.forEach((row) => {
				if (row.name !== cdn && row.is_primary) {
					frappe.model.set_value(cdt, row.name, "is_primary", 0);
				}
			});
		}
	},

	number: function (frm, cdt, cdn) {
		const row = frm.doc.phone_numbers?.find((r) => r.name === cdn);
		if (row && !row.is_primary) {
			const otherRows = frm.doc.phone_numbers?.filter((r) => r.name !== cdn);
			const hasExistingPrimary = otherRows?.some((r) => r.is_primary);
			if (!hasExistingPrimary) {
				frappe.model.set_value(cdt, cdn, "is_primary", 1);
			}
		}
	},
});

// Email Addresses - Primary validation
frappe.ui.form.on("KNAPS Email", {
	is_primary: function (frm, cdt, cdn) {
		if (frm.doc.email_addresses) {
			frm.doc.email_addresses.forEach((row) => {
				if (row.name !== cdn && row.is_primary) {
					frappe.model.set_value(cdt, row.name, "is_primary", 0);
				}
			});
		}
	},

	email_address: function (frm, cdt, cdn) {
		const row = frm.doc.email_addresses?.find((r) => r.name === cdn);
		if (row && !row.is_primary) {
			const otherRows = frm.doc.email_addresses?.filter((r) => r.name !== cdn);
			const hasExistingPrimary = otherRows?.some((r) => r.is_primary);
			if (!hasExistingPrimary) {
				frappe.model.set_value(cdt, cdn, "is_primary", 1);
			}
		}
	},
});
