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
      <div v-if="doc.name" class="flex items-center gap-2">
        <Badge :label="doc.status" :theme="statusBadgeTheme" />
        <Button
          v-if="doc.docstatus === 0"
          variant="solid"
          :label="__('Submit')"
          :loading="isSubmitting"
          @click="submitQuotation"
        />
        <Dropdown
          v-else-if="doc.docstatus === 1 && doc.status !== 'Lost'"
          :options="statusActions"
          placement="right"
        >
          <template #default="{ open }">
            <Button
              :label="__('Actions')"
              :iconRight="open ? 'chevron-up' : 'chevron-down'"
            />
          </template>
        </Dropdown>
      </div>
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
  <Dialog
    v-model="showLostReasonDialog"
    :options="{ title: __('Mark Quotation as Lost') }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          type="autocomplete"
          :label="__('Lost Reason')"
          :options="lostReasonOptions"
          v-model="lostReasonLink"
        />
        <FormControl
          type="textarea"
          :label="__('Detailed Reason (optional)')"
          v-model="lostDetailedReason"
        />
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        :label="__('Confirm')"
        :loading="isMarkingLost"
        @click="declareLost"
      />
    </template>
  </Dialog>
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
  Dialog,
  FormControl,
  Badge,
  Tooltip,
  Avatar,
  Tabs,
  Breadcrumbs,
  usePageMeta,
  toast,
} from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'
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

// Quotation's status is mostly computed server-side by ERPNext's own
// Quotation.set_status() on every save (based on docstatus, valid_till,
// and % ordered) — Open/Expired/Ordered/Partially Ordered/Cancelled are
// NOT directly settable by writing the field. The only real actions
// exposed to users are: submit the draft, cancel the submitted doc, or
// declare it lost (which also requires a lost reason). Replied/Ordered/
// Partially Ordered/Expired have no manual control here by design —
// they're derived from emails, linked Sales Orders, and the valid_till
// date respectively.
const QUOTATION_STATUS_COLORS = {
  Draft: 'gray',
  Open: 'blue',
  Replied: 'yellow',
  'Partially Ordered': 'orange',
  Ordered: 'green',
  Lost: 'red',
  Cancelled: 'gray',
  Expired: 'gray',
}

const statusBadgeTheme = computed(
  () => QUOTATION_STATUS_COLORS[doc.value.status] || 'gray',
)

const isSubmitting = ref(false)
const isMarkingLost = ref(false)
const showLostReasonDialog = ref(false)
const lostReasonLink = ref('') // holds { label, value } from FormControl autocomplete, or a plain string
const lostDetailedReason = ref('')

const lostReasonsResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'Quotation Lost Reason',
    fields: ['name'],
    limit_page_length: 0,
  },
  auto: true,
})

const lostReasonOptions = computed(() =>
  (lostReasonsResource.data || []).map((d) => ({
    label: d.name,
    value: d.name,
  })),
)

// Must come after showLostReasonDialog/lostReasonsResource are declared —
// watch()'s source is read immediately when this line runs, so referencing
// either of them before their `const` declaration executes throws a
// "Cannot access before initialization" (TDZ) error and crashes the whole
// component on load.
watch(showLostReasonDialog, (isOpen) => {
  if (isOpen) {
    lostReasonsResource.reload()
  }
})

const statusActions = computed(() => [
  {
    label: __('Mark as Lost'),
    onClick: () => (showLostReasonDialog.value = true),
  },
  {
    label: __('Cancel Quotation'),
    onClick: cancelQuotation,
  },
])

function submitQuotation() {
  isSubmitting.value = true
  createResource({
    url: 'frappe.client.submit',
    params: { doc: JSON.stringify({ ...doc.value, docstatus: 1 }) },
    auto: true,
    onSuccess: () => {
      isSubmitting.value = false
      document.reload()
    },
    onError: (err) => {
      isSubmitting.value = false
      toast.error(err.messages?.[0] || __('Could not submit'))
    },
  })
}

function cancelQuotation() {
  createResource({
    url: 'frappe.client.cancel',
    params: { doctype: 'Quotation', name: props.quotationId },
    auto: true,
    onSuccess: () => document.reload(),
    onError: (err) => toast.error(err.messages?.[0] || __('Could not cancel')),
  })
}

function declareLost() {
  // FormControl's autocomplete binds the whole { label, value } option to
  // v-model, not just the raw string — send only the value to the backend.
  const reasonValue = lostReasonLink.value?.value ?? lostReasonLink.value
  if (!reasonValue) {
    toast.error(__('Please select a lost reason'))
    return
  }
  isMarkingLost.value = true
  createResource({
    url: 'crm.overrides.quotation.declare_quotation_lost',
    params: {
      quotation: props.quotationId,
      lost_reasons_list: JSON.stringify([{ lost_reason: reasonValue }]),
      competitors: JSON.stringify([]),
      detailed_reason: lostDetailedReason.value || null,
    },
    auto: true,
    onSuccess: () => {
      isMarkingLost.value = false
      showLostReasonDialog.value = false
      lostReasonLink.value = ''
      lostDetailedReason.value = ''
      document.reload()
    },
    onError: (err) => {
      isMarkingLost.value = false
      toast.error(err.messages?.[0] || __('Could not update'))
    },
  })
}

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