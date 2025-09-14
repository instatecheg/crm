<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();
const name = String(route.params.name);
const loading = ref(false);
const doc = ref<any>(null);
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

async function load() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      fields: JSON.stringify([
        "name","status","transaction_date","party_name","customer","contact_person",
        "grand_total","currency","quotation_to","doctype","company"
      ])
    });
    const res = await fetch(`/api/resource/Quotation/${encodeURIComponent(name)}?${params}`, { credentials:'include' });
    const data = await res.json();
    doc.value = data.data;
  } finally { loading.value = false; }
}

async function createCustomer() {
  const fd = new FormData();
  fd.set('quotation', name);
  fd.set('customer_name', cust.customer_name || doc.value?.party_name || '');
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
    await load();
    alert(`Customer ${data.message.customer} created and linked.`);
  } else {
    alert(data?.exc || 'Failed to create customer');
  }
}

onMounted(load);
</script>

<template>
  <div class="p-6 space-y-4" v-if="doc">
    <div class="flex items-start justify-between">
      <div>
        <h1 class="text-xl font-semibold">Quotation {{ doc.name }}</h1>
        <div class="text-sm text-gray-600">
          {{ doc.transaction_date }} · {{ doc.status }} · {{ doc.currency }} {{ doc.grand_total }}
        </div>
        <div class="text-sm">
          Party: <strong>{{ doc.customer || doc.party_name || '—' }}</strong>
        </div>
      </div>
      <div class="flex gap-2">
        <button class="border rounded px-3 py-2" v-if="!doc.customer" @click="showCustomerModal = true">
          Create Customer
        </button>
        <router-link class="border rounded px-3 py-2" :to="{ name:'Quotations' }">Back</router-link>
      </div>
    </div>

    <!-- Create Customer Modal -->
    <div v-if="showCustomerModal" class="fixed inset-0 bg-black/40 flex items-center justify-center">
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
          <button class="px-3 py-2" @click="showCustomerModal=false">Cancel</button>
          <button class="bg-black text-white px-4 py-2 rounded"
                  :disabled="!cust.customer_name || !cust.tax_id || !cust.cr_file || !cust.address_line1 || !cust.city || !cust.country"
                  @click="createCustomer">
            Create & Link
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
