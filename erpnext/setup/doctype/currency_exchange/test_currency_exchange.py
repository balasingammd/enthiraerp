# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals


import frappe, unittest
test_records = frappe.get_test_records('Currency Exchange')


def save_new_records(test_records):
	for record in test_records:
		kwargs = dict(
			doctype=record.get("doctype"),
			docname=record.get("date") + '-' + record.get("from_currency") + '-' + record.get("to_currency"),
			fieldname="exchange_rate",
			value=record.get("exchange_rate"),
		)

		try:
			frappe.set_value(**kwargs)
		except frappe.DoesNotExistError:
			curr_exchange = frappe.new_doc(record.get("doctype"))
			curr_exchange.date = record["date"]
			curr_exchange.from_currency = record["from_currency"]
			curr_exchange.to_currency = record["to_currency"]
			curr_exchange.exchange_rate = record["exchange_rate"]
			curr_exchange.insert()


class TestCurrencyExchange(unittest.TestCase):
	def test_exchnage_rate(self):
		from erpnext.setup.utils import get_exchange_rate

		save_new_records(test_records)

		currency_settings = frappe.get_doc("Currency Exchange Settings", "Currency Exchange Settings")
		checkpoint = currency_settings.allow_stale

		# Start with allow_stale is True
		currency_settings.allow_stale = 1
		currency_settings.save()

		exchange_rate = get_exchange_rate("USD", "INR", "2016-01-01")
		self.assertEqual(exchange_rate, 60.0)

		exchange_rate = get_exchange_rate("USD", "INR", "2016-01-15")
		self.assertEqual(exchange_rate, 65.1)

		exchange_rate = get_exchange_rate("USD", "INR", "2016-01-30")
		self.assertEqual(exchange_rate, 62.9)
		
		# Exchange rate as on 15th Dec, 2015, should be fetched from fixer.io
		exchange_rate = get_exchange_rate("USD", "INR", "2015-12-15")
		self.assertFalse(exchange_rate==60)

		# strict currency settings
		currency_settings.allow_stale = 0
		currency_settings.stale_days = 1
		currency_settings.save()

		exchange_rate = get_exchange_rate("USD", "INR", "2016-01-01")
		self.assertEqual(exchange_rate, 60.0)

		exchange_rate = get_exchange_rate("USD", "INR", "2016-01-15")
		self.assertEqual(exchange_rate, 0)

		exchange_rate = get_exchange_rate("USD", "INR", "2016-01-30")
		self.assertEqual(exchange_rate, 62.9)

		# Exchange rate as on 15th Dec, 2015, should be fetched from fixer.io
		exchange_rate = get_exchange_rate("USD", "INR", "2015-12-15")
		self.assertFalse(exchange_rate == 60)

		# Reset Currency Exchange Settings
		currency_settings.allow_stale = 1
		currency_settings.save()
