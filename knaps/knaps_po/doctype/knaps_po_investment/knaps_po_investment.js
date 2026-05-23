frappe.ui.form.on("KNAPS PO Investment", {
	refresh(frm) {
		frm.trigger("add_open_client_button");
	},

	start_date(frm) {
		frm.trigger("calculate_maturity_date");
	},

	period_in_months(frm) {
		frm.trigger("calculate_maturity_date");
	},

	calculate_maturity_date(frm) {
		if (frm.doc.start_date && frm.doc.period_in_months && !frm.doc.extend_investment) {
			let maturity = frappe.datetime.add_months(frm.doc.start_date, frm.doc.period_in_months);
			frm.set_value("maturity_date", maturity);
		}
	},

	extend_investment(frm) {
		if (!frm.doc.extend_investment) {
			frm.trigger("calculate_maturity_date");
		}
	},

	add_open_client_button(frm) {
		if (frm.doc.primary_client) {
			frm.add_custom_button(__("Open Client"), function() {
				frappe.set_route("Form", "KNAPS Client", frm.doc.primary_client);
			});
		}
	},
});
