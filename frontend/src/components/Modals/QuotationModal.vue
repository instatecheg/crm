<template>
  <Dialog :model-value="modelValue" @update:modelValue="$emit('update:modelValue', $event)" :options="{ title: 'Create Quotation' }">
    <form @submit.prevent="createQuotation" class="space-y-4">
      <div>
        <label class="block text-sm mb-1">Customer</label>
        <input v-model="quotation.customer" required class="w-full border rounded p-2" placeholder="Customer name" />
      </div>
      <div>
        <label class="block text-sm mb-1">Date</label>
        <input v-model="quotation.transaction_date" type="date" required class="w-full border rounded p-2" />
      </div>
      <div>
        <label class="block text-sm mb-1">Currency</label>
        <input v-model="quotation.currency" required class="w-full border rounded p-2" placeholder="e.g. USD" />
      </div>
      <div>
        <label class="block text-sm mb-1">Grand Total</label>
        <input v-model.number="quotation.grand_total" type="number" min="0" class="w-full border rounded p-2" placeholder="Total amount" />
      </div>
      <div class="flex gap-2 justify-end">
        <Button type="button" @click="$emit('update:modelValue', false)">Cancel</Button>
        <Button type="submit" variant="primary" :loading="loading">Create</Button>
      </div>
    </form>
  </Dialog>
</template>

<script setup>
import { ref, watch, toRefs } from 'vue'
import { Button, Dialog } from 'frappe-ui'

const props = defineProps({
  modelValue: Boolean,
  defaults: Object
})
const emit = defineEmits(['update:modelValue', 'created'])

const loading = ref(false)
const quotation = ref({})

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      quotation.value = { ...props.defaults }
    }
  },
  { immediate: true }
)

async function createQuotation() {
  loading.value = true
  try {
    const res = await fetch('/api/resource/Quotation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        ...quotation.value
      })
    })
    if (!res.ok) throw new Error('Failed to create quotation')
    emit('update:modelValue', false)
    emit('created')
  } finally {
    loading.value = false
  }
}
</script>
