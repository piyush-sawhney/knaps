frappe.listview_settings["KNAPS Client"] = {
	add_fields: [
		"client_name",
		"client_type",
		"primary_phone",
		"primary_whatsapp",
		"primary_email",
		"pan",
		"status",
	],
	hide_name_column: true,
	hide_name_filter: true,
	formatters: {
		primary_phone: function (val) {
			if (!val) return "";
			if (val.length <= 7) return `<span>${val}</span>`;
			return `<span>${val.slice(0, 5)}${"X".repeat(val.length - 7)}${val.slice(-2)}</span>`;
		},
		primary_whatsapp: function (val) {
			if (!val) return "";
			if (val.length <= 7) return `<span>${val}</span>`;
			return `<span>${val.slice(0, 5)}${"X".repeat(val.length - 7)}${val.slice(-2)}</span>`;
		},
		primary_email: function (val) {
			if (!val) return "";
			const parts = val.split("@");
			if (parts.length !== 2) return `<span>${val}</span>`;
			const local = parts[0];
			if (local.length <= 4) return `<span>${val}</span>`;
			return `<span>${local.slice(0, 2)}XXXXX${local.slice(-2)}@${parts[1]}</span>`;
		},
		pan: function (val) {
			if (!val) return "";
			return "XXXXXX" + val.slice(-4);
		},
	},
};
