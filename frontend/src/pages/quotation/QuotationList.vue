
<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import LayoutHeader from '@/components/LayoutHeader.vue';
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue';
import ViewControls from '@/components/ViewControls.vue';
import QuotationModal from '@/components/Modals/QuotationModal.vue';
import QuotationsListView from '@/components/ListViews/QuotationsListView.vue';
import { Button } from 'frappe-ui';
import { useRoute } from 'vue-router';

const quotations = ref({});
const loadMore = ref(1);
const triggerResize = ref(1);
const updatedPageCount = ref(20);
const showQuotationModal = ref(false);
const viewControls = ref(null);
const quotationsListView = ref(null);
const route = useRoute();

// Compute rows for the list view
const rows = computed(() => {
  console.log('[DEBUG] Computing rows, quotations.value:', quotations.value);
  console.log('[DEBUG] quotations.value?.data:', quotations.value?.data);
  
  if (!quotations.value?.data?.data) {
    console.log('[DEBUG] No data found, returning empty array');
    return [];
  }
  
  const dataArray = quotations.value.data.data;
  console.log('[DEBUG] Data array:', dataArray, 'Type:', typeof dataArray, 'Is Array:', Array.isArray(dataArray));
  
  // Ensure we return an array
  return Array.isArray(dataArray) ? dataArray : [];
});

// Debug watcher for quotations data
watch(quotations, (val) => {
  // eslint-disable-next-line no-console
  console.log('[DEBUG] Quotations list updated:', val);
}, { deep: true });
</script>

<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Quotations" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="showQuotationModal = true"
      />
    </template>
  </LayoutHeader>

  <!-- List and filter controls -->
  <ViewControls
    ref="viewControls"
    v-model="quotations"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="Quotation"
    :options="{ allowedViews: ['list', 'group_by', 'kanban'] }"
  />

  <QuotationsListView
    ref="quotationsListView"
    v-if="quotations.data && rows.length"
    v-model="quotations.data.page_length_count"
    v-model:list="quotations"
    :rows="rows"
    :columns="quotations.data.columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: quotations.data.row_count,
      totalCount: quotations.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="(selections) => viewControls.updateSelections(selections)"
  />
  <div v-else-if="quotations.data" class="flex h-full items-center justify-center">
    <div class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4">
      <span>{{ __('No {0} Found', [__('Quotations')]) }}</span>
      <Button :label="__('Create')" iconLeft="plus" @click="showQuotationModal = true" />
    </div>
  </div>

  <!-- Create Quotation modal -->
  <QuotationModal v-model="showQuotationModal" @created="viewControls?.refresh()" />
</template>
