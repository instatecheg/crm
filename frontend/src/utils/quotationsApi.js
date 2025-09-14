import { call } from 'frappe-ui'

export async function createQuotation(payload) {
  // Try custom server API first (safer if there is server-side validation).
  try {
    return await call('crm.api.quotations.create_quotation', { data: payload })
  } catch (err) {
    // If the RPC doesn't exist or fails, fallback to client.insert
    // (requires the current user to have create permission for CRM Quotation)
    if (err?.exc_type === 'AttributeError' || /not found|no method|404/i.test(err?.message || '')) {
      return await call('frappe.client.insert', {
        doc: { doctype: 'CRM Quotation', ...payload },
      })
    }
    throw err
  }
}
