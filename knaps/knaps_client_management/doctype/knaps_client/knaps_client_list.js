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
		pan: maskPAN,
		primary_phone: maskPhone,
		primary_whatsapp: maskPhone,
		primary_email: maskEmail,
	},
};
