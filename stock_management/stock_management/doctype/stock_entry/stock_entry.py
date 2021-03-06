# Copyright (c) 2022, Rahib Hassan and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, now
from frappe.query_builder.functions import Sum

def check_quantity(item):
	if item.source_warehouse:
		sle = frappe.qb.DocType('Stock Ledger Entry')
		sum_total = Sum(sle.actual_qty).as_("total_qty")
		
		result = (
			frappe.qb.from_(sle)
			.select(sum_total)
			.where(sle.warehouse == item.source_warehouse)
			).run()
		stock_balance = result[0][0]
		if stock_balance < item.quantity:
			frappe.throw(_(f"Not enough stock balance in {item.source_warehouse}"))

class StockEntry(Document):

	def warehouse_validation(self, entry_type, item):

		if entry_type == "Stock Transfer":
			if not item.source_warehouse or not item.target_warehouse:
				frappe.throw(_("Source and Target Warehouse is Mandatory"))

		if entry_type == "Material Issue":
			if not item.source_warehouse:
				frappe.throw(_(f"Source Warehouse mandatory for {entry_type}"))
			item.target_warehouse = None

		if entry_type == "Material Receipt":
			if not item.target_warehouse:
				frappe.throw(_(f"Target Warehouse mandatory for {entry_type}"))
			item.source_warehouse = None

	def create_stock_ledger(self, item, warehouse, warehouse_type):

		stock_ledger = frappe.new_doc('Stock Ledger Entry')
		stock_ledger.item_code = item.item_code
		stock_ledger.warehouse = warehouse
		stock_ledger.posting_date = today()
		stock_ledger.posting_time = now()
		stock_ledger.voucher_type = "Stock Entry"
		stock_ledger.voucher_no = self.name

		if warehouse_type == "Source":
			stock_ledger.incoming_rate = -(item.rate)
			stock_ledger.actual_qty = -(item.quantity)
			stock_ledger.amount = -(item.amount)
		elif warehouse_type == "Target":
			stock_ledger.amount = item.amount
			stock_ledger.actual_qty = item.quantity
			stock_ledger.incoming_rate = item.rate

		stock_ledger.insert()
		stock_ledger.submit()

	def on_submit(self):

		for item in self.items:

			if item.source_warehouse and item.target_warehouse:
				self.create_stock_ledger(item, warehouse = item.source_warehouse, warehouse_type = "Source")
				self.create_stock_ledger(item, warehouse = item.target_warehouse, warehouse_type = "Target")

			elif item.source_warehouse:
				self.create_stock_ledger(item, warehouse = item.source_warehouse, warehouse_type = "Source")

			elif item.target_warehouse:
				self.create_stock_ledger(item, warehouse = item.target_warehouse, warehouse_type = "Target")
				
	def validate(self):		
		for item in self.items:
			self.warehouse_validation(self.stock_entry_type, item)
			check_quantity(item)
		