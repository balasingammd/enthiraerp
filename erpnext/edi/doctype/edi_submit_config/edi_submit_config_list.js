frappe.listview_settings["EDI Submit Config"] = {
	hide_name_column: true,
	hide_name_filter: true,
	custom_filter_configs: () =>
		frappe
			.xcall(
				"erpnext.edi.doctype.edi_submit_config.edi_submit_config.get_submit_config_type_options",
				null,
				"GET"
			)
			.then((options) => {
				return [
					{
						fieldname: "config_type",
						label: __("Config Type"),
						condition: "=",
						is_filter: 1,
						fieldtype: "Select",
						options: ["", ...options],
					},
				];
			}),
};
