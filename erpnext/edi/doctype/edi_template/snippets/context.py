from types import MethodType

import frappe
from frappe import _
from frappe.model import Document

from erpnext.edi.doctype.edi_template.edi_template import EDITemplate

__all__ = ["get_context"]


def _throw(msg):
	frappe.throw(msg, title=_("Incorrect Context Information"))


def get_context(self: EDITemplate, doc: "Document", method: str) -> None:
	self.get_document_proxy_class = MethodType(_get_document_proxy_class, self)
	return {"doc": doc}


def _get_document_proxy_class(template):
	class CustomDocumentProxy(template._get_default_document_proxy_class()):
		def __init__(self, *args, **kwargs):
			super().__init__(*args, **kwargs)
			if self.doctype in ("Customer", "Supplier", "Company"):
				# add additional (eager) attributes
				...

		def __getattr__(self, attr):
			match (self.doctype, attr):
				# add additonal (lazy) attributes
				case ("Address", "foo"):
					return "BAR"
			value = super().__getattr__(attr)
			match (self.doctype, attr):
				# lazy validate values
				case ("Customer", "qux"):
					if not value:
						_throw(_("Customer '{}' has no qux set").format(self.name))
			return value

		...

	return CustomDocumentProxy
