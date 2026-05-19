frappe.listview_settings["KNAPS Opportunity"] = {
	add_fields: ["client", "phone", "whatsapp", "email"],
	hide_name_column: true,
	hide_name_filter: true,
	formatters: {
		phone: function (val) {
			if (!val) return "";
			if (val.length <= 7) return `<span>${val}</span>`;
			return `<span>${val.slice(0, 5)}${"X".repeat(val.length - 7)}${val.slice(-2)}</span>`;
		},
		whatsapp: function (val) {
			if (!val) return "";
			if (val.length <= 7) return `<span>${val}</span>`;
			return `<span>${val.slice(0, 5)}${"X".repeat(val.length - 7)}${val.slice(-2)}</span>`;
		},
		email: function (val) {
			if (!val) return "";
			const parts = val.split("@");
			if (parts.length !== 2) return `<span>${val}</span>`;
			const local = parts[0];
			if (local.length <= 4) return `<span>${val}</span>`;
			return `<span>${local.slice(0, 2)}XXXXX${local.slice(-2)}@${parts[1]}</span>`;
		},
	},
};
