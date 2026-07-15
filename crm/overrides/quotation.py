# crm/overrides/quotation.py
#
# Adds the CRM-list-view hooks (default_list_data / default_kanban_settings)
# that crm.api.doc.get_data() expects every doctype's controller to expose,
# without modifying ERPNext's core Quotation controller.
#
# Wire this up in crm/hooks.py:
#
#     override_doctype_class = {
#         "Quotation": "crm.overrides.quotation.CustomQuotation",
#         # ...merge with any existing entries already in override_doctype_class
#     }

from erpnext.selling.doctype.quotation.quotation import Quotation

import frappe


class CustomQuotation(Quotation):

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Customer",
				"type": "Data",
				"key": "party_name",
				"width": "12rem",
			},
			{
				"label": "Grand Total",
				"type": "Currency",
				"key": "grand_total",
				"align": "right",
				"width": "9rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "10rem",
			},
			{
				"label": "Valid Till",
				"type": "Date",
				"key": "valid_till",
				"width": "8rem",
			},
			{
				"label": "Assigned To",
				"type": "Text",
				"key": "_assign",
				"width": "10rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"party_name",
			"customer_name",
			"grand_total",
			"currency",
			"status",
			"transaction_date",
			"valid_till",
			"owner",
			"modified",
			"_assign",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "party_name",
			"kanban_fields": '["grand_total", "valid_till", "_assign", "modified"]',
		}