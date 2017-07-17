// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Process Payroll", {
	onload: function (frm) {
		frm.doc.posting_date = frappe.datetime.nowdate();
		frm.doc.start_date = '';
		frm.doc.end_date = '';
		frm.doc.payroll_frequency = '';
		frm.toggle_reqd(['payroll_frequency'], !frm.doc.salary_slip_based_on_timesheet);
	},

	setup: function (frm) {
		frm.set_query("payment_account", function () {
			var account_types = ["Bank", "Cash"];
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			}
		}),
			frm.set_query("cost_center", function () {
				return {
					filters: {
						"is_group": 0,
						company: frm.doc.company
					}
				}
			}),
			frm.set_query("project", function () {
				return {
					filters: {
						company: frm.doc.company
					}
				}
			})
	},

	refresh: function (frm) {
		frm.disable_save();
	},

	payroll_frequency: function (frm) {
		frm.trigger("set_start_end_dates");
	},

	start_date: function (frm) {
		frm.trigger("set_start_end_dates");
	},

	end_date: function (frm) {
//		console.log("catch", frm.doc.end_date);
//		frm.trigger("set_start_end_dates");
//		console.log("catch", frm.doc.end_date);
	},

	salary_slip_based_on_timesheet: function (frm) {
		frm.toggle_reqd(['payroll_frequency'], !frm.doc.salary_slip_based_on_timesheet);
	},

	payment_account: function (frm) {
		frm.toggle_display(['make_bank_entry'], (frm.doc.payment_account != "" && frm.doc.payment_account != "undefined"));
	},

	set_start_end_dates: function (frm) {
		if (!frm.doc.salary_slip_based_on_timesheet) {
			frappe.call({
				method: 'erpnext.hr.doctype.process_payroll.process_payroll.get_start_end_dates',
				args: {
					payroll_frequency: frm.doc.payroll_frequency,
					start_date: frm.doc.start_date || frm.doc.posting_date
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value('start_date', r.message.start_date);
						frm.set_value('end_date', r.message.end_date);
					}
				}
			})
		}
	},
})

cur_frm.cscript.display_activity_log = function (msg) {
	if (!cur_frm.ss_html)
		cur_frm.ss_html = $a(cur_frm.fields_dict['activity_log'].wrapper, 'div');
	if (msg) {
		cur_frm.ss_html.innerHTML =
			'<div class="padding"><h4>' + __("Activity Log:") + '</h4>' + msg + '</div>';
	} else {
		cur_frm.ss_html.innerHTML = "";
	}
}

// Create salary slip
// -----------------------
cur_frm.cscript.create_salary_slip = function (doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");
	var callback = function (r, rt) {
		if (r.message)
			cur_frm.cscript.display_activity_log(r.message);
	}
	return $c('runserverobj', { 'method': 'create_salary_slips', 'docs': doc }, callback);
}

cur_frm.cscript.submit_salary_slip = function (doc, cdt, cdn) {
	cur_frm.cscript.display_activity_log("");

	frappe.confirm(__("Do you really want to Submit all Salary Slip from {0} to {1}", [doc.start_date, doc.end_date]), function () {
		// clear all in locals
		if (locals["Salary Slip"]) {
			$.each(locals["Salary Slip"], function (name, d) {
				frappe.model.remove_from_locals("Salary Slip", name);
			});
		}

		var callback = function (r, rt) {
			if (r.message)
				cur_frm.cscript.display_activity_log(r.message);
		}

		return $c('runserverobj', { 'method': 'submit_salary_slips', 'docs': doc }, callback);
	});
}

cur_frm.cscript.make_bank_entry = function (doc, cdt, cdn) {
	if (doc.company && doc.start_date && doc.end_date) {
		return frappe.call({
			doc: cur_frm.doc,
			method: "make_payment_entry",
			callback: function (r) {
				if (r.message)
					var doc = frappe.model.sync(r.message)[0];
				frappe.set_route("Form", doc.doctype, doc.name);
			}
		});
	} else {
		frappe.msgprint(__("Company, From Date and To Date is mandatory"));
	}
}