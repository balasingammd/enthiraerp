# This file provides an example of how to sign an XML document as the most common edi format
# You might not have an xml document and thus may not find this template useful
import frappe
from frappe.model.document import Document
from lxml import etree
from signxml import DigestAlgorithm
from signxml.xades import (
	XAdESSignaturePolicy,
	XAdESSigner,
)

from erpnext.edi.doctype.edi_template.edi_template import EDITemplate

__all__ = ["sign"]

SIGNATURE_POLICY = XAdESSignaturePolicy(
	...,
	DigestMethod=DigestAlgorithm.SHA256,
)


def sign(self: EDITemplate, data: str, doc: Document) -> str:
	key, cert = _get_credentials(self)

	signer = XAdESSigner(
		...,
		signature_policy=SIGNATURE_POLICY,
	)

	return etree.tostring(
		signer.sign(etree.XML(data), key=key, cert=cert),
		pretty_print=True,
		xml_declaration=True,
	).decode()


KeyFileContent = str
CertFileContent = str


def _get_credentials(self: EDITemplate) -> (KeyFileContent, CertFileContent):
	submit_config = frappe.get_doc("EDI Submit Config", self.submit_config)
	key_file_doc = frappe.get_doc("File", {"file_url": submit_config.keyfile})
	cert_file_doc = frappe.get_doc("File", {"file_url": submit_config.certfile})

	key_file_content = key_file_doc.get_content()
	cert_file_content = cert_file_doc.get_content()

	return key_file_content, cert_file_content
