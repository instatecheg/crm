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
      <AssignTo
        v-model="assignees.data"
        doctype="Quotation"
        :docname="quotationId"
      />
      <Dropdown
        v-if="doc && statusOptionsList.length"
        :options="statusOptionsList"
        placement="right"
      >
        <template #default="{ open }">
          <Button
            v-if="doc.status"
            :label="doc.status"
            :iconRight="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix>
              <IndicatorIcon :class="getQuotationStatusColor(doc.status)" />
            </template>
          </Button>
        </template>
      </Dropdown>
    </template>
  </LayoutHeader>
  <div v-if="doc.name" class="flex h-full overflow-hidden">
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-panel>
        <Activities
          ref="activities"
          doctype="Quotation"
          :docname="quotationId"
          :tabs="tabs"
          v-model:reload="reload"
          v-model:tabIndex="tabIndex"
          @beforeSave="(data) => document.save.submit(null, { onSuccess: () => reloadAssignees(data) })"
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
        <Tooltip :text="__('Customer')">
          <div class="group relative size-12">
            <Avatar size="3xl" class="size-12" :label="title" />
          </div>
        </Tooltip>
        <div class="flex flex-col gap-2.5 truncate text-ink-gray-9">
          <Tooltip :text="doc.party_name || __('No customer set')">
            <div class="truncate text-2xl font-medium">
              {{ title }}
            </div>
          </Tooltip>
          <div class="flex gap-1.5">
            <Button
              v-if="callEnabled"
              :tooltip="__('Make a call')"
              :icon="PhoneIcon"
              @click="triggerCall"
            />

            <Button
              :tooltip="__('Send an email')"
              :icon="Email2Icon"
              @click="
                doc.contact_email
                  ? openEmailBox()
                  : toast.error(__('No email set'))
              "
            />

            <Button
              v-if="doc.crm_deal"
              :tooltip="__('Go to linked deal')"
              :icon="LinkIcon"
              @click="
                router.push({
                  name: 'Deal',
                  params: { dealId: doc.crm_deal },
                })
              "
            />

            <Button
              :tooltip="__('Attach a file')"
              :icon="AttachmentIcon"
              @click="showFilesUploader = true"
            />

            <Button
              :tooltip="__('Delete')"
              variant="subtle"
              icon="trash-2"
              theme="red"
              @click="deleteQuotation"
            />
          </div>
        </div>
      </div>
      <!-- Quick summary of items/total — Quotation-specific, no Deal equivalent -->
      <div
        v-if="doc.items?.length"
        class="flex flex-col gap-2 border-b p-5 text-base"
      >
        <div
          v-for="item in doc.items"
          :key="item.name"
          class="flex items-center justify-between text-ink-gray-7"
        >
          <span class="truncate">{{ item.item_name }} &times; {{ item.qty }}</span>
          <span class="shrink-0">{{ formatCurrency(item.amount, doc.currency) }}</span>
        </div>
        <div class="flex items-center justify-between border-t pt-2 font-medium text-ink-gray-9">
          <span>{{ __('Grand Total') }}</span>
          <span>{{ formatCurrency(doc.grand_total, doc.currency) }}</span>
        </div>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="Quotation"
          :docname="quotationId"
          @reload="sections.reload"
          @beforeFieldChange="(data) => document.save.submit(null, { onSuccess: () => reloadAssignees(data) })"
          @afterFieldChange="reloadAssignees"
        />
      </div>
    </Resizer>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <FilesUploader
    v-model="showFilesUploader"
    doctype="Quotation"
    :docname="quotationId"
    @after="
      () => {
        activities?.all_activities?.reload()
        changeTabTo('attachments')
      }
    "
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'Quotation'"
    :docname="quotationId"
    name="Quotations"
  />
</template>

<script setup>
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Icon from '@/components/Icon.vue'
import Resizer from '@/components/Resizer.vue'
import ActivityIcon from '@/components/Icons/ActivityIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import LinkIcon from '@/components/Icons/LinkIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import Activities from '@/components/Activities/Activities.vue'
import AssignTo from '@/components/AssignTo.vue'
import FilesUploader from '@/components/FilesUploader/FilesUploader.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import CustomActions from '@/components/CustomActions.vue'
import { copyToClipboard } from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { callEnabled } from '@/composables/settings'
import {
  createResource,
  Dropdown,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, h, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useActiveTabManager } from '@/composables/useActiveTabManager'

const { brand } = getSettings()
const { makeCall } = globalStore()
const { doctypeMeta } = getMeta('Quotation')

const route = useRoute()
const router = useRouter()

const props = defineProps({
  quotationId: {
    type: String,
    required: true,
  },
})

const errorTitle = ref('')
const errorMessage = ref('')
const showDeleteLinkedDocModal = ref(false)
const showFilesUploader = ref(false)
const reload = ref(false)

const { assignees, document, error } = useDocument('Quotation', props.quotationId)

const doc = computed(() => document.doc || {})

watch(error, (err) => {
  if (err) {
    errorTitle.value = __(
      err.exc_type == 'DoesNotExistError'
        ? 'Document not found'
        : 'Error occurred',
    )
    errorMessage.value = __(err.messages?.[0] || 'An error occurred')
  } else {
    errorTitle.value = ''
    errorMessage.value = ''
  }
})

// Quotation has a fixed ERPNext status list (no per-tenant "statuses"
// doctype the way CRM Deal/Lead do), so this is defined locally rather
// than pulled from a statusesStore.
const QUOTATION_STATUSES = [
  'Draft',
  'Open',
  'Replied',
  'Partially Ordered',
  'Ordered',
  'Lost',
  'Cancelled',
  'Expired',
]
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
function getQuotationStatusColor(status) {
  return QUOTATION_STATUS_COLORS[status] || 'text-ink-gray-4'
}

const statusOptionsList = computed(() =>
  QUOTATION_STATUSES.map((status) => ({
    label: status,
    icon: () => h(IndicatorIcon, { class: getQuotationStatusColor(status) }),
    onClick: () => updateField('status', status),
  })),
)

function formatCurrency(value, currency) {
  if (value == null) return ''
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency || 'USD',
      maximumFractionDigits: 2,
    }).format(value)
  } catch (e) {
    return `${currency || ''} ${value}`
  }
}

const title = computed(() => {
  let t = doctypeMeta['Quotation']?.title_field || 'party_name'
  return doc.value?.[t] || doc.value?.customer_name || props.quotationId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

const tabs = computed(() => {
  let tabOptions = [
    { name: 'Activity', label: __('Activity'), icon: ActivityIcon },
    { name: 'Emails', label: __('Emails'), icon: EmailIcon },
    { name: 'Comments', label: __('Comments'), icon: CommentIcon },
    { name: 'Data', label: __('Data'), icon: DetailsIcon },
    { name: 'Calls', label: __('Calls'), icon: PhoneIcon },
    { name: 'Tasks', label: __('Tasks'), icon: TaskIcon },
    { name: 'Notes', label: __('Notes'), icon: NoteIcon },
    { name: 'Attachments', label: __('Attachments'), icon: AttachmentIcon },
  ]
  return tabOptions
})

const { tabIndex } = useActiveTabManager(tabs, 'lastQuotationTab')

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Quotation'],
  params: { doctype: 'Quotation' },
})

if (!sections.data) sections.fetch()

const breadcrumbs = computed(() => {
  let items = [{ label: __('Quotations'), route: { name: 'Quotations' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Quotation')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Quotations',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Quotation', params: { quotationId: props.quotationId } },
  })
  return items
})

function triggerCall() {
  let mobile_no = doc.value.contact_mobile || null
  if (!mobile_no) {
    toast.error(__('No mobile number set'))
    return
  }
  makeCall(mobile_no)
}

function updateField(name, value) {
  let oldValue = doc.value[name]
  doc.value[name] = value

  document.save.submit(null, {
    onSuccess: () => (reload.value = true),
    onError: (err) => {
      doc.value[name] = oldValue
      toast.error(err.messages?.[0] || __('Error updating field'))
    },
  })
}

function reloadAssignees(data) {
  if (data?.hasOwnProperty('owner')) {
    assignees.reload()
  }
}

function deleteQuotation() {
  showDeleteLinkedDocModal.value = true
}

const activities = ref(null)

function openEmailBox() {
  let currentTab = tabs.value[tabIndex.value]
  if (!['Emails', 'Comments', 'Activities'].includes(currentTab.name)) {
    activities.value.changeTabTo('emails')
  }
  nextTick(() => (activities.value.emailBox.show = true))
}
</script>