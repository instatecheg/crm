import frappe
from frappe import _
from frappe.utils import formatdate, getdate, nowdate


@frappe.whitelist()
def get_quotations(
	limit_start=0,
	limit=20,
	order_by="modified desc",
	filters=None,
	fields=None
):
	"""Get list of quotations from ERPNext"""
	
	if not fields:
		fields = [
			"name",
			"customer",
			"party_name", 
			"transaction_date",
			"valid_till",
			"status",
			"grand_total",
			"currency",
			"company",
			"quotation_to",
			"order_type",
			"territory",
			"contact_person",
			"modified",
			"creation"
		]
	
	if filters is None:
		filters = {}
	
	# Add default filters to show only active quotations
	filters.update({
		"docstatus": ["!=", 2]  # Not cancelled
	})
	
	try:
		quotations = frappe.get_list(
			"Quotation",
			fields=fields,
			filters=filters,
			order_by=order_by,
			limit_start=limit_start,
			limit=limit,
			as_list=False
		)
		
		# Get total count for pagination
		total_count = frappe.db.count("Quotation", filters=filters)
		
		return {
			"data": quotations,
			"total_count": total_count,
			"limit_start": limit_start,
			"limit": limit
		}
		
	except Exception as e:
		frappe.log_error(f"Error fetching quotations: {str(e)}")
		return {"data": [], "total_count": 0, "limit_start": 0, "limit": limit}


@frappe.whitelist()
def get_quotation_details(quotation_name):
	"""Get detailed information about a specific quotation"""
	
	try:
		quotation = frappe.get_doc("Quotation", quotation_name)
		
		# Check permissions
		if not quotation.has_permission("read"):
			frappe.throw(_("Not permitted to view this quotation"))
		
		# Get quotation items
		items = frappe.get_list(
			"Quotation Item",
			fields=[
				"item_code",
				"item_name", 
				"description",
				"qty",
				"uom",
				"rate",
				"amount",
				"item_group",
				"warehouse"
			],
			filters={"parent": quotation_name},
			order_by="idx"
		)
		
		# Return quotation details with items
		return {
			"quotation": quotation.as_dict(),
			"items": items
		}
		
	except Exception as e:
		frappe.log_error(f"Error fetching quotation details: {str(e)}")
		frappe.throw(_("Could not fetch quotation details"))


@frappe.whitelist()
def create_quotation(data):
	"""Create a new quotation in ERPNext"""
	
	try:
		doc = frappe.new_doc("Quotation")
		doc.update(data)
		
		# Set default values if not provided
		if not doc.get("transaction_date"):
			doc.transaction_date = nowdate()
			
		if not doc.get("quotation_to"):
			doc.quotation_to = "Customer" if doc.get("customer") else "Lead"
		
		doc.insert()
		frappe.db.commit()
		
		return {
			"success": True,
			"name": doc.name,
			"message": _("Quotation created successfully")
		}
		
	except Exception as e:
		frappe.log_error(f"Error creating quotation: {str(e)}")
		frappe.throw(_("Could not create quotation: {0}").format(str(e)))


@frappe.whitelist()
def get_quotation_stats():
	"""Get quotation statistics for dashboard"""
	
	try:
		stats = {}
		
		# Total quotations
		stats["total"] = frappe.db.count("Quotation", {"docstatus": ["!=", 2]})
		
		# Draft quotations
		stats["draft"] = frappe.db.count("Quotation", {"docstatus": 0})
		
		# Submitted quotations  
		stats["submitted"] = frappe.db.count("Quotation", {"docstatus": 1})
		
		# Ordered quotations
		stats["ordered"] = frappe.db.count("Quotation", {"status": "Ordered"})
		
		# Lost quotations
		stats["lost"] = frappe.db.count("Quotation", {"status": "Lost"})
		
		# This month's quotations
		from frappe.utils import get_first_day, get_last_day
		first_day = get_first_day(nowdate())
		last_day = get_last_day(nowdate())
		
		stats["this_month"] = frappe.db.count(
			"Quotation", 
			{
				"docstatus": ["!=", 2],
				"transaction_date": ["between", [first_day, last_day]]
			}
		)
		
		return stats
		
	except Exception as e:
		frappe.log_error(f"Error fetching quotation stats: {str(e)}")
		return {}


@frappe.whitelist()
def get_quotation_filters():
	"""Get available filter options for quotations"""
	
	try:
		filters = {}
		
		# Status options
		filters["status"] = frappe.get_list(
			"Quotation",
			fields=["status"],
			distinct=True,
			filters={"docstatus": ["!=", 2]},
			pluck="status"
		)
		
		# Currency options
		filters["currency"] = frappe.get_list(
			"Quotation",
			fields=["currency"], 
			distinct=True,
			filters={"docstatus": ["!=", 2]},
			pluck="currency"
		)
		
		# Company options
		filters["company"] = frappe.get_list(
			"Company",
			fields=["name"],
			pluck="name"
		)
		
		# Territory options
		filters["territory"] = frappe.get_list(
			"Territory",
			fields=["name"],
			pluck="name"
		)
		
		return filters
		
	except Exception as e:
		frappe.log_error(f"Error fetching quotation filters: {str(e)}")
		return {}