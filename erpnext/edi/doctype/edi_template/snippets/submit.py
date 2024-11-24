# This file provides an example of how to submit an XML document as the most common edi format
# You might not have an xml document and thus may not find this template useful

import frappe
import xmlsec
import zeep
from frappe.model.document import Document
from lxml import etree
from zeep import Client
from zeep.cache import Base
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport
from zeep.wsse import utils
from zeep.wsse.signature import BinarySignature

from erpnext.edi.doctype.edi_template.edi_template import EDITemplate

__all__ = ["submit"]

# you might eventually need to monkey patch some namespaces
# beware - this is not threadsafe and has sideffects for other usages of zeep
# zeep.ns.SP = "http://schemas.xmlsoap.org/ws/2005/07/securitypolicy"
# zeep.wsdl.wsdl.NSMAP["sp"] = zeep.ns.SP


class FrappeCache(Base):
	def __init__(self, timeout=3600):
		self._timeout = timeout

	def add(self, url, content):
		frappe.cache().set_value(key=f"edi|{url}", val=content, expires_in_sec=self._timeout)

	def get(self, url):
		if cached_data := frappe.cache().get_value(f"edi|{url}"):
			return cached_data
		return None


def submit(self: EDITemplate, data: str, doc: Document) -> None:
	key, cert = _get_credentials(self)

	history = HistoryPlugin()
	plugins = set(
		# declare your plugins
		...
	)

	client = Client(
		self.submit_url,
		transport=Transport(
			...,
			cache=FrappeCache(),
		),
		wsse=BinarySignature(
			key_file=key,
			certfile=cert,
			signature_method=xmlsec.Transform.RSA_SHA256,
			digest_method=xmlsec.Transform.SHA256,
		),
		plugins=(*plugins, history),
	)

	response = client.service.DoSomething(...)

	def is_ok(resp):
		...

	def needs_retry(resp):
		...

	def process(history):
		return {
			"request_header": history.last_sent["headers"],
			"request": etree.tostring(history.last_sent["envelope"], encoding="unicode", pretty_print=True),
			"response_header": history.last_received["headers"],
			"response": etree.tostring(
				history.last_received["envelope"], encoding="unicode", pretty_print=True
			),
		}

	if is_ok(response):
		self.write_log(doc, status="Success", **process(history))
		doc.db_set(...)
		...
	elif needs_retry(response):
		self.write_log(doc, status="Queued", **process(history))
		doc.db_set(...)
	else:
		log = self.write_log(doc, status="Error", **process(history))
		doc.log_error("EDI submittion failed", frappe.utils.get_url_to_form(log.doctype, log.docname))
		doc.db_set(...)
		...


KeyFilePath = str
CertFilePath = str


def _get_credentials(self: EDITemplate) -> (KeyFilePath, CertFilePath):
	submit_config = frappe.get_doc("EDI Submit Config", self.submit_config)
	key_file_doc = frappe.get_doc("File", {"file_url": submit_config.keyfile})
	cert_file_doc = frappe.get_doc("File", {"file_url": submit_config.certfile})

	key_file_path = key_file_doc.get_full_path()
	cert_file_path = cert_file_doc.get_full_path()

	return key_file_path, cert_file_path
