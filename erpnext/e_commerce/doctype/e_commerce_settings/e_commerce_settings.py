<<<<<<< HEAD:erpnext/portal/doctype/products_settings/products_settings.py
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
=======
# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
>>>>>>> 939b0dd67d (feat: E-commerce Refactor):erpnext/e_commerce/doctype/e_commerce_settings/e_commerce_settings.py
# For license information, please see license.txt

<<<<<<< HEAD

=======
>>>>>>> eef9cf152f (chore: Drive E-commerce via Website Item)
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint
from frappe.utils import get_datetime, get_datetime_str, now_datetime

class ShoppingCartSetupError(frappe.ValidationError): pass

class ECommerceSettings(Document):
	def onload(self):
		self.get("__onload").quotation_series = frappe.get_meta("Quotation").get_options("naming_series")

	def validate(self):
		if self.home_page_is_products:
			frappe.db.set_value("Website Settings", None, "home_page", "products")
		elif frappe.db.get_single_value("Website Settings", "home_page") == 'products':
			frappe.db.set_value("Website Settings", None, "home_page", "home")

		self.validate_field_filters()
		self.validate_attribute_filters()
		if self.enabled:
			self.validate_exchange_rates_exist()

		frappe.clear_document_cache("E Commerce Settings", "E Commerce Settings")

	def validate_field_filters(self):
		if not (self.enable_field_filters and self.filter_fields): return

		item_meta = frappe.get_meta("Item")
		valid_fields = [df.fieldname for df in item_meta.fields if df.fieldtype in ["Link", "Table MultiSelect"]]

		for f in self.filter_fields:
			if f.fieldname not in valid_fields:
				frappe.throw(_("Filter Fields Row #{0}: Fieldname <b>{1}</b> must be of type 'Link' or 'Table MultiSelect'").format(f.idx, f.fieldname))

	def validate_attribute_filters(self):
		if not (self.enable_attribute_filters and self.filter_attributes): return

		# if attribute filters are enabled, hide_variants should be disabled
		self.hide_variants = 0

	def validate_exchange_rates_exist(self):
		"""check if exchange rates exist for all Price List currencies (to company's currency)"""
		company_currency = frappe.get_cached_value('Company',  self.company,  "default_currency")
		if not company_currency:
			msgprint(_("Please specify currency in Company") + ": " + self.company,
				raise_exception=ShoppingCartSetupError)

		price_list_currency_map = frappe.db.get_values("Price List",
			[self.price_list], "currency")

		price_list_currency_map = dict(price_list_currency_map)

		# check if all price lists have a currency
		for price_list, currency in price_list_currency_map.items():
			if not currency:
				frappe.throw(_("Currency is required for Price List {0}").format(price_list))

		expected_to_exist = [currency + "-" + company_currency
			for currency in price_list_currency_map.values()
			if currency != company_currency]

		# manqala 20/09/2016: set up selection parameters for query from tabCurrency Exchange
		from_currency = [currency for currency in price_list_currency_map.values() if currency != company_currency]
		to_currency = company_currency
		# manqala end

		if expected_to_exist:
			# manqala 20/09/2016: modify query so that it uses date in the selection from Currency Exchange.
			# exchange rates defined with date less than the date on which this document is being saved will be selected
			exists = frappe.db.sql_list("""select CONCAT(from_currency,'-',to_currency) from `tabCurrency Exchange`
				where from_currency in (%s) and to_currency = "%s" and date <= curdate()""" % (", ".join(["%s"]*len(from_currency)), to_currency), tuple(from_currency))
			# manqala end

			missing = list(set(expected_to_exist).difference(exists))

			if missing:
				msgprint(_("Missing Currency Exchange Rates for {0}").format(comma_and(missing)),
					raise_exception=ShoppingCartSetupError)

	def validate_tax_rule(self):
		if not frappe.db.get_value("Tax Rule", {"use_for_shopping_cart" : 1}, "name"):
			frappe.throw(frappe._("Set Tax Rule for shopping cart"), ShoppingCartSetupError)

	def get_tax_master(self, billing_territory):
		tax_master = self.get_name_from_territory(billing_territory, "sales_taxes_and_charges_masters",
			"sales_taxes_and_charges_master")
		return tax_master and tax_master[0] or None

	def get_shipping_rules(self, shipping_territory):
		return self.get_name_from_territory(shipping_territory, "shipping_rules", "shipping_rule")

def validate_cart_settings(doc, method):
	frappe.get_doc("E Commerce Settings", "E Commerce Settings").run_method("validate")

def get_shopping_cart_settings():
	if not getattr(frappe.local, "shopping_cart_settings", None):
		frappe.local.shopping_cart_settings = frappe.get_doc("E Commerce Settings", "E Commerce Settings")

	return frappe.local.shopping_cart_settings

@frappe.whitelist(allow_guest=True)
def is_cart_enabled():
	return get_shopping_cart_settings().enabled

def show_quantity_in_website():
	return get_shopping_cart_settings().show_quantity_in_website

def check_shopping_cart_enabled():
	if not get_shopping_cart_settings().enabled:
		frappe.throw(_("You need to enable Shopping Cart"), ShoppingCartSetupError)

def show_attachments():
	return get_shopping_cart_settings().show_attachments

def home_page_is_products(doc, method):
	"""Called on saving Website Settings."""
	home_page_is_products = cint(frappe.db.get_single_value("E Commerce Settings", "home_page_is_products"))
	if home_page_is_products:
		doc.home_page = "products"