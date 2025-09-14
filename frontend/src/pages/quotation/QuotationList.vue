
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Button, ListView, ListHeader, ListHeaderItem, ListFooter, Dropdown, Tooltip } from 'frappe-ui'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import ListBulkActions from '@/components/ListBulkActions.vue'
import QuotationModal from '@/components/Modals/QuotationModal.vue'

const router = useRouter()
const loading = ref(false)
const rows = ref([])
const q = ref('')
const status = ref()
const showQuotationModal = ref(false)
const defaults = ref({})

const columns = [
  { key: 'name', label: 'Name', width: 180 },
  { key: 'transaction_date', label: 'Date', width: 120 },
  { key: 'customer', label: 'Customer', width: 200 },
  { key: 'status', label: 'Status', width: 120 },
  { key: 'grand_total', label: 'Total', width: 120, render: (row) => row.grand_total ? `${row.grand_total} ${row.currency}` : '—' },
]


// Fetch quotations from ERPNext using integration API/module
async function fetchList() {
  loading.value = true
  try {
    // Example endpoint: /api/method/crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_quotations
    // You may need to adjust the endpoint to match your integration
    const params = new URLSearchParams({
      q: q.value,
      status: status.value || '',
    })
    const res = await fetch(`/api/method/crm.fcrm.doctype.erpnext_crm_settings.erpnext_crm_settings.get_quotations?${params.toString()}`, { credentials: 'include' })
    const data = await res.json()
    // Assume data.message is the list of quotations
    rows.value = data?.message || []
  } finally {
    loading.value = false
  }
}

function openCreateModal() {
  defaults.value = {}
  showQuotationModal.value = true
}


// Fetch deals for dropdown
const deals = ref([])
async function fetchDeals() {
  loading.value = true
  try {
    const res = await fetch('/api/resource/CRM Deal?fields=["name","organization","customer","currency"]', { credentials: 'include' })
    const data = await res.json()
    deals.value = data?.data || []
  } finally {
    loading.value = false
  }
}

// Open modal to create quotation from deal
async function openCreateFromDeal(dealId) {
  loading.value = true
  try {
    // Fetch deal details
    const res = await fetch(`/api/resource/CRM Deal/${dealId}`, { credentials: 'include' })
    const data = await res.json()
    const deal = data.data || {}
    // Prefill quotation modal with deal details
    defaults.value = {
      customer: deal.customer || deal.organization,
      party_name: deal.organization,
      currency: deal.currency || 'USD',
      // Add more fields as needed (e.g., items)
    }
    showQuotationModal.value = true
  } finally {
    loading.value = false
  }
}

</script>

<template>
  <div class="p-0">
    <div class="flex items-center justify-between border-b px-6 py-4">
      <div class="flex items-center gap-2">
        <span class="text-lg font-semibold">Quotations</span>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="solid" iconLeft="plus" @click="openCreateModal">Create</Button>
        <Dropdown :options="dealOptions" variant="ghost" @open="fetchDeals">
          <Button iconLeft="plus" variant="ghost">Create from Deal</Button>
        </Dropdown>
      </div>


// Dropdown options for deals
const dealOptions = computed(() =>
  deals.value.map(deal => ({
    label: deal.name + (deal.organization ? ` (${deal.organization})` : ''),
    onClick: () => openCreateFromDeal(deal.name)
  }))
)
    </div>
    <div class="flex items-center gap-3 px-6 py-2 border-b bg-surface-gray-1">
      <input v-model="q" @keyup.enter="fetchList" class="w-64 border rounded p-2" placeholder="Search by Name or Party" />
      <select v-model="status" @change="fetchList" class="border rounded p-2">
        <option :value="undefined">All Statuses</option>
        <option>Draft</option>
        <option>Open</option>
        <option>Lost</option>
        <option>Ordered</option>
        <option>Expired</option>
        <option>Cancelled</option>
      </select>
      <Button @click="fetchList" iconLeft="refresh-cw" variant="ghost">Refresh</Button>
    </div>
    <ListView
      :columns="columns"
      :rows="rows"
      :loading="loading"
      row-key="name"
      :options="{
        getRowRoute: (row) => ({ name: 'QuotationView', params: { name: row.name } }),
        selectable: true,
        showTooltip: true,
        resizeColumn: false,
      }"
      
    >
      <template #row="{ row }">
        <tr>
          <td>
            <span class="font-medium">{{ row.name }}</span>
          </td>
          <td>
            <span>{{ row.transaction_date }}</span>
          </td>
          <td>
            <UserAvatar :name="row.customer" size="sm" class="inline-block mr-2" />
            <span>{{ row.customer }}</span>
          </td>
          <td>
            <span class="inline-flex items-center">
              <IndicatorIcon :class="row.status === 'Draft' ? 'text-gray-400' : row.status === 'Open' ? 'text-blue-500' : row.status === 'Ordered' ? 'text-green-500' : row.status === 'Lost' ? 'text-red-500' : row.status === 'Expired' ? 'text-yellow-500' : 'text-gray-300'" />
              <span class="ml-1">{{ row.status }}</span>
            </span>
          </td>
          <td>
            <span>{{ row.grand_total ? row.grand_total + ' ' + row.currency : '—' }}</span>
          </td>
        </tr>
      </template>

    </ListView>
    <ListBulkActions v-model="rows" doctype="Quotation" />
    <QuotationModal v-if="showQuotationModal" v-model="showQuotationModal" :defaults="defaults" @created="fetchList" />
  </div>
</template>
