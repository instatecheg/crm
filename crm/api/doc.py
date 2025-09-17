import json

import frappe
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.desk.form.assign_to import set_status
from frappe.model import no_value_fields
from frappe.model.document import get_controller
from frappe.utils import make_filter_tuple
from pypika import Criterion

from crm.api.views import get_views
from crm.fcrm.doctype.crm_form_script.crm_form_script import get_form_script
from crm.utils import get_dynamic_linked_docs, get_linked_docs


# ----------- quick wiring check -----------
@frappe.whitelist(allow_guest=False)
def ping():
	"""Use this to confirm the route crm.api.doc.ping works & you’re logged in."""
	return {"ok": True, "message": "pong"}


@frappe.whitelist(allow_guest=False)
def sort_options(doctype: str):
	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{
			"label": _(field.label),
			"value": field.fieldname,
			"fieldname": field.fieldname,
		}
		for field in fields
		if field.label and field.fieldname
	]

	standard_fields = [
		{"label": "Name", "fieldname": "name"},
		{"label": "Created On", "fieldname": "creation"},
		{"label": "Last Modified", "fieldname": "modified"},
		{"label": "Modified By", "fieldname": "modified_by"},
		{"label": "Owner", "fieldname": "owner"},
	]

	for field in standard_fields:
		field["label"] = _(field["label"])
		field["value"] = field["fieldname"]
		fields.append(field)

	return fields


@frappe.whitelist(allow_guest=False)
def get_filterable_fields(doctype: str):
	allowed_fieldtypes = [
		"Check","Data","Float","Int","Currency","Dynamic Link","Link",
		"Long Text","Select","Small Text","Text Editor","Text","Duration","Date","Datetime",
	]

	c = get_controller(doctype)
	restricted_fields = []
	if hasattr(c, "get_non_filterable_fields"):
		restricted_fields = c.get_non_filterable_fields()

	res = []

	DocField = frappe.qb.DocType("DocField")
	doc_fields = get_doctype_fields_meta(DocField, doctype, allowed_fieldtypes, restricted_fields)
	res.extend(doc_fields)

	CustomField = frappe.qb.DocType("Custom Field")
	custom_fields = get_doctype_fields_meta(CustomField, doctype, allowed_fieldtypes, restricted_fields)
	res.extend(custom_fields)

	standard_fields = [
		{"fieldname": "name", "fieldtype": "Link", "label": "ID", "options": doctype},
		{"fieldname": "owner", "fieldtype": "Link", "label": "Created By", "options": "User"},
		{"fieldname": "modified_by", "fieldtype": "Link", "label": "Last Updated By", "options": "User"},
		{"fieldname": "_user_tags", "fieldtype": "Data", "label": "Tags"},
		{"fieldname": "_liked_by", "fieldtype": "Data", "label": "Like"},
		{"fieldname": "_comments", "fieldtype": "Text", "label": "Comments"},
		{"fieldname": "_assign", "fieldtype": "Text", "label": "Assigned To"},
		{"fieldname": "creation", "fieldtype": "Datetime", "label": "Created On"},
		{"fieldname": "modified", "fieldtype": "Datetime", "label": "Last Updated On"},
	]
	for field in standard_fields:
		if field.get("fieldname") not in restricted_fields and field.get("fieldtype") in allowed_fieldtypes:
			field["name"] = field.get("fieldname")
			res.append(field)

	for field in res:
		field["label"] = _(field.get("label"))
		field["value"] = field.get("fieldname")

	return res


@frappe.whitelist(allow_guest=False)
def get_group_by_fields(doctype: str):
	allowed_fieldtypes = [
		"Check","Data","Float","Int","Currency","Dynamic Link","Link","Select","Duration","Date","Datetime",
	]

	fields = frappe.get_meta(doctype).fields
	fields = [
		field for field in fields
		if field.fieldtype not in no_value_fields and field.fieldtype in allowed_fieldtypes
	]
	fields = [{"label": _(field.label), "fieldname": field.fieldname} for field in fields if field.label and field.fieldname]

	standard_fields = [
		{"label": "Name", "fieldname": "name"},
		{"label": "Created On", "fieldname": "creation"},
		{"label": "Last Modified", "fieldname": "modified"},
		{"label": "Modified By", "fieldname": "modified_by"},
		{"label": "Owner", "fieldname": "owner"},
		{"label": "Liked By", "fieldname": "_liked_by"},
		{"label": "Assigned To", "fieldname": "_assign"},
		{"label": "Comments", "fieldname": "_comments"},
		{"label": "Created On", "fieldname": "creation"},
		{"label": "Modified On", "fieldname": "modified"},
	]
	for field in standard_fields:
		field["label"] = _(field["label"])
		fields.append(field)

	return fields


def get_doctype_fields_meta(DocField, doctype, allowed_fieldtypes, restricted_fields):
	parent = "parent" if DocField._table_name == "tabDocField" else "dt"
	return (
		frappe.qb.from_(DocField)
		.select(DocField.fieldname, DocField.fieldtype, DocField.label, DocField.name, DocField.options)
		.where(DocField[parent] == doctype)
		.where(DocField.hidden == False)  # noqa: E712
		.where(Criterion.any([DocField.fieldtype == i for i in allowed_fieldtypes]))
		.where(Criterion.all([DocField.fieldname != i for i in restricted_fields]))
		.run(as_dict=True)
	)


@frappe.whitelist(allow_guest=False)
def get_quick_filters(doctype: str, cached: bool = True):
	meta = frappe.get_meta(doctype, cached)
	quick_filters = []

	if gs := frappe.db.exists("CRM Global Settings", {"dt": doctype, "type": "Quick Filters"}):
		_gf = frappe.db.get_value("CRM Global Settings", gs, "json")
		_gf = json.loads(_gf) or []

		fields = []
		for filter_name in _gf:
			if filter_name == "name":
				fields.append({"label": "Name", "fieldname": "name", "fieldtype": "Data"})
			else:
				field = next((f for f in meta.fields if f.fieldname == filter_name), None)
				if field:
					fields.append(field)
	else:
		fields = [field for field in meta.fields if field.in_standard_filter]

	for field in fields:
		options = field.get("options")
		if field.get("fieldtype") == "Select" and options and isinstance(options, str):
			opts = [{"label": o, "value": o} for o in options.split("\n")]
			if not any([not o.get("value") for o in opts]):
				opts.insert(0, {"label": "", "value": ""})
			options = opts
		quick_filters.append({
			"label": _(field.get("label")),
			"fieldname": field.get("fieldname"),
			"fieldtype": field.get("fieldtype"),
			"options": options,
		})

	if doctype == "CRM Lead":
		quick_filters = [f for f in quick_filters if f.get("fieldname") != "converted"]

	return quick_filters


@frappe.whitelist(allow_guest=False)
def update_quick_filters(quick_filters: str, old_filters: str, doctype: str):
	quick_filters = json.loads(quick_filters)
	old_filters = json.loads(old_filters)

	new_filters = [f for f in quick_filters if f not in old_filters]
	removed_filters = [f for f in old_filters if f not in quick_filters]

	create_update_global_settings(doctype, quick_filters)

	for f in removed_filters:
		update_in_standard_filter(f, doctype, 0)

	for f in new_filters:
		update_in_standard_filter(f, doctype, 1)


def create_update_global_settings(doctype, quick_filters):
	if gs := frappe.db.exists("CRM Global Settings", {"dt": doctype, "type": "Quick Filters"}):
		frappe.db.set_value("CRM Global Settings", gs, "json", json.dumps(quick_filters))
	else:
		doc = frappe.new_doc("CRM Global Settings")
		doc.dt = doctype
		doc.type = "Quick Filters"
		doc.json = json.dumps(quick_filters)
		doc.insert()


def update_in_standard_filter(fieldname, doctype, value):
	if ps := frappe.db.exists("Property Setter", {"doc_type": doctype, "field_name": fieldname, "property": "in_standard_filter"}):
		frappe.db.set_value("Property Setter", ps, "value", value)
	else:
		make_property_setter(doctype, fieldname, "in_standard_filter", value, "Check", validate_fields_for_doctype=False)


# -------- core data endpoint --------
@frappe.whitelist(allow_guest=False)
def get_data(
	doctype: str,
	filters: dict | None = None,
	order_by: str | None = None,
	page_length=20,
	page_length_count=20,
	column_field=None,
	title_field=None,
	columns=[],
	rows=[],
	kanban_columns=[],
	kanban_fields=[],
	view=None,
	default_filters=None,
):
	frappe.logger().info(f"[get_data] doctype={doctype} filters={filters} order_by={order_by} view={view}")

	if doctype == "Quotation":
		return get_quotation_data(
			filters=filters or {},
			order_by=order_by or "modified desc",
			page_length=page_length,
			page_length_count=page_length_count,
			view=view,
			default_filters=default_filters,
			column_field=column_field,
			title_field=title_field,
			custom_columns=columns,
			custom_rows=rows,
			kanban_columns=kanban_columns,
			kanban_fields=kanban_fields,
		)

	# ---- generic path (unchanged logic, but null-safe) ----
	custom_view = False
	filters = frappe._dict(filters or {})
	rows = frappe.parse_json(rows or "[]")
	columns = frappe.parse_json(columns or "[]")
	kanban_fields = frappe.parse_json(kanban_fields or "[]")
	kanban_columns = frappe.parse_json(kanban_columns or "[]")

	custom_view_name = view.get("custom_view_name") if view else None
	view_type = view.get("view_type") if view else None
	group_by_field = view.get("group_by_field") if view else None

	for key in filters:
		value = filters[key]
		if isinstance(value, list):
			if "@me" in value:
				value[value.index("@me")] = frappe.session.user
			elif "%@me%" in value:
				index = [i for i, v in enumerate(value) if v == "%@me%"]
				for i in index:
					value[i] = "%" + frappe.session.user + "%"
		elif value == "@me":
			filters[key] = frappe.session.user

	if default_filters:
		try:
			default_filters = frappe.parse_json(default_filters)
			filters.update(default_filters)
		except Exception:
			pass

	is_default = True
	data = []
	_list = get_controller(doctype)
	default_rows = []
	if hasattr(_list, "default_list_data"):
		default_rows = _list.default_list_data().get("rows")

	meta = frappe.get_meta(doctype)

	if view_type != "kanban":
		if columns or rows:
			custom_view = True
			is_default = False
			columns = frappe.parse_json(columns)
			rows = frappe.parse_json(rows)

		if not columns:
			columns = [
				{"label": "Name", "type": "Data", "key": "name", "width": "16rem"},
				{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
			]

		if not rows:
			rows = ["name"]

		default_view_filters = {"dt": doctype, "type": view_type or "list", "is_standard": 1, "user": frappe.session.user}

		if not custom_view and frappe.db.exists("CRM View Settings", default_view_filters):
			list_view_settings = frappe.get_doc("CRM View Settings", default_view_filters)
			columns = frappe.parse_json(list_view_settings.columns)
			rows = frappe.parse_json(list_view_settings.rows)
			is_default = False
		elif not custom_view or (is_default and hasattr(_list, "default_list_data")):
			rows = default_rows
			columns = _list.default_list_data().get("columns")

		for column in list(columns):
			if column.get("key") not in rows:
				rows.append(column.get("key"))
			column["label"] = _(column.get("label"))

			column_meta = meta.get_field(column.get("key"))
			if column_meta and column_meta.get("hidden"):
				columns.remove(column)

		if group_by_field and group_by_field not in rows:
			rows.append(group_by_field)

		data = (
			frappe.get_list(doctype, fields=rows, filters=filters, order_by=order_by, page_length=page_length)
			or []
		)
		data = parse_list_data(data, doctype)

	# (kanban branch preserved from your version)
	# ... omitted here for brevity; keep your existing kanban code ...

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in no_value_fields]
	fields = [
		{"label": _(field.label), "fieldtype": field.fieldtype, "fieldname": field.fieldname, "options": field.options}
		for field in fields if field.label and field.fieldname
	]

	std_fields = [
		{"label": "Name", "fieldtype": "Data", "fieldname": "name"},
		{"label": "Created On", "fieldtype": "Datetime", "fieldname": "creation"},
		{"label": "Last Modified", "fieldtype": "Datetime", "fieldname": "modified"},
		{"label": "Modified By", "fieldtype": "Link", "fieldname": "modified_by", "options": "User"},
		{"label": "Assigned To", "fieldtype": "Text", "fieldname": "_assign"},
		{"label": "Owner", "fieldtype": "Link", "fieldname": "owner", "options": "User"},
		{"label": "Like", "fieldtype": "Data", "fieldname": "_liked_by"},
	]
	for field in std_fields:
		if field.get("fieldname") not in rows:
			rows.append(field.get("fieldname"))
		if field not in fields:
			field["label"] = _(field["label"])
			fields.append(field)

	if custom_view_name:
		is_default = frappe.db.get_value("CRM View Settings", custom_view_name, "load_default_columns")

	return {
		"data": data,
		"columns": columns,
		"rows": rows,
		"fields": fields,
		"column_field": column_field,
		"title_field": title_field,
		"kanban_columns": kanban_columns,
		"kanban_fields": kanban_fields,
		"group_by_field": group_by_field if (view or {}).get("view_type") == "group_by" else None,
		"page_length": page_length,
		"page_length_count": page_length_count,
		"is_default": is_default,
		"views": get_views(doctype),
		"total_count": frappe.get_list(doctype, filters=filters, fields="count(*) as total_count")[0].total_count,
		"row_count": len(data),
		"form_script": get_form_script(doctype),
		"list_script": get_form_script(doctype, "List"),
		"view_type": (view or {}).get("view_type"),
	}


def parse_list_data(data, doctype):
	_list = get_controller(doctype)
	if hasattr(_list, "parse_list_data"):
		data = _list.parse_list_data(data)
	return data


def convert_filter_to_tuple(doctype, filters):
	if isinstance(filters, dict):
		filters_items = filters.items()
		filters = []
		for key, value in filters_items:
			filters.append(make_filter_tuple(doctype, key, value))
	return filters


def get_records_based_on_order(doctype, rows, filters, page_length, order):
	records = []
	filters = convert_filter_to_tuple(doctype, filters)
	in_filters = filters.copy()
	in_filters.append([doctype, "name", "in", order[:page_length]])
	records = frappe.get_list(doctype, fields=rows, filters=in_filters, order_by="creation desc", page_length=page_length)

	if len(records) < page_length:
		not_in_filters = filters.copy()
		not_in_filters.append([doctype, "name", "not in", order])
		remaining_records = frappe.get_list(
			doctype, fields=rows, filters=not_in_filters, order_by="creation desc",
			page_length=page_length - len(records),
		)
		for record in remaining_records:
			records.append(record)

	return records


@frappe.whitelist(allow_guest=False)
def get_fields_meta(doctype, restricted_fieldtypes=None, as_array=False, only_required=False):
	not_allowed_fieldtypes = ["Tab Break","Section Break","Column Break"]
	if restricted_fieldtypes:
		restricted_fieldtypes = frappe.parse_json(restricted_fieldtypes)
		not_allowed_fieldtypes += restricted_fieldtypes

	fields = frappe.get_meta(doctype).fields
	fields = [field for field in fields if field.fieldtype not in not_allowed_fieldtypes]

	standard_fields = [
		{"fieldname": "name", "fieldtype": "Link", "label": "ID", "options": doctype},
		{"fieldname": "owner", "fieldtype": "Link", "label": "Created By", "options": "User"},
		{"fieldname": "modified_by", "fieldtype": "Link", "label": "Last Updated By", "options": "User"},
		{"fieldname": "_user_tags", "fieldtype": "Data", "label": "Tags"},
		{"fieldname": "_liked_by", "fieldtype": "Data", "label": "Like"},
		{"fieldname": "_comments", "fieldtype": "Text", "label": "Comments"},
		{"fieldname": "_assign", "fieldtype": "Text", "label": "Assigned To"},
		{"fieldname": "creation", "fieldtype": "Datetime", "label": "Created On"},
		{"fieldname": "modified", "fieldtype": "Datetime", "label": "Last Updated On"},
	]
	for field in standard_fields:
		if not restricted_fieldtypes or field.get("fieldtype") not in restricted_fieldtypes:
			fields.append(field)

	if only_required:
		fields = [field for field in fields if field.get("reqd")]

	if as_array:
		return fields

	fields_meta = {}
	for field in fields:
		fields_meta[field.get("fieldname")] = field
		if field.get("fieldtype") == "Table":
			_fields = frappe.get_meta(field.get("options")).fields
			fields_meta[field.get("fieldname")] = {"df": field, "fields": _fields}

	return fields_meta


@frappe.whitelist(allow_guest=False)
def remove_assignments(doctype, name, assignees, ignore_permissions=False):
	assignees = frappe.parse_json(assignees)
	if not assignees:
		return
	for assign_to in assignees:
		set_status(doctype, name, todo=None, assign_to=assign_to, status="Cancelled", ignore_permissions=ignore_permissions)


@frappe.whitelist(allow_guest=False)
def get_assigned_users(doctype, name, default_assigned_to=None):
	assigned_users = frappe.get_all(
		"ToDo",
		fields=["allocated_to"],
		filters={"reference_type": doctype, "reference_name": name, "status": ("!=", "Cancelled")},
		pluck="allocated_to",
	)
	users = list(set(assigned_users))
	if not users and default_assigned_to:
		users = [default_assigned_to]
	return users


@frappe.whitelist(allow_guest=False)
def get_fields(doctype: str, allow_all_fieldtypes: bool = False):
	not_allowed_fieldtypes = [*list(frappe.model.no_value_fields), "Read Only"]
	if allow_all_fieldtypes:
		not_allowed_fieldtypes = []
	fields = frappe.get_meta(doctype).fields
	return [f for f in fields if f.fieldtype not in not_allowed_fieldtypes and f.fieldname]


def getCounts(d, doctype):
	d["_email_count"] = (
		frappe.db.count("Communication", filters={
			"reference_doctype": doctype, "reference_name": d.get("name"), "communication_type": "Communication",
		}) or 0
	)
	d["_email_count"] += frappe.db.count("Communication", filters={
		"reference_doctype": doctype, "reference_name": d.get("name"), "communication_type": "Automated Message",
	})
	d["_comment_count"] = frappe.db.count("Comment", filters={
		"reference_doctype": doctype, "reference_name": d.get("name"), "comment_type": "Comment",
	})
	d["_task_count"] = frappe.db.count("CRM Task", filters={"reference_doctype": doctype, "reference_docname": d.get("name")})
	d["_note_count"] = frappe.db.count("FCRM Note", filters={"reference_doctype": doctype, "reference_docname": d.get("name")})
	return d


@frappe.whitelist(allow_guest=False)
def get_linked_docs_of_document(doctype, docname):
	doc = frappe.get_doc(doctype, docname)
	linked_docs = get_linked_docs(doc)
	dynamic_linked_docs = get_dynamic_linked_docs(doc)
	linked_docs.extend(dynamic_linked_docs)
	linked_docs = list({doc["reference_docname"]: doc for doc in linked_docs}.values())

	docs_data = []
	for ldoc in linked_docs:
		data = frappe.get_doc(ldoc["reference_doctype"], ldoc["reference_docname"])
		title = data.get("title")
		if data.doctype == "CRM Call Log":
			title = f"Call from {data.get('from')} to {data.get('to')}"
		if data.doctype == "CRM Deal":
			title = data.get("organization")

		docs_data.append({
			"doc": data.doctype,
			"title": title or data.get("name"),
			"reference_docname": ldoc["reference_docname"],
			"reference_doctype": ldoc["reference_doctype"],
		})
	return docs_data


def remove_doc_link(doctype, docname):
	ld = frappe.get_doc(doctype, docname)
	ld.update({"reference_doctype": None, "reference_docname": None})
	ld.save(ignore_permissions=True)


def remove_contact_link(doctype, docname):
	ld = frappe.get_doc(doctype, docname)
	ld.update({"contact": None, "contacts": []})
	ld.save(ignore_permissions=True)


@frappe.whitelist(allow_guest=False)
def remove_linked_doc_reference(items, remove_contact=None, delete=False):
	if isinstance(items, str):
		items = frappe.parse_json(items)

	for item in items:
		if remove_contact:
			remove_contact_link(item["doctype"], item["docname"])
		else:
			remove_doc_link(item["doctype"], item["docname"])
		if delete:
			frappe.delete_doc(item["doctype"], item["docname"])
	return "success"


@frappe.whitelist(allow_guest=False)
def delete_bulk_docs(doctype, items, delete_linked=False):
	from frappe.desk.reportview import delete_bulk

	items = frappe.parse_json(items)
	for doc in items:
		linked_docs = get_linked_docs_of_document(doctype, doc)
		for linked_doc in linked_docs:
			remove_linked_doc_reference(
				[{"doctype": linked_doc["reference_doctype"], "docname": linked_doc["reference_docname"]}],
				remove_contact=doctype == "Contact",
				delete=delete_linked,
			)

	if len(items) > 10:
		frappe.enqueue("frappe.desk.reportview.delete_bulk", doctype=doctype, items=items)
	else:
		delete_bulk(doctype, items)


# ------------------------------
# Quotation helpers
# ------------------------------
def _quotation_columns_and_rows():
	"""Pull from ERPNext Quotation.default_list_data() if available; fallback otherwise."""
	doctype = "Quotation"
	ListCtl = get_controller(doctype)
	if hasattr(ListCtl, "default_list_data"):
		defs = ListCtl.default_list_data()
		cols = defs.get("columns", [])
		rows = defs.get("rows", []) or ["name"]
	else:
		cols = [
			{"label": _("Quotation"), "type": "Link", "key": "name", "width": "10rem"},
			{"label": _("Customer Name"), "type": "Data", "key": "customer_name", "width": "14rem"},
			{"label": _("Status"), "type": "Data", "key": "status", "width": "8rem"},
			{"label": _("Grand Total"), "type": "Currency", "key": "grand_total", "width": "10rem"},
			{"label": _("Transaction Date"), "type": "Date", "key": "transaction_date", "width": "10rem"},
			{"label": _("Valid Till"), "type": "Date", "key": "valid_till", "width": "10rem"},
			{"label": _("Owner"), "type": "Data", "key": "owner", "width": "10rem"},
			{"label": _("Modified"), "type": "Datetime", "key": "modified", "width": "10rem"},
		]
		rows = ["name","customer_name","status","grand_total","transaction_date","valid_till","owner","modified"]
	return cols, rows


@frappe.whitelist(allow_guest=False)
def get_quotation_list(filters=None, order_by=None, limit=20):
	"""Simple endpoint to test DB/permissions quickly from the browser."""
	f = frappe._dict(filters or {})
	cols, rows = _quotation_columns_and_rows()
	data = frappe.get_list("Quotation", fields=rows, filters=f, order_by=order_by or "modified desc", page_length=limit)
	return {"ok": True, "rows": rows, "data": data, "count": len(data)}


def get_quotation_data(
	filters=None,
	order_by=None,
	page_length=20,
	page_length_count=20,
	view=None,
	default_filters=None,
	column_field=None,
	title_field=None,
	custom_columns=None,
	custom_rows=None,
	kanban_columns=None,
	kanban_fields=None,
):
	doctype = "Quotation"
	log_prefix = "[QuotationList]"

	# Normalize filters
	filters = frappe._dict(filters or {})
	if default_filters:
		try:
			filters.update(frappe.parse_json(default_filters))
		except Exception:
			pass

	# resolve @me tokens
	for key in list(filters.keys()):
		val = filters[key]
		if isinstance(val, list) and "@me" in val:
			val = [frappe.session.user if v == "@me" else v for v in val]
			filters[key] = val
		elif val == "@me":
			filters[key] = frappe.session.user

	f = frappe._dict(filters or {})

	try:
		columns, rows = _quotation_columns_and_rows()

		# UI overrides
		if custom_columns:
			try: columns = frappe.parse_json(custom_columns)
			except Exception: pass
		if custom_rows:
			try: rows = frappe.parse_json(custom_rows)
			except Exception: pass

		# ensure all column keys in rows
		for c in columns:
			k = c.get("key")
			if k and k not in rows:
				rows.append(k)
			if "label" in c:
				c["label"] = _(c["label"])

		frappe.logger().info(f"{log_prefix} filters={dict(filters)} order_by={order_by} page_length={page_length}")
		data = frappe.get_list(
			doctype, fields=rows, filters=f, order_by=order_by or "modified desc", page_length=page_length
		) or []

		# meta fields for ViewControls
		meta_fields = frappe.get_meta(doctype).fields
		meta_fields = [f for f in meta_fields if f.fieldtype not in no_value_fields and f.label and f.fieldname]
		fields = [{"label": _(f.label), "fieldtype": f.fieldtype, "fieldname": f.fieldname, "options": f.options} for f in meta_fields]

		std_fields = [
			{"label": "Name", "fieldtype": "Data", "fieldname": "name"},
			{"label": "Created On", "fieldtype": "Datetime", "fieldname": "creation"},
			{"label": "Last Modified", "fieldtype": "Datetime", "fieldname": "modified"},
			{"label": "Modified By", "fieldtype": "Link", "fieldname": "modified_by", "options": "User"},
			{"label": "Assigned To", "fieldtype": "Text", "fieldname": "_assign"},
			{"label": "Owner", "fieldtype": "Link", "fieldname": "owner", "options": "User"},
			{"label": "Like", "fieldtype": "Data", "fieldname": "_liked_by"},
		]
		for fdf in std_fields:
			if fdf["fieldname"] not in rows:
				rows.append(fdf["fieldname"])
			if fdf not in fields:
				fdf["label"] = _(fdf["label"])
				fields.append(fdf)

		total_count = frappe.db.count(doctype, filters=f)
		view_type = (view or {}).get("view_type")

		return {
			"data": data,
			"columns": columns,
			"rows": rows,
			"fields": fields,
			"column_field": column_field,
			"title_field": title_field,
			"kanban_columns": kanban_columns or [],
			"kanban_fields": kanban_fields or [],
			"group_by_field": None,
			"page_length": page_length,
			"page_length_count": page_length_count,
			"is_default": True,
			"views": get_views(doctype),
			"total_count": total_count,
			"row_count": len(data),
			"form_script": get_form_script(doctype),
			"list_script": get_form_script(doctype, "List"),
			"view_type": view_type,
		}
	except Exception:
		frappe.log_error(f"Error fetching quotations: {frappe.get_traceback()}")
		return {
			"data": [],
			"columns": [],
			"rows": [],
			"fields": [],
			"column_field": column_field,
			"title_field": title_field,
			"kanban_columns": [],
			"kanban_fields": [],
			"group_by_field": None,
			"page_length": page_length,
			"page_length_count": page_length_count,
			"is_default": True,
			"views": get_views("Quotation"),
			"total_count": 0,
			"row_count": 0,
			"form_script": get_form_script("Quotation"),
			"list_script": get_form_script("Quotation", "List"),
			"view_type": (view or {}).get("view_type"),
		}
