# Copyright (c) 2022, Rahib Hassan and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)

	return columns, data

def get_columns():
	return [
		{
			'fieldname': 'item_code',
			'label': _('Item'),
			'fieldtype': 'Link',
			'options': 'Item',
			'width': 140
		},
		{
			'fieldname': 'warehouse',
			'label': _('Warehouse'),
			'fieldtype': 'Link',
			'options': 'Warehouse',
			'width': 200
		},
		{
			'fieldname': 'stock_balance',
			'label': _('Stock Balance'),
			'fieldtype': 'Data'
		},
		{
			'fieldname': 'valuation_rate',
			'label': _('Valuation Rate'),
			'fieldtype': 'Float',
			'width': 120
		},
		{
			'fieldname': 'posting_date',
			'label': _('Posting Date')
		},
		{
			'fieldname': 'posting_time',
			'label': _('Posting Time'),
		},
	]
	
def get_data(filters):

	conditions = get_conditions(filters)

	data = frappe.db.sql("""
		SELECT
			sum(amount) / sum(actual_qty) as valuation_rate, sum(actual_qty) as stock_balance, item_code, warehouse, posting_date, posting_time
		FROM
			`tabStock Ledger Entry` as sle
		WHERE
			sle.docstatus = 1  %s
		GROUP BY
			item_code, warehouse
		""" %(conditions), filters, as_dict=True)
	
	return data

def get_conditions(filters):
	conditions = ""
	if filters.get("item_code"):
		conditions += "and sle.item_code = %s" % frappe.db.escape(filters.get("item_code"), percent=False)
		
	if filters.get("warehouse"):
		conditions += "and sle.warehouse = %s" % frappe.db.escape(filters.get("warehouse"), percent=False)
	
	return conditions


def get_stock_balance(item, warehouse):
	from stock_management.stock_management.doctype.stock_entry.calculate_valuation_rate import get_records

	stock_balance = 0
	records = get_records(item, warehouse)
	for record in records:
		stock_balance += record.actual_qty
	
	return stock_balance