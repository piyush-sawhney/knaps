frappe.listview_settings["KNAPS Individual"] = {
	add_fields: [
		"full_name",
		"age",
		"date_of_birth",
		"status",
		"gender",
		"pan",
		"primary_phone",
		"primary_whatsapp",
		"primary_email",
		"family",
		"preferred_contact_mode",
	],
	hide_name_column: true,
	hide_name_filter: true,
	get_indicator: function (doc) {
		const colors = {
			Active: "green",
			Passive: "orange",
			Deceased: "red",
		};
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
	formatters: {
		age: function (val, df, doc) {
			if (!doc.date_of_birth || val == null) return "";
			return val + " yrs";
		},
		pan: function (val) {
			if (!val) return "";
			return "XXXXXX" + val.slice(-4);
		},
		preferred_contact_mode: function (val) {
			if (!val) return "";
			const icons = {
				Phone: "fa fa-phone",
				Whatsapp: "fa fa-whatsapp",
				Email: "fa fa-envelope",
			};
			return `<i class="${icons[val] || "fa fa-circle"}"></i> ${val}`;
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
