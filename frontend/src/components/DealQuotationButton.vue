<template>
  <div>
    <button class="btn btn-sm btn-outline" @click="open = true">{{ __('New Quotation') }}</button>
    <FreightQuotationDialog v-model="open" :dealId="dealId" @created="onCreated" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import FreightQuotationDialog from '@/components/Modals/FreightQuotationDialog.vue'

const props = defineProps({ dealId: { type: String, required: true } })
const emit = defineEmits(['created'])

const open = ref(false)

function onCreated(res) {
  emit('created', res)
}
</script>
