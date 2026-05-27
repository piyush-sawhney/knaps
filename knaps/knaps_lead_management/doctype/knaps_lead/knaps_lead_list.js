frappe.listview_settings["KNAPS Lead"] = {
	add_fields: ["lead_name", "phone", "whatsapp", "email", "lead_type"],
	hide_name_column: true,
	hide_name_filter: true,
	formatters: {
		phone: maskPhone,
		whatsapp: maskPhone,
		email: maskEmail,
	},
};
