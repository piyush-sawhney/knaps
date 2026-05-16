frappe.listview_settings["KNAPS Non Individual"] = {
	add_fields: [
		"legal_name",
		"non_individual_type",
		"status",
		"pan",
		"primary_contact",
		"primary_contact_phone",
		"primary_contact_email",
		"primary_contact_whatsapp",
	],
	hide_name_column: true,
	hide_name_filter: true,
	get_indicator: function (doc) {
		var colors = {
			Active: "green",
			Inactive: "orange",
		};
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
	formatters: {
		pan: function (val) {
			if (!val) return "";
			return "XXXXXX" + val.slice(-4);
		},
	},
};
