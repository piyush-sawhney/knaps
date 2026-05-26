frappe.ui.form.on("KNAPS Vehicle Insurance", {
	refresh(frm) {
		frm.trigger("toggle_status_fields");
		frm.trigger("add_open_client_button");
	},
	status(frm) {
		frm.trigger("toggle_status_fields");
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
