<template>
  <Dialog :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)" :title="__('Create Quotation')">
    <template #body-content>
      <div class="p-4">
        <div class="flex flex-col gap-2">
          <label class="text-sm text-ink-gray-7">{{ __('Quotation Title') }}</label>
          <input v-model="title" class="input" :placeholder="__('Title')" />
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end gap-2 p-4">
        <button class="btn btn-ghost" @click="$emit('update:modelValue', false)">{{ __('Cancel') }}</button>
        <button class="btn btn-primary" :disabled="loading" @click="create">
          <span v-if="loading">{{ __('Creating...') }}</span>
          <span v-else>{{ __('Create') }}</span>
        </button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref } from 'vue'
import { createQuotation } from '@/utils/quotationsApi'
import { toast } from 'frappe-ui'
import { useRouter } from 'vue-router'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  dealId: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'created'])

const title = ref('')
const loading = ref(false)
const router = useRouter()

async function create() {
  try {
    if (!title.value || !title.value.trim()) {
      toast.error(__('Please enter a title'))
      return
    }
    loading.value = true
    const payload = { title: title.value, deal: props.dealId }
    let res = await createQuotation(payload)
    toast.success(__('Quotation created'))
    emit('created', res)
    emit('update:modelValue', false)
    // Navigate to Quotation page if response includes name
    if (res?.name) {
      router.push({ name: 'Quotation', params: { quotationId: res.name } })
    }
  } catch (err) {
    toast.error(err?.message || __('Error creating quotation'))
  } finally {
    loading.value = false
  }
}
</script>
