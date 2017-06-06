# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import flt, cint, getdate
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name

class SalaryStructure(Document):
	
	def validate(self):
		self.validate_amount()
		self.validate_joining_date()
		for e in self.get('employees'):
			set_employee_name(e)

	def get_ss_values(self,employee):
		basic_info = frappe.db.sql("""select bank_name, bank_ac_no
			from `tabEmployee` where name =%s""", employee)
		ret = {'bank_name': basic_info and basic_info[0][0] or '',
			'bank_ac_no': basic_info and basic_info[0][1] or ''}
		return ret

	def validate_amount(self):
		if flt(self.net_pay) < 0 and self.salary_slip_based_on_timesheet:
			frappe.throw(_("Net pay cannot be negative"))
	
	def get_grade_info(self,employee,cdn):
		import copy
		self.deductions = []
		self.earnings = []
		if employee:
			emp_doc = frappe.get_doc("Employee",employee)
			grade_doc = frappe.get_doc("Grade",emp_doc.grade)
			#~ self.earnings = grade_doc.earnings
			self.earnings = []
			for e in  grade_doc.earnings:
				child = self.append('earnings', {})
				child.salary_component= e.salary_component
				child.abbr= e.abbr
				child.condition= e.condition
				child.amount_based_on_formula= e.amount_based_on_formula
				child.formula= e.formula
				child.amount= e.amount
				child.depends_on_lwp= e.depends_on_lwp
				child.default_amount= e.default_amount
				
			#~ self.deductions = grade_doc.deductions	
			self.deductions = []
			for e in  grade_doc.deductions:
				child = self.append('deductions', {})
				child.salary_component= e.salary_component
				child.abbr= e.abbr
				child.condition= e.condition
				child.amount_based_on_formula= e.amount_based_on_formula
				child.formula= e.formula
				child.amount= e.amount
				child.depends_on_lwp= e.depends_on_lwp
				child.default_amount= e.default_amount
							
			for value in self.get("employees"):
				if value.name == cdn : 
					level =int(emp_doc.level)
					percent =float(emp_doc.lpercent)/100
					salary = grade_doc.base 
					for l in range(0, level+1):
						salary += salary *percent
					value.base = salary	

					#~ value.base = grade_doc.base + (int(emp_doc.level)-1)*grade_doc.level_value
					
	
	def validate_joining_date(self):
		for e in self.get('employees'):
			joining_date = getdate(frappe.db.get_value("Employee", e.employee, "date_of_joining"))
			if e.from_date and getdate(e.from_date) < joining_date:
				frappe.throw(_("From Date {0} for Employee {1} cannot be before employee's joining Date {2}")
					    .format(e.from_date, e.employee, joining_date))	

@frappe.whitelist()
def make_salary_slip(source_name, target_doc = None, employee = None, as_print = False, print_format = None):
	def postprocess(source, target):
		if employee:
			target.employee = employee
		target.run_method('process_salary_structure')

	doc = get_mapped_doc("Salary Structure", source_name, {
		"Salary Structure": {
			"doctype": "Salary Slip",
			"field_map": {
				"total_earning": "gross_pay",
				"name": "salary_structure"
			}
		}
	}, target_doc, postprocess, ignore_child_tables=True)

	if cint(as_print):
		doc.name = 'Preview for {0}'.format(employee)
		return frappe.get_print(doc.doctype, doc.name, doc = doc, print_format = print_format)
	else:
		return doc


@frappe.whitelist()
def get_employees(**args):
	return frappe.get_list('Employee',filters=args['filters'], fields=['name', 'employee_name'])
