frappe.listview_settings["KNAPS Person"] = {
	add_fields: [
		"full_name",
		"age",
		"date_of_birth",
		"status",
		"gender",
		"pan",
		"primary_phone",
		"primary_email",
		"primary_household",
		"preferred_contact_mode",
	],
	hide_name_column: true,
	hide_name_filter: true,
	get_indicator: function (doc) {
		var colors = {
			Active: "green",
			Passive: "orange",
			Deceased: "red",
		};
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
	formatters: {
		age: function (val, df, doc) {
			if (!doc.date_of_birth) return "";
			return val + " yrs";
		},
		pan: function (val) {
			if (!val) return "";
			return "XXXXXX" + val.slice(-4);
		},
		preferred_contact_mode: function (val) {
			if (!val) return "";
			var icons = {
				Phone: "fa fa-phone",
				Whatsapp: "fa fa-whatsapp",
				Email: "fa fa-envelope",
			};
			return `<i class="${icons[val] || "fa fa-circle"}"></i> ${val}`;
		},
	},
};
