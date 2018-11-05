# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

class TestQualityGoal(unittest.TestCase):

	def test_quality_goal(self):
		create_procedure()
		create_unit()
		test_create_goal = create_goal()
		test_get_goal = get_goal()
		self.assertEquals(test_create_goal, test_get_goal)

def create_goal():
	goal = frappe.get_doc({
		"doctype": "Quality Goal",
		"goal": "_Test Quality Goal",
		"revision": "1",
		"procedure": "_Test Quality Procedure 1",
		"frequency": "Daily",
		"measureable": "Yes",
		"objective": [
			{
				"objective": "_Test Quality Objective",
				"target": "4",
				"unit": "_Test UOM"
			}
		]
	})
	goal_exist = frappe.db.exists("Quality Goal", ""+ goal.goal +"")
	if not goal_exist:
		goal.insert()
		return goal.goal
	else:
		return goal_exist

def get_goal():
	goal = frappe.db.exists("Quality Goal", "_Test Quality Goal")
	return goal

def create_procedure():
	procedure = frappe.get_doc({
		"doctype": "Quality Procedure",
		"procedure": "_Test Quality Procedure",
		"procedure_step": [
			{
				"step": "_Test Quality Procedure Table",
			}
		]
	})
	procedure_exist = frappe.db.exists("Quality Procedure",""+ procedure.procedure +"")
	if not procedure_exist:
		procedure.insert()

def create_unit():
	unit = frappe.get_doc({
		"doctype": "UOM",
		"uom_name": "_Test UOM",
	})
	unit_exist = frappe.db.exists("UOM", ""+ unit.uom_name +"")
	if not unit_exist:
		unit.insert()
