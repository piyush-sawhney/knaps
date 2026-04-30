// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

// Sync primary contact on form load
frappe.ui.form.on("KNAPS Non Individual", "refresh", function(frm) {
	if(!frm.doc.__islocal) {
  		frappe.contacts.render_address_and_contact(frm);
    } else {
  		frappe.contacts.clear_address_and_contact(frm);
	}
	// Sync primary contact from signatories
	if (frm.doc.signatories && frm.doc.signatories.length) {
		frm.trigger("sync_primary_contact");
	}
});

// Sync primary contact trigger
frappe.ui.form.on("KNAPS Non Individual", "sync_primary_contact", function(frm) {
	const primary = frm.doc.signatories?.find(s => s.is_primary_contact);

	if (primary && primary.signatory) {
		frm.set_value("primary_contact", primary.signatory);
	} else {
		frm.set_value("primary_contact", "");
	}
});

// Signatories (Authorised Signatories) - Primary Contact
frappe.ui.form.on("KNAPS Authorised Signatory", {
	is_primary_contact: function(frm, cdt, cdn) {
		// Auto-uncheck other rows when one is checked
		if (frm.doc.signatories) {
			frm.doc.signatories.forEach(row => {
				if (row.name !== cdn && row.is_primary_contact) {
					frappe.model.set_value(cdt, row.name, "is_primary_contact", 0);
				}
			});
		}
		// Trigger sync
		frm.trigger("sync_primary_contact");
	},

	signatory: function(frm, cdt, cdn) {
		// Trigger sync when signatory changes
		frm.trigger("sync_primary_contact");
	}
});

// Phone Numbers - Primary validation
frappe.ui.form.on("KNAPS Phone Number", {
	is_primary: function(frm, cdt, cdn) {
		// Auto-uncheck other rows when one is checked
		if (frm.doc.phone_numbers) {
			frm.doc.phone_numbers.forEach(row => {
				if (row.name !== cdn && row.is_primary) {
					frappe.model.set_value(cdt, row.name, "is_primary", 0);
				}
			});
		}
	},

	number: function(frm, cdt, cdn) {
		// Auto-check "Is Primary" if first phone
		const row = frm.doc.phone_numbers?.find(r => r.name === cdn);
		if (row && !row.is_primary) {
			const otherRows = frm.doc.phone_numbers?.filter(r => r.name !== cdn);
			const hasExistingPrimary = otherRows?.some(r => r.is_primary);
			if (!hasExistingPrimary) {
				frappe.model.set_value(cdt, cdn, "is_primary", 1);
			}
		}
	}
});

// Email Addresses - Primary validation
frappe.ui.form.on("KNAPS Email", {
	is_primary: function(frm, cdt, cdn) {
		// Auto-uncheck other rows when one is checked
		if (frm.doc.email_addresses) {
			frm.doc.email_addresses.forEach(row => {
				if (row.name !== cdn && row.is_primary) {
					frappe.model.set_value(cdt, row.name, "is_primary", 0);
				}
			});
		}
	},

	email_address: function(frm, cdt, cdn) {
		// Auto-check "Is Primary" if first email
		const row = frm.doc.email_addresses?.find(r => r.name === cdn);
		if (row && !row.is_primary) {
			const otherRows = frm.doc.email_addresses?.filter(r => r.name !== cdn);
			const hasExistingPrimary = otherRows?.some(r => r.is_primary);
			if (!hasExistingPrimary) {
				frappe.model.set_value(cdt, cdn, "is_primary", 1);
			}
		}
	}
});