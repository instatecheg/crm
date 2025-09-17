<template>
  <div class="rounded-lg bg-white border p-3 h-full overflow-hidden">
    <div class="flex items-center justify-between mb-2">
      <div class="text-base font-semibold truncate">
        {{ item?.data?.title || '' }}
      </div>
      <div v-if="item?.data?.subtitle" class="text-xs text-gray-500 truncate ml-2">
        {{ item.data.subtitle }}
      </div>
    </div>

    <!-- Number card -->
    <div v-if="item.type === 'number_chart'" class="flex items-center h-[120px]">
      <div class="text-3xl font-bold tabular-nums">
        <span v-if="item?.data?.prefix">{{ item.data.prefix }}</span>{{ item?.data?.value ?? 0 }}<span v-if="item?.data?.suffix">{{ item.data.suffix }}</span>
      </div>
      <div class="ml-3 text-sm text-gray-500">
        <div v-if="item?.data?.delta !== undefined" class="text-xs">
          <span :class="deltaClass(item.data)">{{ item.data.delta }}{{ item.data.deltaSuffix || '' }}</span>
        </div>
      </div>
    </div>

    <!-- Funnel (pyramid) + explanation -->
    <div v-else-if="isFunnel" class="h-[360px] flex flex-col">
      <div class="flex-1">
        <ECharts :options="funnelOptions" autoresize />
      </div>

      <!-- Explanation under chart -->
      <div class="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2">
        <div
          v-for="(row, idx) in funnelRows"
          :key="row.stage"
          class="text-xs rounded border p-2 flex items-start gap-2"
          :style="{ borderColor: seriesColors[idx % seriesColors.length] }"
        >
          <div
            class="mt-0.5 h-3 w-3 rounded"
            :style="{ background: seriesColors[idx % seriesColors.length] }"
          />
          <div class="leading-5">
            <div class="font-medium">
              {{ row.stage }}
            </div>
            <div>
              <span class="tabular-nums">Count: {{ row.count }}</span>
              <span v-if="row.amount != null">
                • Amount: {{ currency }}{{ formatMoney(row.amount) }}
              </span>
            </div>
            <div class="text-gray-500">
              % of Leads: {{ row.pctOfLeads }}% • From prev: {{ row.pctFromPrev }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Axis / Donut (fallback) -->
    <div v-else class="h-[360px]">
      <ECharts :options="genericOptions" autoresize />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ECharts } from 'frappe-ui'

const props = defineProps<{ item: any }>()

const isFunnel = computed(
  () => props.item?.type === 'funnel_chart' || props.item?.data?.chart === 'funnel'
)

const deltaClass = (d: any) =>
  d?.negativeIsBetter
    ? (Number(d.delta) <= 0 ? 'text-green-600' : 'text-red-600')
    : (Number(d.delta) >= 0 ? 'text-green-600' : 'text-red-600')

/** Palette reused for the legend chips */
const seriesColors = [
  '#3b82f6', // blue
  '#22d3ee', // cyan
  '#facc15', // yellow
  '#fb923c', // orange
  '#34d399', // green
  '#f472b6', // pink
]

/** Currency symbol from backend, defaults to blank */
const currency = computed<string>(() => props.item?.data?.currency_symbol || '')

/** Nicely format amounts */
function formatMoney(v: number): string {
  try {
    return Number(v).toLocaleString()
  } catch {
    return String(v ?? '')
  }
}

/** Build funnel ECharts options (client-side so formatters work) */
const funnelOptions = computed(() => {
  const d = props.item?.data || {}
  const rows: any[] = Array.isArray(d.funnel) ? d.funnel : []

  // Percentages are relative to the TOP stage (Leads)
  const top = Math.max(...rows.map(r => Number(r.count) || 0), 1)

  const dataPoints = rows.map((r) => {
    const c = Number(r.count) || 0
    const pct = Math.round((c / top) * 100)
    const amt = r.amount != null ? Number(r.amount) : undefined
    return { name: r.stage, value: c, amount: amt, percent: pct }
  })

  return {
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        const amt = p.data.amount != null ? `\n${currency.value}${Number(p.data.amount).toLocaleString()}` : ''
        return `<b>${p.name}</b>\n${p.value} (${p.data.percent}%)${amt}`
      },
      confine: true,
    },
    legend: { top: 0, type: 'scroll' },
    grid: { left: 8, right: 8, top: 50, bottom: 8, containLabel: true },
    series: [
      {
        type: 'funnel',
        left: '5%',
        top: 60,
        bottom: 20,
        width: '90%',
        min: 0,
        max: Math.max(...dataPoints.map(x => x.value), 1),
        sort: 'descending',
        gap: 2,
        label: {
          show: true,
          position: 'inside',
          formatter: (p: any) => {
            const amt = p.data.amount != null ? `\n${currency.value}${Number(p.data.amount).toLocaleString()}` : ''
            return `${p.name}\n${p.value} (${p.data.percent}%)${amt}`
          },
          fontSize: 12,
          width: 180,
          overflow: 'truncate',
        },
        labelLine: { show: false },
        itemStyle: { borderWidth: 1, borderColor: '#fff' },
        data: dataPoints,
      },
    ],
  }
})

/** Build the explanation rows under the funnel */
const funnelRows = computed(() => {
  const d = props.item?.data || {}
  const rows: any[] = Array.isArray(d.funnel) ? d.funnel : []
  if (!rows.length) return []

  const topCount = Math.max(Number(rows[0]?.count) || 0, 1)

  return rows.map((r, idx) => {
    const count = Number(r.count) || 0
    const prev = idx > 0 ? Number(rows[idx - 1]?.count) || 0 : count
    const pctOfLeads = Math.round((count / topCount) * 100)
    const pctFromPrev = prev ? `${Math.round((count / prev) * 100)}%` : '—'
    return {
      stage: r.stage,
      count,
      amount: r.amount != null ? Number(r.amount) : null,
      pctOfLeads,
      pctFromPrev,
    }
  })
})

/** Generic options for axis/donut when API doesn’t already send full `echartOptions` */
const genericOptions = computed(() => {
  const it = props.item
  const d = it?.data || {}

  if (it?.type === 'donut_chart') {
    return {
      tooltip: { trigger: 'item' },
      legend: { top: 0 },
      series: [
        {
          name: d.title || '',
          type: 'pie',
          radius: ['45%', '70%'],
          avoidLabelOverlap: false,
          label: { show: true, formatter: '{b}\n{c}' },
          data: (d.data || []).map((r: any) => ({
            name: r[d.categoryColumn],
            value: r[d.valueColumn],
          })),
        },
      ],
    }
  }

  // axis_chart
  return d.echartOptions || {
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 40, right: 20, top: 40, bottom: 40, containLabel: true },
    xAxis: {
      type: d?.xAxis?.type === 'time' ? 'time' : 'category',
      name: d?.xAxis?.title,
      boundaryGap: true,
    },
    yAxis: [
      { type: 'value', name: d?.yAxis?.title || '' },
      ...(d?.y2Axis ? [{ type: 'value', name: d?.y2Axis?.title || '' }] : []),
    ],
    series: (d.series || []).map((s: any) => ({ ...s })),
    dataset: d.data ? { source: d.data } : undefined,
  }
})
</script>
