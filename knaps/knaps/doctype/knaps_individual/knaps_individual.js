// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

// Shared helpers (enforce_single_primary, auto_mark_first_as_primary)
// are loaded globally via app_include_js from child_table_helpers.js

// Full name update handlers
frappe.ui.form.on("KNAPS Individual", {
	salutation: function (frm) {
		frm.trigger("update_full_name");
	},
	first_name: function (frm) {
		frm.trigger("update_full_name");
	},
	middle_name: function (frm) {
		frm.trigger("update_full_name");
	},
	last_name: function (frm) {
		frm.trigger("update_full_name");
	},
	update_full_name: function (frm) {
		const parts = [];
		if (frm.doc.salutation) parts.push(frm.doc.salutation);
		if (frm.doc.first_name) parts.push(frm.doc.first_name);
		if (frm.doc.middle_name) parts.push(frm.doc.middle_name);
		if (frm.doc.last_name) parts.push(frm.doc.last_name);
		frm.set_value("full_name", parts.join(" ").trim());
	},
});

frappe.ui.form.on("KNAPS Individual", "refresh", function (frm) {
	if (!frm.doc.__islocal) {
		frappe.contacts.render_address_and_contact(frm);
	} else {
		frappe.contacts.clear_address_and_contact(frm);
	}
	if (frm.doc.phone_numbers && frm.doc.phone_numbers.length) {
		frm.trigger("sync_primary_phone");
		frm.trigger("sync_primary_whatsapp");
	}
	if (frm.doc.email_address && frm.doc.email_address.length) {
		frm.trigger("sync_primary_email");
	}
	frm.trigger("update_full_name");

	if (frm.doc.profile_link) {
		frm.add_custom_button(__("Open Profile"), function () {
			frappe.set_route("Form", "KNAPS Individual Profile", frm.doc.profile_link);
		});
	} else {
		frm.add_custom_button(__("Create Profile"), function () {
			frappe.new_doc("KNAPS Individual Profile", { individual: frm.doc.name });
		});
	}
});

// KNAPS Phone Number child table events
frappe.ui.form.on("KNAPS Phone Number", {
	is_primary: function (frm, cdt, cdn) {
		enforce_single_primary(frm.doc.phone_numbers, cdt, cdn, "is_primary");
		frm.trigger("sync_primary_phone");
	},
	is_whatsapp: function (frm, cdt, cdn) {
		enforce_single_primary(frm.doc.phone_numbers, cdt, cdn, "is_whatsapp");
		frm.trigger("sync_primary_whatsapp");
	},
	number: function (frm, cdt, cdn) {
		auto_mark_first_as_primary(frm.doc.phone_numbers, cdt, cdn, "is_primary");
		frm.trigger("sync_primary_phone");
		frm.trigger("sync_primary_whatsapp");
	},
	is_active: function (frm, cdt, cdn) {
		const row = frm.doc.phone_numbers?.find((r) => r.name === cdn);
		if (row && !row.is_active) {
			if (row.is_primary) frappe.model.set_value(cdt, cdn, "is_primary", 0);
			if (row.is_whatsapp) frappe.model.set_value(cdt, cdn, "is_whatsapp", 0);
		}
		frm.trigger("sync_primary_phone");
		frm.trigger("sync_primary_whatsapp");
	},
});

// KNAPS Email child table events
frappe.ui.form.on("KNAPS Email", {
	is_active: function (frm, cdt, cdn) {
		const row = frm.doc.email_address?.find((r) => r.name === cdn);
		if (row && !row.is_active && row.is_primary) {
			frappe.model.set_value(cdt, cdn, "is_primary", 0);
		}
		frm.trigger("sync_primary_email");
	},
	is_primary: function (frm, cdt, cdn) {
		enforce_single_primary(frm.doc.email_address, cdt, cdn, "is_primary");
		frm.trigger("sync_primary_email");
	},
	email_address: function (frm, cdt, cdn) {
		auto_mark_first_as_primary(frm.doc.email_address, cdt, cdn, "is_primary");
		frm.trigger("sync_primary_email");
	},
});

// Sync triggers for parent fields
frappe.ui.form.on("KNAPS Individual", {
	sync_primary_phone: function (frm) {
		const primary_phone = frm.doc.phone_numbers?.find((p) => p.is_primary);
		const value = primary_phone?.number || "";
		if (frm.doc.primary_phone !== value) {
			frm.set_value("primary_phone", value);
		}
	},
	sync_primary_whatsapp: function (frm) {
		const whatsapp_phone = frm.doc.phone_numbers?.find((p) => p.is_whatsapp);
		const value = whatsapp_phone?.number || "";
		if (frm.doc.primary_whatsapp !== value) {
			frm.set_value("primary_whatsapp", value);
		}
	},
	sync_primary_email: function (frm) {
		const primary_email = frm.doc.email_address?.find((e) => e.is_primary);
		const value = primary_email?.email_address || "";
		if (frm.doc.primary_email !== value) {
			frm.set_value("primary_email", value);
		}
	},
});
