// Copyright (c) 2026, KNAPS and Contributors and contributors
// For license information, please see license.txt

frappe.ui.form.on("KNAPS Family Member", {
	member_type: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		const grid_row = frm.fields_dict.members.grid.get_row(cdn);
		if (grid_row) {
			const isPerson = row.member_type === "KNAPS Person";
			grid_row.toggle_reqd("relation_with_head", isPerson);
			grid_row.toggle_editable("relation_with_head", isPerson);
			if (!isPerson && row.relation_with_head) {
				frappe.model.set_value(cdt, cdn, "relation_with_head", null);
			}
		}
	},
});
