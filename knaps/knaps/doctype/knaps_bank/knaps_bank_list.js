frappe.listview_settings["KNAPS Bank"] = {
	add_fields: [
		"bank_name",
		"bank_account_number",
		"ifsc",
		"bank_branch",
		"holder_type",
		"first_holder_name",
	],
	hide_name_column: true,
	hide_name_filter: true,
	formatters: {
		bank_account_number: function (val) {
			if (!val) return "";
			if (val.length <= 4) return `<span>${val}</span>`;
			return `<span>${"X".repeat(val.length - 4)}${val.slice(-4)}</span>`;
		},
	},
};
