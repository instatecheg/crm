<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Button, createResource } from 'frappe-ui';
import { formatDate, formatCurrency } from '@/utils';

const route = useRoute();
const router = useRouter();
const quotationId = String(route.params.quotationId);
const loading = ref(false);
const showCustomerModal = ref(false);

const cust = reactive({
  customer_name: '',
  tax_id: '',
  cr_file: null as File | null,
  address_line1: '',
  city: '',
  country: 'Saudi Arabia',
  pincode: ''
});

// Fetch quotation details using the new API
const quotationResource = createResource({
  url: 'crm.api.quotation.get_quotation_details',
  params: { quotation_name: quotationId },
  auto: true,
});

const quotation = computed(() => quotationResource.data?.quotation);
const items = computed(() => quotationResource.data?.items || []);

// Navigate back to quotation list
function goBack() {
  router.push({ name: 'Quotations' });
}

async function createCustomer() {
  const fd = new FormData();
  fd.set('quotation', quotationId);
  fd.set('customer_name', cust.customer_name || quotation.value?.party_name || '');
  fd.set('tax_id', cust.tax_id || '');
  fd.set('address_line1', cust.address_line1 || '');
  fd.set('city', cust.city || '');
  fd.set('country', cust.country || 'Saudi Arabia');
  fd.set('pincode', cust.pincode || '');
  if (cust.cr_file) fd.set('cr_file', cust.cr_file, cust.cr_file.name);

  const res = await fetch('/api/method/instatech_crm.create_customer_from_quotation', {
    method: 'POST',
    credentials: 'include',
    body: fd,
  });
  const data = await res.json();
  if (data?.message?.customer) {
    showCustomerModal.value = false;
    quotationResource.reload();
    alert(`Customer ${data.message.customer} created and linked.`);
  } else {
    alert(data?.exc || 'Failed to create customer');
  }
}
</script>

<template>
  <div class="p-6 space-y-6" v-if="quotation">
    <!-- Header -->
    <div class="flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">{{ quotation.name }}</h1>
        <div class="flex gap-4 mt-2 text-sm text-gray-600">
          <span>Date: {{ formatDate(quotation.transaction_date) }}</span>
          <span v-if="quotation.valid_till">Valid Till: {{ formatDate(quotation.valid_till) }}</span>
          <span 
            class="inline-block px-2 py-1 rounded text-xs font-medium"
            :class="{
              'bg-green-100 text-green-800': quotation.status === 'Ordered',
              'bg-yellow-100 text-yellow-800': quotation.status === 'Open',
              'bg-red-100 text-red-800': quotation.status === 'Lost',
              'bg-gray-100 text-gray-800': !['Ordered', 'Open', 'Lost'].includes(quotation.status)
            }"
          >
            {{ quotation.status }}
          </span>
        </div>
      </div>
      <div class="flex gap-2">
        <Button v-if="!quotation.customer" @click="showCustomerModal = true">
          Create Customer
        </Button>
        <Button @click="goBack">Back to List</Button>
      </div>
    </div>

    <!-- Customer/Party Information -->
    <div class="bg-white rounded-lg border border-gray-200 p-6">
      <h2 class="text-lg font-semibold mb-4">Customer Information</h2>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Customer</label>
          <p class="mt-1 text-sm text-gray-900">{{ quotation.customer || quotation.party_name || '—' }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Contact Person</label>
          <p class="mt-1 text-sm text-gray-900">{{ quotation.contact_person || '—' }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Company</label>
          <p class="mt-1 text-sm text-gray-900">{{ quotation.company || '—' }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Territory</label>
          <p class="mt-1 text-sm text-gray-900">{{ quotation.territory || '—' }}</p>
        </div>
      </div>
    </div>

    <!-- Financial Information -->
    <div class="bg-white rounded-lg border border-gray-200 p-6">
      <h2 class="text-lg font-semibold mb-4">Financial Summary</h2>
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Currency</label>
          <p class="mt-1 text-sm text-gray-900">{{ quotation.currency }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Grand Total</label>
          <p class="mt-1 text-lg font-semibold text-gray-900">
            {{ formatCurrency(quotation.grand_total, quotation.currency) }}
          </p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700">Order Type</label>
          <p class="mt-1 text-sm text-gray-900">{{ quotation.order_type || '—' }}</p>
        </div>
      </div>
    </div>

    <!-- Items -->
    <div class="bg-white rounded-lg border border-gray-200 p-6" v-if="items.length">
      <h2 class="text-lg font-semibold mb-4">Items</h2>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Item</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Qty</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Rate</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="item in items" :key="item.item_code">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">{{ item.item_name || item.item_code }}</div>
                <div class="text-sm text-gray-500">{{ item.item_code }}</div>
              </td>
              <td class="px-6 py-4">
                <div class="text-sm text-gray-900 max-w-xs truncate">{{ item.description || '—' }}</div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {{ item.qty }} {{ item.uom || '' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                {{ formatCurrency(item.rate, quotation.currency) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900">
                {{ formatCurrency(item.amount, quotation.currency) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Customer Modal -->
    <div v-if="showCustomerModal" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl w-full max-w-xl p-6 space-y-4">
        <h3 class="text-lg font-medium">Create Customer (Required Fields)</h3>
        <div class="grid grid-cols-2 gap-3">
          <label class="col-span-2">
            <span class="text-sm">Customer Name *</span>
            <input v-model="cust.customer_name" class="w-full border rounded p-2" required/>
          </label>
          <label>
            <span class="text-sm">Tax ID *</span>
            <input v-model="cust.tax_id" class="w-full border rounded p-2" required/>
          </label>
          <label>
            <span class="text-sm">CR Certificate (PDF/Image) *</span>
            <input type="file" accept=".pdf,image/*" class="w-full border rounded p-2"
                   @change="(e:any)=>{ cust.cr_file = e.target.files?.[0] || null }" required/>
          </label>
          <label class="col-span-2">
            <span class="text-sm">Address Line 1 *</span>
            <input v-model="cust.address_line1" class="w-full border rounded p-2" required/>
          </label>
          <label>
            <span class="text-sm">City *</span>
            <input v-model="cust.city" class="w-full border rounded p-2" required/>
          </label>
          <label>
            <span class="text-sm">Country *</span>
            <input v-model="cust.country" class="w-full border rounded p-2" required/>
          </label>
          <label>
            <span class="text-sm">Postal Code</span>
            <input v-model="cust.pincode" class="w-full border rounded p-2"/>
          </label>
        </div>

        <div class="flex justify-end gap-2">
          <Button @click="showCustomerModal=false">Cancel</Button>
          <Button 
            variant="solid"
            :disabled="!cust.customer_name || !cust.tax_id || !cust.cr_file || !cust.address_line1 || !cust.city || !cust.country"
            @click="createCustomer"
          >
            Create & Link
          </Button>
        </div>
      </div>
    </div>
  </div>

  <!-- Loading state -->
  <div v-else-if="quotationResource.loading" class="flex h-full items-center justify-center">
    <div class="text-lg text-gray-600">Loading quotation...</div>
  </div>

  <!-- Error state -->
  <div v-else class="flex h-full items-center justify-center">
    <div class="text-center">
      <div class="text-lg text-gray-600 mb-4">Quotation not found</div>
      <Button @click="goBack">Back to List</Button>
    </div>
  </div>
</template>
