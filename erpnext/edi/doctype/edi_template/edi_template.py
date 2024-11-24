# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import os
from collections import defaultdict
from typing import ClassVar

import frappe
from frappe import _
from frappe.model.document import Document, DocumentProxy
from frappe.modules.utils import export_module_json, get_doc_module
from frappe.utils.jinja import ProcessedContext, process_context
from lxml import etree, objectify

from erpnext.edi.doctype.edi_log.edi_log import EDILog


def use_module_if_standard(func):
	def wrapper(self, *args, **kwargs):
		if self.is_standard:
			app = frappe.local.module_app[frappe.scrub(self.module)]
			doctype = frappe.scrub(self.doctype)
			module = frappe.scrub(self.module)
			name = frappe.scrub(self.name)
			module_name = f"{app}.{module}.{doctype}.{name}"
			module = frappe.get_module(module_name)
			if hasattr(module, func.__name__):
				module_func = getattr(module, func.__name__)
			return module_func(self, *args, **kwargs)
		return func(self, *args, **kwargs)

	return wrapper


class EDITemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from erpnext.edi.doctype.bound_edi_template_common_codes.bound_edi_template_common_codes import (
			BoundEDITemplateCommonCodes,
		)

		api_endpoint: DF.Link | None
		bound_common_codes: DF.Table[BoundEDITemplateCommonCodes]
		bound_doctype: DF.Link
		condition: DF.Code | None
		is_standard: DF.Check
		module: DF.Link | None
		schema: DF.Code | None
		status: DF.Literal["Draft", "Staging", "Production", "Obsolete"]
		submit_config: DF.Link | None
		template: DF.Code | None
		validation: DF.Code | None
	# end: auto-generated types

	@property
	def document_proxy_class(self):
		return self.get_document_proxy_class()

	def get_document_proxy_class(self):
		return self._get_default_document_proxy_class()

	def _get_default_document_proxy_class(template):
		class EDITemplateDocumentProxy(DocumentProxy):
			_bound_common_codes: ClassVar[dict[str, dict[str, list]]] = defaultdict(lambda: defaultdict(list))
			_initialized: ClassVar[bool] = False

			# Don't deviate from DocumentProxy's init signature - recursive instantiation (!)
			def __init__(self, *args, **kwargs):
				super().__init__(*args, **kwargs)
				self._init_bindings()

			@classmethod
			def _init_bindings(cls):
				if not cls._initialized:
					for bc in template.bound_common_codes:
						cls._bound_common_codes[bc.reference_doctype][bc.reference_name].append(bc)
					cls._initialized = True

			def __getattr_value__(self, attr):
				value = super().__getattr_value__(attr)
				if isinstance(value, type(self)):
					for bcc in self._bound_common_codes.get(value.doctype, {}).get(value.name, []):
						setattr(
							value,
							bcc.attribute_name,
							type(self)("Common Code", bcc.common_code),
						)
					return value
				if attr == "additional_data" and isinstance(value, str):
					# Parse XML stored in additional_data
					return objectify.fromstring(value)
				return value

		return EDITemplateDocumentProxy

	def evaluate_condition(self, doc, method):
		if not self.condition:
			return True
		try:
			context = {"doc": doc, "method": method}  # limited context for perforance reasons
			return frappe.safe_eval(self.condition, None, context)
		except Exception as e:
			self.log_error(f"Error evaluating condition: {e!s}")
		return False

	def get_processed_context(self, doc: Document, method: str) -> ProcessedContext:
		return process_context(self.get_context(doc, method), document_proxy_class=self.document_proxy_class)

	@use_module_if_standard
	def get_context(self, doc: Document, method: str) -> dict:
		return {"doc": doc, "method": method}

	@use_module_if_standard
	def get_validation(self, data: str) -> None:
		pass

	@use_module_if_standard
	def sign(self, data: str, doc: Document) -> str:
		return data

	@use_module_if_standard
	def attach(self, data: str, doc: Document) -> str:
		pass

	def get_render(self, doc: Document, method: str) -> str:
		context = self.get_processed_context(doc, method)
		render = frappe.render_template(self.template, context=context)
		try:
			signed = self.sign(render, doc)
		except Exception as e:
			logger = frappe.logger("edi-template")
			logger.warning("\n" + render)
			hint = _("Tip: analyze the render in <code>logs/edi-template.log</code>")
			raise frappe.Throw(
				title="EDI Signing Error",
				msg=f"<i>{hint}</i><hr/><b>{e.__class__.__name__}</b><br/>{e!s}",
			) from e
		try:
			self.get_validation(signed)
		except Exception as e:
			logger = frappe.logger("edi-template")
			logger.warning("\n" + render)
			hint = _("Tip: analyze the render in <code>logs/edi-template.log</code>")
			raise frappe.Throw(
				title="EDI Validation Error",
				msg=f"<i>{hint}</i><hr/><b>{e.__class__.__name__}</b><br/>{e!s}",
			) from e
		return signed

	@use_module_if_standard
	def get_parsed(self, data: str) -> Document | None:
		pass

	@use_module_if_standard
	def submit(self, data: str, doc: Document) -> None:
		pass

	def write_log(
		self,
		doc: Document,
		status: str,
		request_header: str,
		request: str,
		response_header: str,
		response: str,
	) -> EDILog:
		log = frappe.new_doc("EDI Log")
		log.edi = self.name
		log.reference_doctype = doc.doctype
		log.reference_docname = doc.docname
		log.status = status
		log.request_header = request_header
		log.response_header = response_header
		log.request = request
		log.response = response
		return log.save(ignore_permissions=True)

	# field content primes over file content
	def get_code_fields(self):
		return {"template": "xml", "validation": "check.xml", "schema": "schema.xml"}

	def on_update(self):
		path = export_module_json(self, self.is_standard, self.module)
		if not path:
			return
		path = os.path.dirname(path)
		snippets_dir = os.path.join(os.path.dirname(__file__), "snippets")
		if (init := os.path.join(path, "__init__.py")) and os.path.getsize(init) == 0:
			with open(init, "w") as f:
				f.write("# hooks used by this edi_template\n\n")
				for snippet_file in os.listdir(snippets_dir):
					if snippet_file.endswith(".py"):
						module_name = os.path.splitext(snippet_file)[0]
						f.write(f"from .{module_name} import *\n")

		for snippet_file in os.listdir(snippets_dir):
			if snippet_file.endswith(".py"):
				source_path = os.path.join(snippets_dir, snippet_file)
				dest_path = os.path.join(path, snippet_file)

			if not os.path.exists(dest_path):
				with open(source_path) as source, open(dest_path, "w") as dest:
					dest.write(source.read())


def _process(template, doc, method=None):
	render = template.get_render(doc, method)
	template.attach(render)
	# template.submit(render)


def process(doc, method=None):
	"""
	# hooks.py

	Example:
	        doc_events = {
	            "Your Bound DocType": {
	                "on_submit": "erpnext.edi.doctype.edi_template.edi_template.process"
	            }
	        }
	"""
	edi_templates = frappe.get_all(
		"EDI Template",
		filters={"bound_doctype": doc.doctype, "status": ["in", ["Staging", "Production"]]},
		pluck="name",
	)

	for name in edi_templates:
		template = frappe.get_doc("EDI Template", name)
		if template.evaluate_condition(doc, method):
			_process(template, doc, method)


@frappe.whitelist()
def manual_process(template: str, doc: str):
	"""Development utility; invoked from buttons in bound_doctype.js"""
	template = frappe.get_doc("EDI Template", template)
	doc = frappe.get_doc(template.bound_doctype, doc)
	_process(template, doc, "manual")
