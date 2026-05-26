frappe.ui.form.on("KNAPS Health Insurance Member", {
	is_primary(frm, cdt, cdn) {
		enforce_single_primary(frm.doc.holders, cdt, cdn, "is_primary");
		auto_mark_first_as_primary(frm.doc.holders, cdt, cdn, "is_primary");
	},
});

frappe.ui.form.on("KNAPS Health Insurance", {
	refresh(frm) {
		frm.trigger("toggle_policy_type_fields");
		frm.trigger("toggle_status_fields");
		frm.trigger("add_open_client_button");
	},
	policy_type(frm) {
		frm.trigger("toggle_policy_type_fields");
	},
	status(frm) {
		frm.trigger("toggle_status_fields");
	},
	toggle_policy_type_fields(frm) {
		const is_floater = frm.doc.policy_type === "Floater";
		frm.set_df_property("floater_sum_insured", "hidden", !is_floater);
		frm.set_df_property("floater_sum_insured", "reqd", is_floater);

		if (frm.doc.holders && frm.doc.holders.length) {
			frm.doc.holders.forEach((row) => {
				const child = locals["KNAPS Health Insurance Member"]?.[row.name];
				if (child && is_floater) {
					frappe.model.set_value(child.doctype, child.name, "sum_insured", 0);
				}
			});
		}
	},
	toggle_status_fields(frm) {
		const is_active_renewed_surrendered = ["Active", "Renewed", "Surrendered"].includes(
			frm.doc.status
		);

		frm.set_df_property("policy_number", "reqd", is_active_renewed_surrendered);
		frm.set_df_property("start_date", "reqd", is_active_renewed_surrendered);
		frm.set_df_property("policy_document", "reqd", is_active_renewed_surrendered);
	},
	add_open_client_button(frm) {
		if (frm.doc.primary_client) {
			frm.add_custom_button(__("Open Client"), function () {
				frappe.set_route("Form", "KNAPS Client", frm.doc.primary_client);
			});
		}
	},
});
