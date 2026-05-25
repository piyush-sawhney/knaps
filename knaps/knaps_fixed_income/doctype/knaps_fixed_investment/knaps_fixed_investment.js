frappe.ui.form.on("KNAPS Fixed Investment", {
	refresh(frm) {
		frm.trigger("add_open_client_button");
	},

	add_open_client_button(frm) {
		if (frm.doc.primary_client) {
			frm.add_custom_button(__("Open Client"), function () {
				frappe.set_route("Form", "KNAPS Client", frm.doc.primary_client);
			});
		}
	},
});
