frappe.listview_settings["KNAPS Bank"] = {
	add_fields: [
		"bank_name",
		"account_number",
		"ifsc",
		"branch",
		"holder_type",
		"primary_holder_name",
	],
	hide_name_column: true,
	hide_name_filter: true,
	formatters: {
		account_number: function (val) {
			if (!val) return "";
			if (val.length <= 4) return `<span>${val}</span>`;
			return `<span>${"X".repeat(val.length - 4)}${val.slice(-4)}</span>`;
		},
	},
};
