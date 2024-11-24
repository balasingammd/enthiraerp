# This file provides an example of how to parse an XML document as the most common edi format
# You might not have an xml document and thus may not find this template useful
import frappe
from frappe import _
from lxml import etree, objectify

from erpnext.edi.doctype.edi_template.edi_template import EDITemplate

__all__ = ["get_parsed"]


def get_parsed(self: EDITemplate, render: str) -> None:
	src = _process(self, render)
	doc = frappe.new_doc(self.bound_doctype)

	# adapt to your actual schema
	doc.name = src.foo
	...

	return doc


def _process(self: EDITemplate, data: str) -> object:
	schema = None
	if self.schema:
		schema = etree.XMLSchema(self.schema)
	parser = objectify.makeparser(schema=schema)
	try:
		obj = objectify.fromstring(data, parser)
	except etree.XMLSytaxError:
		frappe.throw(_("Invalid Schema"))
	return obj
