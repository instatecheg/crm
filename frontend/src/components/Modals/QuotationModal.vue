<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Quotation') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit fields layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button variant="ghost" class="w-7" icon="x" @click="show = false" />
          </div>
        </div>
        <div>
          <FieldLayout
            ref="fieldLayoutRef"
            v-if="tabs.data?.length"
            :tabs="tabs.data"
            :data="quotation.doc"
            doctype="Quotation"
          />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isQuotationCreating"
            @click="createQuotation"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useDocument } from '@/data/document'
import { createResource } from 'frappe-ui'
import { computed, ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { getUser, isManager } = usersStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)

const { document: quotation } = useDocument('Quotation')

const isQuotationCreating = ref(false)
const fieldLayoutRef = ref(null)

// Quotation uses ERPNext's fixed status list rather than a per-tenant
// statuses doctype (unlike CRM Deal/Lead), so it's defined locally here
// instead of coming from statusesStore.
const QUOTATION_STATUS_COLORS = {
  Draft: 'text-ink-gray-4',
  Open: 'text-blue-500',
  Replied: 'text-yellow-500',
  'Partially Ordered': 'text-orange-500',
  Ordered: 'text-green-600',
  Lost: 'text-red-500',
  Cancelled: 'text-ink-gray-4',
  Expired: 'text-ink-gray-4',
}
const quotationStatuses = computed(() =>
  Object.keys(QUOTATION_STATUS_COLORS).map((status) => ({
    label: status,
    value: status,
  })),
)

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Quotation'],
  params: { doctype: 'Quotation', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = quotationStatuses.value
              field.prefix =
                QUOTATION_STATUS_COLORS[quotation.doc.status] ||
                QUOTATION_STATUS_COLORS.Draft
            }

            if (field.fieldtype === 'Table') {
              quotation.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

// Helper to fetch individual Item Name dynamically
function fetchItemName(itemCode) {
  return new Promise((resolve) => {
    const resource = createResource({
      url: 'frappe.client.get_value',
      params: {
        doctype: 'Item',
        filters: { name: itemCode },
        fieldname: 'item_name',
      },
      onSuccess(data) {
        resolve(data?.item_name || null)
      },
      onError() {
        resolve(null)
      },
    })
    resource.fetch()
  })
}

// Sanitizes child items for validation compatibility
async function sanitizeQuotationItems() {
  if (!quotation.doc.items || !Array.isArray(quotation.doc.items)) return

  for (let item of quotation.doc.items) {
    // 1. Force default UOM to 'Nos' if missing
    if (!item.uom) {
      item.uom = 'Nos'
    }

    // 2. Fetch the Item Name if missing but Item Code exists
    if (!item.item_name && item.item_code) {
      const fetchedName = await fetchItemName(item.item_code)
      item.item_name = fetchedName || item.item_code // Fallback to Code if name fetch fails
    }
  }
}

async function createQuotation() {
  error.value = null
  
  // Basic validation check
  if (!quotation.doc.quotation_to) {
    error.value = __('Quotation To is required')
    return
  }
  if (!quotation.doc.party_name) {
    error.value = __('Customer/Lead is required')
    return
  }
  if (!quotation.doc.status) {
    error.value = __('Status is required')
    return
  }

  isQuotationCreating.value = true

  try {
    // Process items and fetch names/add UOM values before submission
    await sanitizeQuotationItems()

    const insertResource = createResource({
      url: 'frappe.client.insert',
      params: {
        doc: {
          doctype: 'Quotation',
          ...quotation.doc,
        },
      },
      onSuccess(doc) {
        isQuotationCreating.value = false
        show.value = false
        router.push({ name: 'Quotation', params: { quotationId: doc.name } })
      },
      onError(err) {
        isQuotationCreating.value = false
        if (!err.messages) {
          error.value = err.message
          return
        }
        error.value = err.messages.join('\n')
      },
    })

    await insertResource.fetch()
  } catch (err) {
    isQuotationCreating.value = false
    error.value = err.message || __('An unexpected error occurred.')
  }
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'Quotation' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  quotation.doc = {
    quotation_to: 'Customer',
    transaction_date: new Date().toISOString().split('T')[0],
  }
  Object.assign(quotation.doc, props.defaults)

  if (!quotation.doc.owner) {
    quotation.doc.owner = getUser().name
  }
  if (!quotation.doc.status) {
    quotation.doc.status = quotationStatuses.value[0].value
  }
})
</script>