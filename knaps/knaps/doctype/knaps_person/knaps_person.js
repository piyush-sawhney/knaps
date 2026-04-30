// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

// Full name update handlers
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

// FIXED: Use string syntax for form-level events
frappe.ui.form.on("KNAPS Person", "refresh", function(frm) {
	if(!frm.doc.__islocal) {
  		frappe.contacts.render_address_and_contact(frm);
    } else {
  		frappe.contacts.clear_address_and_contact(frm);
	}
	// Sync primary fields on form load
	if (frm.doc.phone_numbers && frm.doc.phone_numbers.length) {
		frm.trigger("sync_primary_phone");
		frm.trigger("sync_primary_whatsapp");
	}
	if (frm.doc.email_address && frm.doc.email_address.length) {
		frm.trigger("sync_primary_email");
	}
	frm.trigger("update_full_name");
});

// Sync primary fields from child tables
frappe.ui.form.on("KNAPS Phone Number", {
	is_primary: function(frm, cdt, cdn) {
		if (frm.doc.phone_numbers) {
			frm.doc.phone_numbers.forEach(row => {
				if (row.name !== cdn && row.is_primary) {
					frappe.model.set_value(cdt, row.name, "is_primary", 0);
				}
			});
		}
		frm.trigger("sync_primary_phone");
	},
	is_whatsapp: function(frm, cdt, cdn) {
		if (frm.doc.phone_numbers) {
			frm.doc.phone_numbers.forEach(row => {
				if (row.name !== cdn && row.is_whatsapp) {
					frappe.model.set_value(cdt, row.name, "is_whatsapp", 0);
				}
			});
		}
		frm.trigger("sync_primary_whatsapp");
	},
	number: function(frm, cdt, cdn) {
		// Auto-check "Is Primary" if it's the first phone row
		const row = frm.doc.phone_numbers?.find(r => r.name === cdn);
		if (row && !row.is_primary) {
			const otherRows = frm.doc.phone_numbers?.filter(r => r.name !== cdn);
			const hasExistingPrimary = otherRows?.some(r => r.is_primary);
			if (!hasExistingPrimary) {
				frappe.model.set_value(cdt, cdn, "is_primary", 1);
			}
		}
		frm.trigger("sync_primary_phone");
		frm.trigger("sync_primary_whatsapp");
	}
});

frappe.ui.form.on("KNAPS Email", {
	is_primary: function(frm, cdt, cdn) {
		if (frm.doc.email_address) {
			frm.doc.email_address.forEach(row => {
				if (row.name !== cdn && row.is_primary) {
					frappe.model.set_value(cdt, row.name, "is_primary", 0);
				}
			});
		}
		frm.trigger("sync_primary_email");
	},
	email_address: function(frm, cdt, cdn) {
		// Auto-check "Is Primary" if it's the first email row
		const row = frm.doc.email_address?.find(r => r.name === cdn);
		if (row && !row.is_primary) {
			const otherRows = frm.doc.email_address?.filter(r => r.name !== cdn);
			const hasExistingPrimary = otherRows?.some(r => r.is_primary);
			if (!hasExistingPrimary) {
				frappe.model.set_value(cdt, cdn, "is_primary", 1);
			}
		}
		frm.trigger("sync_primary_email");
	}
});

// Sync triggers for parent fields
frappe.ui.form.on("KNAPS Person", {
	sync_primary_phone: function(frm) {
		const primary_phone = frm.doc.phone_numbers?.find(p => p.is_primary);
		const value = primary_phone?.number || "";
		if (frm.doc.primary_phone !== value) {
			frm.doc.primary_phone = value;
			const field = frm.fields_dict.primary_phone;
			if (field && field.$input) {
				field.$input.val(value).trigger("change");
			}
		}
	},
	sync_primary_whatsapp: function(frm) {
		const whatsapp_phone = frm.doc.phone_numbers?.find(p => p.is_whatsapp);
		const value = whatsapp_phone?.number || "";
		if (frm.doc.primary_whatsapp !== value) {
			frm.doc.primary_whatsapp = value;
			const field = frm.fields_dict.primary_whatsapp;
			if (field && field.$input) {
				field.$input.val(value).trigger("change");
			}
		}
	},
	sync_primary_email: function(frm) {
		const primary_email = frm.doc.email_address?.find(e => e.is_primary);
		const value = primary_email?.email_address || "";
		if (frm.doc.primary_email !== value) {
			frm.doc.primary_email = value;
			const field = frm.fields_dict.primary_email;
			if (field && field.$input) {
				field.$input.val(value).trigger("change");
			}
		}
	}
});