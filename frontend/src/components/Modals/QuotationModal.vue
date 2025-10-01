<template>
  <Dialog v-model="show" :options="{ size: '2xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-2xl font-semibold">{{ __('Create Quotation') }}</h3>
          <Button variant="ghost" class="w-7" icon="x" @click="show = false" />
        </div>

        <!-- Quick-entry fields -->
        <FieldLayout
          ref="fieldLayoutRef"
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="quotation.doc"
          doctype="Quotation"
        />

        <ErrorMessage v-if="error" :message="__(error)" class="mt-4" />
      </div>

      <div class="px-4 pb-7 pt-4 sm:px-6 flex flex-row-reverse gap-2">
        <Button
          variant="solid"
          :label="__('Create')"
          :loading="isCreating"
          @click="createQuotation"
        />
        <Button variant="ghost" :label="__('Cancel')" @click="show = false" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Dialog, ErrorMessage, createResource } from 'frappe-ui'
import { call } from 'frappe-ui'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { useDocument } from '@/data/document'

const props = defineProps({
  modelValue: Boolean
})
const emit = defineEmits(['update:modelValue', 'created'])

// Two-way binding for modal visibility
const show = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

// Reactive Quotation document
const { document: quotation, triggerOnBeforeCreate } = useDocument('Quotation')

// Ensure items table exists
if (!quotation.doc.items) {
  quotation.doc.items = []
}

const error = ref(null)
const isCreating = ref(false)

// Fetch quick-entry layout
const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Quotation'],
  params: { doctype: 'Quotation', type: 'Quick Entry' },
  auto: true
})

// Save the new quotation via Frappe REST API
async function createQuotation() {
  isCreating.value = true
  error.value = null

  try {
    await triggerOnBeforeCreate?.()

    // Mandatory fields
    const data = {
      quotation_to: quotation.doc.quotation_to,
      transaction_date: quotation.doc.transaction_date,
      order_type: quotation.doc.order_type,
      company: quotation.doc.company,
      currency: quotation.doc.currency,
      selling_price_list: quotation.doc.selling_price_list,
      items: (quotation.doc.items || []).map(item => ({
        item_code: item.item_code,
        qty: item.qty,
        rate: item.rate
      }))
    }

    // Validation
    if (!data.quotation_to || !data.transaction_date || !data.order_type ||
        !data.company || !data.currency || !data.selling_price_list) {
      throw new Error(__('Please fill all mandatory fields'))
    }

    if (!data.items.length) {
      throw new Error(__('At least one Item is required in Quotation'))
    }

    // ✅ Send API request directly
    const res = await call('crm.api.quotation.create_quotation', {
      data:data
    })

    console.log('Created Quotation:', res)
    emit('created') // notify parent to reload list
    show.value = false
  } catch (err) {
    error.value = err?.message || 'Failed to create quotation'
  } finally {
    isCreating.value = false
  }
}
</script>
