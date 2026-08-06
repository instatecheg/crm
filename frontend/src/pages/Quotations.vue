<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Quotations" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="quotationsListView?.customListActions"
        :actions="quotationsListView.customListActions"
      />
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showQuotationModal = true"
      />
    </template>
  </LayoutHeader>

  <ViewControls
    ref="viewControls"
    v-model="quotations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Quotation"
    :options="{
      allowedViews: ['list', 'group_by', 'kanban'],
    }"
  />

  <!-- Loading State -->
  <div v-if="isLoading" class="flex h-full items-center justify-center p-8">
    <div class="text-ink-gray-4 text-lg font-medium">{{ __('Loading Quotations...') }}</div>
  </div>

  <template v-else>
    <!-- Kanban View -->
    <KanbanView
      v-if="route.params.viewType == 'kanban'"
      v-model="quotations"
      :options="{
        getRoute: (row) => ({
          name: 'Quotation',
          params: { quotationId: row.name || 'unknown' },
          query: { view: route.query.view, viewType: route.params.viewType },
        }),
        onNewClick: (column) => onNewClick(column),
      }"
      @update="(data) => viewControls.updateKanbanSettings(data)"
      @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
    >
      <template #title="{ titleField, itemName }">
        <div class="flex gap-2 items-center">
          <div v-if="titleField === 'status'">
            <IndicatorIcon :class="getRow(itemName, titleField).color" />
          </div>
          <div
            v-else-if="titleField === 'owner' && getRow(itemName, titleField).full_name"
          >
            <Avatar
              class="flex items-center"
              :image="getRow(itemName, titleField).user_image"
              :label="getRow(itemName, titleField).full_name"
              size="sm"
            />
          </div>
          <div
            v-if="['modified', 'creation', 'transaction_date', 'valid_till'].includes(titleField)"
            class="truncate text-base"
          >
            <Tooltip :text="getRow(itemName, titleField).label">
              <div>{{ getRow(itemName, titleField).timeAgo || getRow(itemName, titleField).label }}</div>
            </Tooltip>
          </div>
          <div
            v-else-if="getRow(itemName, titleField).label"
            class="truncate text-base"
          >
            {{ getRow(itemName, titleField).label }}
          </div>
          <div class="text-ink-gray-4" v-else>{{ __('No Title') }}</div>
        </div>
      </template>

      <template #fields="{ fieldName, itemName }">
        <div
          v-if="getRow(itemName, fieldName).label"
          class="truncate flex items-center gap-2"
        >
          <div v-if="fieldName === 'status'">
            <IndicatorIcon :class="getRow(itemName, fieldName).color" />
          </div>
          <div v-else-if="fieldName === 'owner'">
            <Avatar
              v-if="getRow(itemName, fieldName).full_name"
              class="flex items-center"
              :image="getRow(itemName, fieldName).user_image"
              :label="getRow(itemName, fieldName).full_name"
              size="xs"
            />
          </div>
          <div
            v-if="['modified', 'creation', 'transaction_date', 'valid_till'].includes(fieldName)"
            class="truncate text-base"
          >
            <Tooltip :text="getRow(itemName, fieldName).label">
              <div>{{ getRow(itemName, fieldName).timeAgo || getRow(itemName, fieldName).label }}</div>
            </Tooltip>
          </div>
          <div v-else-if="fieldName === '_assign'" class="flex items-center">
            <MultipleAvatar
              :avatars="getRow(itemName, fieldName).label"
              size="xs"
            />
          </div>
          <div v-else class="truncate text-base">
            {{ getRow(itemName, fieldName).label }}
          </div>
        </div>
      </template>

      <template #actions="{ itemName }">
        <div class="flex gap-2 items-center justify-between">
          <div class="text-ink-gray-5 flex items-center gap-1.5">
            <EmailAtIcon class="h-4 w-4" />
            <span v-if="getRow(itemName, '_email_count').label">
              {{ getRow(itemName, '_email_count').label }}
            </span>
            <span class="text-3xl leading-[0]"> &middot; </span>
            <NoteIcon class="h-4 w-4" />
            <span v-if="getRow(itemName, '_note_count').label">
              {{ getRow(itemName, '_note_count').label }}
            </span>
            <span class="text-3xl leading-[0]"> &middot; </span>
            <TaskIcon class="h-4 w-4" />
            <span v-if="getRow(itemName, '_task_count').label">
              {{ getRow(itemName, '_task_count').label }}
            </span>
            <span class="text-3xl leading-[0]"> &middot; </span>
            <CommentIcon class="h-4 w-4" />
            <span v-if="getRow(itemName, '_comment_count').label">
              {{ getRow(itemName, '_comment_count').label }}
            </span>
          </div>
          <Dropdown
            class="flex items-center gap-2"
            :options="actions(itemName)"
            variant="ghost"
            @click.stop.prevent
          >
            <Button icon="plus" variant="ghost" />
          </Dropdown>
        </div>
      </template>
    </KanbanView>

    <!-- List View -->
    <QuotationsListView
      ref="quotationsListView"
      v-else-if="quotations.data && rows.length"
      v-model="quotations.data.page_length_count"
      v-model:list="quotations"
      :rows="rows"
      :columns="quotations.data.columns || []"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: quotations.data.row_count || 0,
        totalCount: quotations.data.total_count || 0,
      }"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @likeDoc="(data) => viewControls.likeDoc(data)"
      @selectionsChanged="
        (selections) => viewControls.updateSelections(selections)
      "
    />

    <!-- Empty State -->
    <div
      v-else-if="quotations.data"
      class="flex h-full items-center justify-center"
    >
      <div
        class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4"
      >
        <Icon class="h-10 w-10" />
        <span>{{ __('No {0} Found', [__('Quotations')]) }}</span>
        <Button
          :label="__('Create')"
          iconLeft="plus"
          @click="showQuotationModal = true"
        />
      </div>
    </div>
  </template>

  <!-- Modals -->
  <QuotationModal
    v-if="showQuotationModal"
    v-model="showQuotationModal"
    :defaults="defaults"
    @created="viewControls?.refresh()"
  />
  <NoteModal
    v-if="showNoteModal"
    v-model="showNoteModal"
    :note="note"
    doctype="Quotation"
    :doc="docname"
  />
  <TaskModal
    v-if="showTaskModal"
    v-model="showTaskModal"
    :task="task"
    doctype="Quotation"
    :doc="docname"
  />
</template>

<script setup>
import { ref, reactive, computed, h, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Tooltip, Avatar, Dropdown, Button, createResource } from 'frappe-ui'

import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import CustomActions from '@/components/CustomActions.vue'
import EmailAtIcon from '@/components/Icons/EmailAtIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuotationsListView from '@/components/ListViews/QuotationsListView.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import QuotationModal from '@/components/Modals/QuotationModal.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import ViewControls from '@/components/ViewControls.vue'

import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { formatDate, timeAgo } from '@/utils'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } = getMeta('Quotation')
const { makeCall } = globalStore()
const { getUser } = usersStore()

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

const route = useRoute()

const quotationsListView = ref(null)
const showQuotationModal = ref(false)
const defaults = reactive({})

const quotations = ref({})
const isLoading = ref(false)
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// Adapt dynamic fetching for the list
const fetchQuotations = () => {
  isLoading.value = true

  const resource = createResource({
    url: 'frappe.client.get_list',
    params: {
      doctype: 'Quotation',
      fields: ['name', 'customer_name', 'status', 'grand_total', 'valid_till', 'owner', '_assign', 'modified'],
      limit_page_length: 50,
    },
    onSuccess(data) {
      // Re-hydrate the reactive object matching ViewControls expectations
      quotations.value = {
        data: {
          data: data || [],
          columns: [
            { key: 'name', label: 'ID', type: 'Link' },
            { key: 'customer_name', label: 'Customer', type: 'Data' },
            { key: 'status', label: 'Status', type: 'Select' },
            { key: 'grand_total', label: 'Amount', type: 'Currency' },
            { key: 'valid_till', label: 'Valid Till', type: 'Date' }
          ],
          rows: ['customer_name', 'status', 'grand_total', 'valid_till'],
          row_count: data?.length || 0,
          total_count: data?.length || 0,
          view_type: 'list'
        }
      }
    },
    onError(err) {
      console.error('[Fetch error]:', err)
    },
  })

  resource.fetch().finally(() => {
    isLoading.value = false
  })
}

// Fetch on initialization
onMounted(() => {
  fetchQuotations()
})

// Safe-guarded computed row-fetcher
function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      return value
    }
    return { label: value }
  }
  const matchingRow = rows.value?.find((row) => row.name == name)
  return matchingRow ? getValue(matchingRow[field]) : { label: '' }
}

// Compute rows safely combining your data arrays and layout parsing
const rows = computed(() => {
  if (!quotations.value?.data?.data) return []

  const listRows = Array.isArray(quotations.value.data.data) 
    ? quotations.value.data.data 
    : []

  if (quotations.value.data.view_type === 'group_by') {
    if (!quotations.value?.data.group_by_field?.fieldname) return []
    return getGroupedByRows(
      listRows,
      quotations.value?.data.group_by_field,
      quotations.value.data.columns,
    )
  } else if (quotations.value.data.view_type === 'kanban') {
    return getKanbanRows(listRows, quotations.value.data.fields)
  } else {
    return parseRows(listRows, quotations.value.data.columns)
  }
})

function getGroupedByRows(listRows, groupByField, columns) {
  let groupedRows = []

  groupByField.options?.forEach((option) => {
    let filteredRows = listRows.filter(
      (row) => !option ? !row[groupByField.fieldname] : row[groupByField.fieldname] == option
    )

    let groupDetail = {
      label: groupByField.label,
      group: option || __(' '),
      collapsed: false,
      rows: parseRows(filteredRows, columns),
    }
    if (groupByField.fieldname == 'status') {
      groupDetail.icon = () =>
        h(IndicatorIcon, {
          class: getQuotationStatusColor(option),
        })
    }
    groupedRows.push(groupDetail)
  })

  return groupedRows
}

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

// Safe layout dynamic parsing
function parseRows(rawRows, columns = []) {
  if (!Array.isArray(rawRows)) return []
  
  // Safe extraction of visible UI layout fields
  const layoutFields = Array.isArray(quotations.value?.data?.rows) 
    ? quotations.value.data.rows 
    : []

  let view_type = quotations.value?.data?.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rawRows.map((quotation) => {
    let _rows = {}
    
    // Explicitly add 'name' so vue-router doesn't crash on missing quotationId
    _rows['name'] = quotation.name || ''

    layoutFields.forEach((row) => {
      _rows[row] = quotation[row]

      let fieldType = columns?.find(
        (col) => (col[key] || col.value) == row,
      )?.[type]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(quotation[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, quotation)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, quotation)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, quotation)
      }

      if (row == 'status') {
        _rows[row] = {
          label: quotation.status,
          color: getQuotationStatusColor(quotation.status),
        }
      } else if (row == 'owner') {
        _rows[row] = {
          label: quotation.owner && getUser(quotation.owner).full_name,
          ...(quotation.owner && getUser(quotation.owner)),
        }
      } else if (row == '_assign') {
        let assignees = JSON.parse(quotation._assign || '[]')
        _rows[row] = assignees.map((user) => ({
          name: user,
          image: getUser(user).user_image,
          label: getUser(user).full_name,
        }))
      } else if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(quotation[row]),
          timeAgo: __(timeAgo(quotation[row])),
        }
      } else if (['transaction_date', 'valid_till'].includes(row)) {
        _rows[row] = {
          label: quotation[row] ? formatDate(quotation[row]) : '',
        }
      }
    })

    _rows['_email_count'] = quotation._email_count
    _rows['_note_count'] = quotation._note_count
    _rows['_task_count'] = quotation._task_count
    _rows['_comment_count'] = quotation._comment_count
    return _rows
  })
}

function onNewClick(column) {
  let column_field = quotations.value?.params?.column_field
  if (column_field) {
    defaults[column_field] = column.column.name
  }
  showQuotationModal.value = true
}

function actions(itemName) {
  return [
    {
      icon: h(NoteIcon, { class: 'h-4 w-4' }),
      label: __('New Note'),
      onClick: () => showNote(itemName),
    },
    {
      icon: h(TaskIcon, { class: 'h-4 w-4' }),
      label: __('New Task'),
      onClick: () => showTask(itemName),
    },
  ]
}

const docname = ref('')
const showNoteModal = ref(false)
const note = ref({ title: '', content: '' })

function showNote(name) {
  docname.value = name
  showNoteModal.value = true
}

const showTaskModal = ref(false)
const task = ref({
  title: '',
  description: '',
  assigned_to: '',
  due_date: '',
  priority: 'Low',
  status: 'Backlog',
})

function showTask(name) {
  docname.value = name
  showTaskModal.value = true
}
</script>