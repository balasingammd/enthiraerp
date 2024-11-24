// This file is a toolkit to help developing edi templates
// use it e.g. as follows in hooks.py
// doctype_js = {"Sales Invoice": "../../erpnext/erpnext/edi/doctype/edi_template/bound_doctype.js"}
frappe.ui.form.on(cur_frm.doc.doctype, {
	refresh: (frm) => {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "EDI Template",
				filters: {
					status: "Draft",
				},
				fields: ["name"],
			},
			callback: function (r) {
				if (r.message && r.message.length > 0) {
					r.message.forEach(function (template) {
						frm.add_custom_button(
							__(template.name),
							function () {
								frappe.call({
									method: "erpnext.edi.doctype.edi_template.edi_template.manual_process",
									args: {
										doc: frm.doc.name,
										template: template.name,
									},
									callback: function (r) {
										frm.reload_doc();
									},
								});
							},
							__("Create EDI Template")
						);
					});
				} else {
					frappe.msgprint(__("No draft EDI templates found."));
				}
			},
		});
	},
});
