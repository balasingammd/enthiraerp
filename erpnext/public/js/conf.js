// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide('erpnext');

// add toolbar icon
$(document).bind('toolbar_setup', function() {
	frappe.app.name = "ERPNext";

	frappe.help_feedback_link = '<p><a class="text-muted" \
		href="https://discuss.erpnext.com">Feedback</a></p>'


	$('[data-link="docs"]').attr("href", "https://erpnext.com/docs")
	$('[data-link="issues"]').attr("href", "https://github.com/frappe/erpnext/issues")


	// default documentation goes to erpnext
	// $('[data-link-type="documentation"]').attr('data-path', '/erpnext/manual/index');

	// additional help links for erpnext
	var $help_menu = $('.dropdown-help ul .documentation-links');
	$('<li><a data-link-type="forum" href="https://erpnext.com/docs/user/manual" \
		target="_blank" rel="noopener noreferrer">'+__('Documentation')+'</a></li>').insertBefore($help_menu);
	$('<li><a data-link-type="forum" href="https://discuss.erpnext.com" \
		target="_blank" rel="noopener noreferrer">'+__('User Forum')+'</a></li>').insertBefore($help_menu);
	$('<li><a href="https://github.com/frappe/erpnext/issues" \
		target="_blank" rel="noopener noreferrer">'+__('Report an Issue')+'</a></li>').insertBefore($help_menu);

});

// preferred modules for breadcrumbs
$.extend(frappe.breadcrumbs.preferred, {
	"Item Group": "Stock",
	"Customer Group": "Selling",
	"Supplier Group": "Buying",
	"Territory": "Selling",
	"Sales Person": "Selling",
	"Sales Partner": "Selling",
	"Brand": "Stock"
});

$.extend(frappe.breadcrumbs.module_map, {
	'ERPNext Integrations': 'Integrations',
	'Geo': 'Settings',
	'Portal': 'Website',
	'Utilities': 'Settings',
	'Shopping Cart': 'Website',
	'Contacts': 'CRM'
});
