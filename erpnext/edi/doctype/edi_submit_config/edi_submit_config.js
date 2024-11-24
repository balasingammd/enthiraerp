// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("EDI Submit Config", {
	refresh(frm) {
		frappe.call({
			method: "erpnext.edi.doctype.edi_submit_config.edi_submit_config.get_submit_config_type_options",
			callback: function (r) {
				if (r.message) {
					frm.set_df_property("config_type", "options", r.message);
					frm.refresh_field("config_type");
				}
			},
		});
	},
});
