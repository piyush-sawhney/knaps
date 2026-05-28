frappe.ui.form.on("KNAPS Bank", {
	holding_type: function (frm) {
		const grid = frm.fields_dict.holders.grid;
		if (frm.doc.holding_type == "Single") {
			grid.update_docfield_property("order", "options", "\nFirst\nGuardian");
		} else {
			grid.update_docfield_property("order", "options", "\nFirst\nSecond\nThird");
		}
		grid.refresh();
	},

	refresh: function (frm) {
		if (frm.doc.holding_type) {
			frm.trigger("holding_type");
		}
	},
});
