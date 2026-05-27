frappe.listview_settings["KNAPS Opportunity"] = {
	add_fields: ["client", "phone", "whatsapp", "email"],
	hide_name_column: true,
	hide_name_filter: true,
	formatters: {
		phone: maskPhone,
		whatsapp: maskPhone,
		email: maskEmail,
	},
};
