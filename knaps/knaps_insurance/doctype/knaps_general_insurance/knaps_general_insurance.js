frappe.ui.form.on("KNAPS General Insurance", {
	refresh(frm) {
		frm.trigger("toggle_status_fields");
		frm.trigger("toggle_member_fields");
		frm.trigger("add_open_client_button");
	},
	status(frm) {
		frm.trigger("toggle_status_fields");
	},
	has_multiple_members(frm) {
		frm.trigger("toggle_member_fields");
	},
	start_date(frm) {
		frm.trigger("calculate_maturity_date");
	},
	period_type(frm) {
		frm.trigger("calculate_maturity_date");
	},
	period(frm) {
		frm.trigger("calculate_maturity_date");
	},
	toggle_status_fields(frm) {
		const is_active = ["Active", "Renewed", "Surrendered"].includes(frm.doc.status);
		frm.set_df_property("policy_number", "reqd", is_active);
		frm.set_df_property("start_date", "reqd", is_active);
		frm.set_df_property("policy_document", "reqd", is_active);
	},
	toggle_member_fields(frm) {
		frm.set_df_property("holders", "hidden", !frm.doc.has_multiple_members);
		frm.set_df_property("sum_assured", "read_only", frm.doc.has_multiple_members);
		frm.refresh_field("holders");
		frm.refresh_field("sum_assured");
	},
	calculate_maturity_date(frm) {
		if (frm.doc.start_date && frm.doc.period_type && frm.doc.period > 0) {
			let maturity = null;
			if (frm.doc.period_type === "Days") {
				maturity = frappe.datetime.add_days(frm.doc.start_date, frm.doc.period);
			} else if (frm.doc.period_type === "Months") {
				maturity = frappe.datetime.add_months(frm.doc.start_date, frm.doc.period);
			} else if (frm.doc.period_type === "Years") {
				maturity = frappe.datetime.add_months(frm.doc.start_date, frm.doc.period * 12);
			}
			if (maturity) {
				frm.set_value("maturity_date", maturity);
			}
		} else {
			frm.set_value("maturity_date", null);
		}
	},
	add_open_client_button(frm) {
		if (frm.doc.primary_client) {
			frm.add_custom_button(__("Open Client"), function () {
				frappe.set_route("Form", "KNAPS Client", frm.doc.primary_client);
			});
		}
	},
});
