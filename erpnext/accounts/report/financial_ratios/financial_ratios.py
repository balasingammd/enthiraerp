# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.financial_statements import get_data, get_period_list


def execute(filters=None):
	filters["filter_based_on"] = "Fiscal Year"

	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)

	columns, data = [], []
	columns = get_columns(filters)
	data = get_query_data(filters)
	assets = get_data(
		filters.company,
		"Asset",
		"Debit",
		period_list,
		only_current_fiscal_year=False,
		filters=filters,
		accumulated_values=filters.accumulated_values,
	)

	liabilities = get_data(
		filters.company,
		"Liability",
		"Credit",
		period_list,
		only_current_fiscal_year=False,
		filters=filters,
		accumulated_values=filters.accumulated_values,
	)

	current_asset = (
		list(filter(lambda asset: asset.get("account_type") == "Current Asset", assets))[0]["total"]
		or []
	)
	current_liability = (
		list(filter(lambda asset: asset.get("account_type") == "Current Liability", liabilities))[0][
			"total"
		]
		or []
	)
	current_ratio = flt(flt(current_asset) / flt(current_liability), precision=3)

	# Calculating Quick Assets
	quick_asset = 0
	for asset in assets:
		if asset.get("account_type") in ["Bank", "Cash", "Receivable"] and not asset.get("is_group"):
			quick_asset += asset.get("total")

	quick_ratio = flt(quick_asset / current_liability, precision=3)

	total_liablity = 0
	for liability in liabilities:
		if liability.get("total") and not liability.get("parent_account"):
			total_liablity = liability["total"]

	# if liabilities.get('root_type') == 'Liability':
	print(total_liablity)

	data = [
		{"ratio": "Current Ratio", "ratio_value": current_ratio},
		{"ratio": "Quick Ratio", "ratio_value": quick_ratio},
	]

	return columns, data


def get_columns(filters):

	return [
		{
			"label": _("Ratios"),
			"fieldname": "ratio",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("2023-2024"),
			"fieldname": "ratio_value",
			"fieldtype": "Data",
			"width": 200,
		},
	]


def get_query_data(filters):
	pass
