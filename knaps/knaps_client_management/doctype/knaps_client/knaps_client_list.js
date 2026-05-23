frappe.listview_settings["KNAPS Client"] = {
	add_fields: [
		"client_name",
		"client_type",
		"status",
		"pan",
		"primary_phone",
		"primary_whatsapp",
		"primary_email",
		"is_minor",
		"preferred_contact_mode",
	],
	hide_name_column: true,
	hide_name_filter: true,
	get_indicator: function (doc) {
		const colors = {
			Active: "green",
			Passive: "orange",
			Inactive: "orange",
			Deceased: "red",
		};
		return [__(doc.status), colors[doc.status] || "gray", "status,=," + doc.status];
	},
	formatters: {
		client_type: function (val) {
			if (!val) return "";
			const colors = {
				Individual: "blue",
				"Sole Proprietor": "purple",
				"Non Individual": "cyan",
			};
			const color = colors[val] || "gray";
			return `<span class="indicator-pill ${color}">${__(val)}</span>`;
		},
		pan: function (val) {
			if (!val) return "";
			return "XXXXXX" + val.slice(-4);
		},
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
	},
};
