frappe.listview_settings["KNAPS Person"] = {
	add_fields: [
		"full_name",
		"age",
		"status",
		"gender",
		"pan",
		"primary_phone",
		"primary_email",
		"primary_household",
		"preferred_contact_mode",
	],
	hide_name_column: true,
	get_indicator: function (doc) {
		var colors = {
			Active: "green",
			Passive: "orange",
			Deceased: "red",
		};
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
	formatters: {
		age: function (val) {
			if (val == null) return "";
			return val + " yrs";
		},
		pan: function (val) {
			if (!val) return "";
			return "XXXXXX" + val.slice(-4);
		},
		preferred_contact_mode: function (val) {
			if (!val) return "";
			var icons = { Phone: "phone", Whatsapp: "whatsapp", Email: "mail" };
			return `<i class="fa fa-${icons[val] || "circle"}"></i> ${val}`;
		},
	},
};
