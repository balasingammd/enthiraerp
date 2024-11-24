# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
import frappe.share
from frappe import _
from frappe.utils import cint, flt, get_time, now_datetime

from erpnext.controllers.status_updater import StatusUpdater
from erpnext.stock.get_item_details import get_item_details
from erpnext.stock.utils import get_incoming_rate


class UOMMustBeIntegerError(frappe.ValidationError):
	pass


class TransactionBase(StatusUpdater):
	def validate_posting_time(self):
		# set Edit Posting Date and Time to 1 while data import
		if frappe.flags.in_import and self.posting_date:
			self.set_posting_time = 1

		if not getattr(self, "set_posting_time", None):
			now = now_datetime()
			self.posting_date = now.strftime("%Y-%m-%d")
			self.posting_time = now.strftime("%H:%M:%S.%f")
		elif self.posting_time:
			try:
				get_time(self.posting_time)
			except ValueError:
				frappe.throw(_("Invalid Posting Time"))

	def validate_uom_is_integer(self, uom_field, qty_fields, child_dt=None):
		validate_uom_is_integer(self, uom_field, qty_fields, child_dt)

	def validate_with_previous_doc(self, ref):
		self.exclude_fields = ["conversion_factor", "uom"] if self.get("is_return") else []

		for key, val in ref.items():
			is_child = val.get("is_child_table")
			ref_doc = {}
			item_ref_dn = []
			for d in self.get_all_children(self.doctype + " Item"):
				ref_dn = d.get(val["ref_dn_field"])
				if ref_dn:
					if is_child:
						self.compare_values({key: [ref_dn]}, val["compare_fields"], d)
						if ref_dn not in item_ref_dn:
							item_ref_dn.append(ref_dn)
						elif not val.get("allow_duplicate_prev_row_id"):
							frappe.throw(_("Duplicate row {0} with same {1}").format(d.idx, key))
					elif ref_dn:
						ref_doc.setdefault(key, [])
						if ref_dn not in ref_doc[key]:
							ref_doc[key].append(ref_dn)
			if ref_doc:
				self.compare_values(ref_doc, val["compare_fields"])

	def compare_values(self, ref_doc, fields, doc=None):
		for reference_doctype, ref_dn_list in ref_doc.items():
			prev_doc_detail_map = self.get_prev_doc_reference_details(ref_dn_list, reference_doctype, fields)
			for reference_name in ref_dn_list:
				prevdoc_values = prev_doc_detail_map.get(reference_name)
				if not prevdoc_values:
					frappe.throw(_("Invalid reference {0} {1}").format(reference_doctype, reference_name))

				for field, condition in fields:
					if prevdoc_values[field] is not None and field not in self.exclude_fields:
						self.validate_value(field, condition, prevdoc_values[field], doc)

	def get_prev_doc_reference_details(self, reference_names, reference_doctype, fields):
		prev_doc_detail_map = {}
		details = frappe.get_all(
			reference_doctype,
			filters={"name": ("in", reference_names)},
			fields=["name"] + [d[0] for d in fields],
		)

		for d in details:
			prev_doc_detail_map.setdefault(d.name, d)

		return prev_doc_detail_map

	def validate_rate_with_reference_doc(self, ref_details):
		if self.get("is_internal_supplier"):
			return

		buying_doctypes = ["Purchase Order", "Purchase Invoice", "Purchase Receipt"]

		if self.doctype in buying_doctypes:
			action, role_allowed_to_override = frappe.get_cached_value(
				"Buying Settings", "None", ["maintain_same_rate_action", "role_to_override_stop_action"]
			)
		else:
			action, role_allowed_to_override = frappe.get_cached_value(
				"Selling Settings", "None", ["maintain_same_rate_action", "role_to_override_stop_action"]
			)

		stop_actions = []
		for ref_dt, ref_dn_field, ref_link_field in ref_details:
			reference_names = [d.get(ref_link_field) for d in self.get("items") if d.get(ref_link_field)]
			reference_details = self.get_reference_details(reference_names, ref_dt + " Item")
			for d in self.get("items"):
				if d.get(ref_link_field):
					ref_rate = reference_details.get(d.get(ref_link_field))

					if abs(flt(d.rate - ref_rate, d.precision("rate"))) >= 0.01:
						if action == "Stop":
							if role_allowed_to_override not in frappe.get_roles():
								stop_actions.append(
									_("Row #{0}: Rate must be same as {1}: {2} ({3} / {4})").format(
										d.idx, ref_dt, d.get(ref_dn_field), d.rate, ref_rate
									)
								)
						else:
							frappe.msgprint(
								_("Row #{0}: Rate must be same as {1}: {2} ({3} / {4})").format(
									d.idx, ref_dt, d.get(ref_dn_field), d.rate, ref_rate
								),
								title=_("Warning"),
								indicator="orange",
							)
		if stop_actions:
			frappe.throw(stop_actions, as_list=True)

	def get_reference_details(self, reference_names, reference_doctype):
		return frappe._dict(
			frappe.get_all(
				reference_doctype,
				filters={"name": ("in", reference_names)},
				fields=["name", "rate"],
				as_list=1,
			)
		)

	def get_link_filters(self, for_doctype):
		if hasattr(self, "prev_link_mapper") and self.prev_link_mapper.get(for_doctype):
			fieldname = self.prev_link_mapper[for_doctype]["fieldname"]

			values = filter(None, tuple(item.as_dict()[fieldname] for item in self.items))

			if values:
				ret = {for_doctype: {"filters": [[for_doctype, "name", "in", values]]}}
			else:
				ret = None
		else:
			ret = None

		return ret

	def reset_default_field_value(self, default_field: str, child_table: str, child_table_field: str):
		"""Reset "Set default X" fields on forms to avoid confusion.

		example:
		        doc = {
		                "set_from_warehouse": "Warehouse A",
		                "items": [{"from_warehouse": "warehouse B"}, {"from_warehouse": "warehouse A"}],
		        }
		        Since this has dissimilar values in child table, the default field will be erased.

		        doc.reset_default_field_value("set_from_warehouse", "items", "from_warehouse")
		"""
		child_table_values = set()

		for row in self.get(child_table):
			child_table_values.add(row.get(child_table_field))

		if len(child_table_values) > 1:
			self.set(default_field, None)

	def validate_currency_for_receivable_payable_and_advance_account(self):
		if self.doctype in ["Customer", "Supplier"]:
			account_type = "Receivable" if self.doctype == "Customer" else "Payable"
			for x in self.accounts:
				company_default_currency = frappe.get_cached_value("Company", x.company, "default_currency")
				receivable_payable_account_currency = None
				advance_account_currency = None

				if x.account:
					receivable_payable_account_currency = frappe.get_cached_value(
						"Account", x.account, "account_currency"
					)

				if x.advance_account:
					advance_account_currency = frappe.get_cached_value(
						"Account", x.advance_account, "account_currency"
					)
				if receivable_payable_account_currency and (
					receivable_payable_account_currency != self.default_currency
					and receivable_payable_account_currency != company_default_currency
				):
					frappe.throw(
						_(
							"{0} Account: {1} ({2}) must be in either customer billing currency: {3} or Company default currency: {4}"
						).format(
							account_type,
							frappe.bold(x.account),
							frappe.bold(receivable_payable_account_currency),
							frappe.bold(self.default_currency),
							frappe.bold(company_default_currency),
						)
					)

				if advance_account_currency and (
					advance_account_currency != self.default_currency
					and advance_account_currency != company_default_currency
				):
					frappe.throw(
						_(
							"Advance Account: {0} must be in either customer billing currency: {1} or Company default currency: {2}"
						).format(
							frappe.bold(x.advance_account),
							frappe.bold(self.default_currency),
							frappe.bold(company_default_currency),
						)
					)

				if (
					receivable_payable_account_currency
					and advance_account_currency
					and receivable_payable_account_currency != advance_account_currency
				):
					frappe.throw(
						_(
							"Both {0} Account: {1} and Advance Account: {2} must be of same currency for company: {3}"
						).format(
							account_type,
							frappe.bold(x.account),
							frappe.bold(x.advance_account),
							frappe.bold(x.company),
						)
					)

	@frappe.whitelist()
	def item_code_trigger(self, item):
		# 'item' - child table row from UI. Possibly has user-set values
		# Convert it to Frappe doc for better attribute access
		item = frappe.get_doc(item)

		# Server side 'item' doc. Update this to reflect in UI
		item_obj = self.get("items", {"name": item.name})[0]

		# 'item_details' has values fetched by system for backend
		item_details = get_item_details(
			frappe._dict(
				{
					"item_code": item.get("item_code"),
					"barcode": item.get("barcode"),
					"serial_no": item.get("serial_no"),
					"batch_no": item.get("batch_no"),
					"set_warehouse": self.get("set_warehouse"),
					"warehouse": item.get("warehouse"),
					"customer": self.get("customer") or self.get("party_name"),
					"quotation_to": self.get("quotation_to"),
					"supplier": self.get("supplier"),
					"currency": self.get("currency"),
					"is_internal_supplier": self.get("is_internal_supplier"),
					"is_internal_customer": self.get("is_internal_customer"),
					"update_stock": self.update_stock
					if self.doctype in ["Purchase Invoice", "Sales Invoice"]
					else False,
					"conversion_rate": self.get("conversion_rate"),
					"price_list": self.get("selling_price_list") or self.get("buying_price_list"),
					"price_list_currency": self.get("price_list_currency"),
					"plc_conversion_rate": self.get("plc_conversion_rate"),
					"company": self.get("company"),
					"order_type": self.get("order_type"),
					"is_pos": cint(self.get("is_pos")),
					"is_return": cint(self.get("is_return)")),
					"is_subcontracted": self.get("is_subcontracted"),
					"ignore_pricing_rule": self.get("ignore_pricing_rule"),
					"doctype": self.get("doctype"),
					"name": self.get("name"),
					"project": item.get("project") or self.get("project"),
					"qty": item.get("qty") or 1,
					"net_rate": item.get("rate"),
					"base_net_rate": item.get("base_net_rate"),
					"stock_qty": item.get("stock_qty"),
					"conversion_factor": item.get("conversion_factor"),
					"weight_per_unit": item.get("weight_per_unit"),
					"uom": item.get("uom"),
					"weight_uom": item.get("weight_uom"),
					"manufacturer": item.get("manufacturer"),
					"stock_uom": item.get("stock_uom"),
					"pos_profile": self.get("pos_profile") if cint(self.get("is_pos")) else "",
					"cost_center": item.get("cost_center"),
					"tax_category": self.get("tax_category"),
					"item_tax_template": item.get("item_tax_template"),
					"child_doctype": item.get("doctype"),
					"child_docname": item.get("name"),
					"is_old_subcontracting_flow": self.get("is_old_subcontracting_flow"),
				}
			)
		)

		self.set_fetched_values(item_obj, item_details)
		self.set_item_rate_and_discounts(item, item_obj, item_details)

		self.add_taxes_from_item_template(item, item_obj, item_details)
		self.add_free_item(item, item_obj, item_details)
		return

		# self.handle_internal_parties(item, item_details)
		# if self.get("is_internal_customer") or self.get("is_internal_supplier"):
		# TODO: this is already called in handle_internal_parties() -> price_list_rate, Remove?
		# 	self.calculate_taxes_and_totals()

	def set_fetched_values(self, item_obj: object, item_details: dict) -> None:
		for k, v in item_details.items():
			if hasattr(item_obj, k):
				setattr(item_obj, k, v)

	def handle_internal_parties(self, item, item_details):
		if (
			self.get("is_internal_customer") or self.get("is_internal_supplier")
		) and self.represents_company == self.company:
			args = frappe._dict(
				{
					"item_code": item.item_code,
					"warehouse": item.from_warehouse
					if self.doctype in ["Purchase Receipt", "Purchase Invoice"]
					else item.warehouse,
					"posting_date": self.posting_date,
					"posting_time": self.posting_time,
					"qty": item.qty * item.conversion_factor,
					"serial_no": item.serial_no,
					"batch_no": item.batch_no,
					"voucher_type": self.doctype,
					"company": self.company,
					"allow_zero_valuation_rate": item.allow_zero_valuation_rate,
				}
			)
			rate = get_incoming_rate(args=args)
			item.rate = rate * item.conversion_factor
		else:
			self.price_list_rate(item, item_details)

	def add_taxes_from_item_template(self, item: object, item_obj: object, item_details: dict) -> None:
		if item_details.item_tax_rate and frappe.db.get_single_value(
			"Accounts Settings", "add_taxes_from_item_tax_template"
		):
			item_tax_template = frappe.json.loads(item_details.item_tax_rate)
			for tax_head, rate in item_tax_template.items():
				found = [x for x in self.taxes if x.account_head == tax_head]
				if not found:
					self.append("taxes", {"charge_type": "On Net Total", "account_head": tax_head, "rate": 0})

	def price_list_rate(self, item, item_details):
		if item.doctype in [
			"Quotation Item",
			"Sales Order Item",
			"Delivery Note Item",
			"Sales Invoice Item",
			"POS Invoice Item",
			"Purchase Invoice Item",
			"Purchase Order Item",
			"Purchase Receipt Item",
		]:
			# self.apply_pricing_rule_on_item(item, item_details)
			self.apply_pricing_rule_on_item(item)
		else:
			item.rate = flt(
				item.price_list_rate * (1 - item.discount_percentage / 100.0), item.precision("rate")
			)
			self.calculate_taxes_and_totals()

	def copy_from_first_row(self, row, fields):
		if self.items and row:
			# TODO: find a alternate mechanism for setting dimensions
			fields.append("cost_center")
			first_row = self.items[0]
			[setattr(row, k, first_row.get(k)) for k in fields if hasattr(first_row, k)]

	def add_free_item(self, item: object, item_obj: object, item_details: dict) -> None:
		free_items = item_details.get("free_item_data")
		if free_items and len(free_items):
			existing_free_items = [x for x in self.items if x.is_free_item]
			existing_items = [
				{"item_code": x.item_code, "pricing_rules": x.pricing_rules} for x in self.items
			]

			for free_item in free_items:
				_matches = [
					x
					for x in existing_free_items
					if x.item_code == free_item.get('item_code') and x.pricing_rules == free_item.get('pricing_rules')
				]
				if _matches:
					row_to_modify = _matches[0]
				else:
					row_to_modify = self.append("items")

				for k, v in free_item.items():
					setattr(row_to_modify, k, free_item.get(k))

				self.copy_from_first_row(row_to_modify, ["expense_account", "income_account"])

	def conversion_factor(self):
		if frappe.get_meta(item.doctype).has_field("stock_qty"):
			# frappe.model.round_floats_in(item, ["qty", "conversion_factor"]);
			item.stock_qty = flt(item.qty * item.conversion_factor, item.precision("stock_qty"))

			# this.toggle_conversion_factor(item);
			if self.doctype != "Material Request":
				item.total_weight = flt(item.stock_qty * item.weight_per_unit)
				self.calculate_net_weight()

			# TODO: for handling customization not to fetch price list rate
			if frappe.flags.dont_fetch_price_list_rate:
				return

			if not dont_fetch_price_list_rate and frappe.meta.has_field(doc.doctype, "price_list_currency"):
				self.apply_price_list(item, true)
			self.calculate_stock_uom_rate(doc, cdt, cdn)

	def set_item_rate_and_discounts(self, item: object, item_obj: object, item_details: dict) -> None:
		effective_item_rate = item_details.price_list_rate
		item_rate = item_details.rate

		# Field order precedance
		# blanket_order_rate -> margin_type -> discount_percentage -> discount_amount
		if item.parenttype in ["Sales Order", "Quotation"] and item.blanket_order_rate:
			effective_item_rate = item.blanket_order_rate

		if item.margin_type == "Percentage":
			item_obj.rate_with_margin = flt(effective_item_rate) + flt(effective_item_rate) * (
				flt(item.margin_rate_or_amount) / 100
			)
		else:
			item_obj.rate_with_margin = flt(effective_item_rate) + flt(item.margin_rate_or_amount)

		item_obj.base_rate_with_margin = flt(item_obj.rate_with_margin) * flt(self.conversion_rate)
		item_rate = flt(item_obj.rate_with_margin, item_obj.precision("rate"))

		if item.discount_percentage and not item.discount_amount:
			item_obj.discount_amount = flt(item_obj.rate_with_margin) * flt(item.discount_percentage) / 100

		if item.discount_amount and item.discount_amount > 0:
			item_rate = flt((item_obj.rate_with_margin) - (item_obj.discount_amount), item.precision("rate"))
			item_obj.discount_percentage = (
				100 * flt(item_obj.discount_amount) / flt(item_obj.rate_with_margin)
			)

		item_obj.rate = item_rate

	def calculate_net_weight(self):
		self.total_net_weight = sum([x.total_weight for x in self.items])
		self.apply_shipping_rule()

	def apply_price_list(self, item, reset_plc_conversion):
		# We need to reset plc_conversion_rate sometimes because the call to
		# `erpnext.stock.get_item_details.apply_price_list` is sensitive to its value

		if self.doctype == "Material Request":
			return

		if not reset_plc_conversion:
			self.plc_conversion_rate = ""

		if not (item.items or item.price_list):
			return

		if self.in_apply_price_list:
			return

		self.in_apply_price_list = True
		# return this.frm.call({
		# 	method: "erpnext.stock.get_item_details.apply_price_list",
		# 	args: {	args: args, doc: me.frm.doc },
		# 	callback: function(r) {
		# 		if (!r.exc) {
		# 			frappe.run_serially([
		# 				() => me.frm.set_value("price_list_currency", r.message.parent.price_list_currency),
		# 				() => me.frm.set_value("plc_conversion_rate", r.message.parent.plc_conversion_rate),
		# 				() => {
		# 					if(args.items.length) {
		# 						me._set_values_for_item_list(r.message.children);
		# 						$.each(r.message.children || [], function(i, d) {
		# 							me.apply_discount_on_item(d, d.doctype, d.name, 'discount_percentage');
		# 						});
		# 					}
		# 				},
		# 				() => { me.in_apply_price_list = false; }
		# 			]);

		# 		} else {
		# 			me.in_apply_price_list = false;
		# 		}
		# 	}
		# }).always(() => {
		# 	me.in_apply_price_list = false;
		# });


def delete_events(ref_type, ref_name):
	events = (
		frappe.db.sql_list(
			""" SELECT
			distinct `tabEvent`.name
		from
			`tabEvent`, `tabEvent Participants`
		where
			`tabEvent`.name = `tabEvent Participants`.parent
			and `tabEvent Participants`.reference_doctype = %s
			and `tabEvent Participants`.reference_docname = %s
		""",
			(ref_type, ref_name),
		)
		or []
	)

	if events:
		frappe.delete_doc("Event", events, for_reload=True)


def validate_uom_is_integer(doc, uom_field, qty_fields, child_dt=None):
	if isinstance(qty_fields, str):
		qty_fields = [qty_fields]

	distinct_uoms = list(set(d.get(uom_field) for d in doc.get_all_children()))
	integer_uoms = list(
		filter(
			lambda uom: frappe.db.get_value("UOM", uom, "must_be_whole_number", cache=True) or None,
			distinct_uoms,
		)
	)

	if not integer_uoms:
		return

	for d in doc.get_all_children(parenttype=child_dt):
		if d.get(uom_field) in integer_uoms:
			for f in qty_fields:
				qty = d.get(f)
				if qty:
					precision = d.precision(f)
					if abs(cint(qty) - flt(qty, precision)) > 0.0000001:
						frappe.throw(
							_(
								"Row {1}: Quantity ({0}) cannot be a fraction. To allow this, disable '{2}' in UOM {3}."
							).format(
								flt(qty, precision),
								d.idx,
								frappe.bold(_("Must be Whole Number")),
								frappe.bold(d.get(uom_field)),
							),
							UOMMustBeIntegerError,
						)
