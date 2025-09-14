<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
    <template v-if="!errorTitle" #right-header>
      <CustomActions
        v-if="document._actions?.length"
        :actions="document._actions"
      />
      <CustomActions
        v-if="document.actions?.length"
        :actions="document.actions"
      />
      <AssignTo v-model="assignees.data" doctype="CRM Quotation" :docname="quotationId" />
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-panel>
        <Activities
          ref="activities"
          doctype="CRM Quotation"
          :docname="quotationId"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          @beforeSave="beforeStatusChange"
          @afterSave="reloadAssignees"
        />
      </template>
    </Tabs>
    <Resizer side="right" class="flex flex-col justify-between border-l">
      <div
        class="flex h-10.5 cursor-copy items-center border-b px-5 py-2.5 text-lg font-medium text-ink-gray-9"
        @click="copyToClipboard(quotationId)"
      >
        {{ __(quotationId) }}
      </div>
      <div class="flex items-center justify-start gap-5 border-b p-5">
        <Tooltip :text="__('Organization logo')">
          <div class="group relative size-12">
            <Avatar
              size="3xl"
              class="size-12"
              :label="title"
              :image="organization?.organization_logo"
            />
          </div>
        </Tooltip>
        <div class="flex flex-col gap-2.5 truncate text-ink-gray-9">
          <Tooltip :text="organization?.name || __('Set an organization')">
            <div class="truncate text-2xl font-medium">
              {{ title }}
            </div>
          </Tooltip>
        </div>
      </div>
      <div v-if="sections.data" class="flex flex-1 flex-col justify-between overflow-hidden">
        <SidePanelLayout
          :sections="sections.data"
          doctype="CRM Quotation"
          :docname="quotationId"
          @reload="sections.reload"
          @beforeFieldChange="beforeStatusChange"
          @afterFieldChange="reloadAssignees"
        >
          <template #default="{ section }">
            <div v-if="section.name == 'contacts_section'" class="contacts-area">
              <div class="flex h-20 items-center justify-center text-base text-ink-gray-5">
                {{ __('No contacts added') }}
              </div>
            </div>
          </template>
        </SidePanelLayout>
      </div>
    </Resizer>
  </div>
  <ErrorPage v-else-if="errorTitle" :errorTitle="errorTitle" :errorMessage="errorMessage" />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import AssignTo from '@/components/AssignTo.vue'
import { createResource, Tabs, Breadcrumbs, Avatar, Tooltip } from 'frappe-ui'
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDocument } from '@/data/document'
import { getMeta } from '@/stores/meta'
import { copyToClipboard } from '@/utils'

const props = defineProps({
  quotationId: { type: String, required: true },
})

const { document, triggerOnChange, assignees } = useDocument('CRM Quotation', props.quotationId)
const doc = computed(() => document.doc || {})

const errorTitle = ref('')
const errorMessage = ref('')
const reload = ref(false)
const { doctypeMeta } = getMeta('CRM Quotation')

watch(() => document.error, (err) => {
  if (err) {
    errorTitle.value = __('Error occurred')
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

const tabs = ref([
  { name: 'Activity', label: __('Activity'), icon: null },
])

const tabIndex = ref(0)

const sections = createResource({ url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections', params: { doctype: 'CRM Quotation' } })

if (!sections.data) sections.fetch()

const title = computed(() => {
  let t = doctypeMeta['CRM Quotation']?.title_field || 'name'
  return doc.value?.[t] || props.quotationId
})

const organization = computed(() => ({}))

function beforeStatusChange() {
  document.save.submit()
}

function reloadAssignees() {
  assignees.reload()
}
</script>
