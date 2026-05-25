frappe.ui.form.on("KNAPS RD Account", {
	refresh(frm) {
		frm.trigger("add_open_po_investment_button");
	},

	card_number(frm) {
		frm.trigger("compute_effective_card");
	},

	extension_card_number(frm) {
		frm.trigger("compute_effective_card");
	},

	compute_effective_card(frm) {
		let effective = frm.doc.extension_card_number || frm.doc.card_number;
		frm.set_value("effective_card_number", effective);
		frm.set_value("is_updated", effective ? 1 : 0);
	},

	add_open_po_investment_button(frm) {
		if (frm.doc.po_rd_investment) {
			frm.add_custom_button(__("Open PO Investment"), function() {
				frappe.set_route("Form", "KNAPS PO Investment", frm.doc.po_rd_investment);
			});
		}
	},
});
