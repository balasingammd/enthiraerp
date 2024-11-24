# This file provides an example of how to validate an XML document as the most common edi format
# You might not have an xml document and thus may not find this template useful
import frappe
from frappe import _
from lxml import etree

from erpnext.edi.doctype.edi_template.edi_template import EDITemplate

__all__ = ["get_validation"]


def get_validation(self: EDITemplate, data: str) -> None:
	transform: etree.XSLT = _get_transformer(self)

	result: etree._XSLTResultTree = transform(etree.XML(data))
	if transform.error_log:
		msg = "<ol>"
		for entry in transform.error_log:
			msg += "<li>" + str(entry) + "</li>"
		msg += "</ol><hr/>"
		msg += result
		frappe.throw(msg, title=_("XML Validation Error"), wide=True)


class MyExtElement(etree.XSLTExtension):
	def execute(self, context, self_node, input_node, output_parent):
		...


def _get_transformer(self: EDITemplate):
	extensions = {
		...: ...,
		("textns", "ext"): MyExtElement(),
	}
	return etree.XSLT(self.validation, extensions=extensions)
