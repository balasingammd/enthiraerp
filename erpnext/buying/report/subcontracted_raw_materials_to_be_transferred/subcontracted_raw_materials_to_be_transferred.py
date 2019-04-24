# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import itertools

def execute(filters=None):
	data = []
	columns = get_columns()
	get_data(data , filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Purchase Order"),
			"fieldtype": "Link",
			"fieldname": "purchase_order",
			"options": "Purchase Order",
			"width": 150
		},
		{
			"label": _("Date"),
			"fieldtype": "date",
			"fieldname": "date",
			"hidden": 1,
			"width": 150
		},
		{
			"label": _("Supplier"),
			"fieldtype": "Link",
			"fieldname": "supplier",
			"options": "Supplier",
			"width": 150
		},
		{
			"label": _("Item Code"),
			"fieldtype": "data",
			"fieldname": "rm_item_code",
			"width": 100
		},
		{
			"label": _("Required Quantity"),
			"fieldtype": "float",
			"fieldname": "r_qty",
			"width": 100
		},
		{
			"label": _("Transferred Quantity"),
			"fieldtype": "float",
			"fieldname": "t_qty",
			"width": 100
		},
		{
			"label": _("Pending Quantity"),
			"fieldtype": "float",
			"fieldname": "p_qty",
			"width": 100
		}
	]

def get_data(data, filters):
	po = get_po(filters)
	po_name = list(map(lambda x: {k:v for k, v in x.items() if k == 'name'}, po ))
	sub_items = get_purchase_order_item_supplied(po_name)

	from pprint import pprint

	for item in sub_items:
		for order in po:
			print(order)
			if order.name == item.parent:
				row ={
					'purchase_order': item.parent,
					'date': order.transaction_date,
					'supplier': order.supplier,
					'rm_item_code': item.rm_item_code,
					'r_qty': item.required_qty,
					't_qty':item.transfered_qty,
					'p_qty':item.required_qty - item.transfered_qty
				}
				data.append(row)

def get_po(filters):
	return frappe.get_all("Purchase Order", filters={"is_subcontracted": "Yes", "supplier": filters.supplier }, fields=["name", "transaction_date", "supplier"])

def get_purchase_order_item_supplied(po):
	po = ', '.join(map(str, [l['name'] for l in po if 'name' in l]))
	return frappe.get_all("Purchase Order Item Supplied", filters=[
			('parent', 'IN', po)
	], fields=["parent", "main_item_code", "rm_item_code", "required_qty", "transfered_qty", "required_qty"])