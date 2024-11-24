import frappe
from frappe.model.document import Document

from erpnext.edi.doctype.edi_template.edi_template import EDITemplate

__all__ = ["attach"]


def attach(self: EDITemplate, data: str, doc: Document) -> str:
	filename = frappe.scrub(doc.name) + ".xml"
	# Attach the file
	file = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"attached_to_doctype": doc.doctype,
			"attached_to_name": doc.name,
			"is_private": True,
			"content": data,
		}
	)
	file.save()
