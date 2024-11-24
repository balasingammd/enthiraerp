// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

function get_filters() {
	let filters = [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "period_start_date",
			label: __("Start Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "period_end_date",
			label: __("End Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "account",
			label: __("Account"),
			fieldtype: "MultiSelectList",
			options: "Account",
			get_data: function (txt) {
				return frappe.db.get_link_options("Account", txt, {
					company: frappe.query_report.get_filter_value("company"),
					account_type: ["in", ["Receivable", "Payable"]],
				});
			},
		},
		{
			fieldname: "voucher_no",
			label: __("Voucher No"),
			fieldtype: "Data",
			width: 100,
		},
	];
	return filters;
}

frappe.query_reports["General and Payment Ledger Comparison"] = {
	filters: get_filters(),

	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true,
		});
	},

	onload(report) {
		report.page.add_inner_button(__("Repost"), function () {
			let message = `Are you sure you want to Repost Payment Ledger Entry for the selected differences?`;
			let indexes = frappe.query_report.datatable.rowmanager.getCheckedRows();
			let selected_rows = indexes.map((i) => frappe.query_report.data[i]);

			if (!selected_rows.length) {
				frappe.throw(__("Please select rows to create repost entries"));
			}

			frappe.confirm(__(message), () => {
				frappe.call({
					method: "erpnext.accounts.report.general_and_payment_ledger_comparison.general_and_payment_ledger_comparison.create_repost_payment_ledger_entry",
					args: {
						rows: selected_rows,
						company: frappe.query_report.get_filter_values().company,
					},
				});
			});
		});
	},
};
