frappe.listview_settings["KNAPS Fixed Investment"] = {
	hide_name_column: true,
	hide_name_filter: true,
	add_fields: [
		"account_number",
		"investment_type",
		"investment_company",
		"primary_client",
		"client_name",
		"status",
		"amount",
		"start_date",
		"maturity_date",
	],
	get_indicator: function (doc) {
		const status_colors = {
			"Entry Done": "purple",
			Submitted: "yellow",
			Active: "green",
			Renewed: "blue",
			Matured: "gray",
			"Pre-Matured": "pink",
			Transmitted: "orange",
			Rejected: "red",
		};
		return [__(doc.status), status_colors[doc.status] || "gray", "status,=," + doc.status];
	},
	formatters: {
		investment_type: function (val) {
			if (!val) return "";
			const colors = {
				"FD- Fixed Deposit": "blue",
				"NCD - Non Convertible Debentures": "orange",
				BOND: "green",
			};
			const color = colors[val] || "gray";
			return `<span class="indicator-pill ${color}">${__(val)}</span>`;
		},
	},
	dropdown_button: {
		get_label: __("Actions"),
		buttons: [
			{
				get_label: __("View Details"),
				get_description: function () {
					return __("Open investment record");
				},
				action: function (doc) {
					frappe.set_route("Form", "KNAPS Fixed Investment", doc.name);
				},
			},
			{
				show: function (doc) {
					return doc.primary_client ? true : false;
				},
				get_label: __("Open Client"),
				get_description: function (doc) {
					return __("Open {0}", [doc.client_name || doc.primary_client]);
				},
				action: function (doc) {
					frappe.set_route("Form", "KNAPS Client", doc.primary_client);
				},
			},
		],
	},
};
