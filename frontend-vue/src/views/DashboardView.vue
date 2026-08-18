<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import {
  getProducts,
  getInventory,
  getOutboundOrders,
  getInboundOrders,
} from '@/api'
import { Goods, Box, Warning, Document } from '@element-plus/icons-vue'

interface Stat {
  productKinds: number
  totalQty: number
  lowStock: number
  outbound: number
}

const stat = ref<Stat>({ productKinds: 0, totalQty: 0, lowStock: 0, outbound: 0 })
const lowStockList = ref<{ productName: string; locationCode: string; quantity: number }[]>([])
const inboundTrend = ref<number[]>([0, 0, 0, 0, 0, 0, 0])
const outboundTrend = ref<number[]>([0, 0, 0, 0, 0, 0, 0])
const loading = ref(false)

function buildTrend(list: any[]): number[] {
  const days = 7
  const today = new Date()
  const buckets = new Array(days).fill(0)
  const map: Record<string, number> = {}
  list.forEach((o) => {
    const k = String(o?.createdAt || o?.orderDate || '').slice(0, 10)
    if (k) map[k] = (map[k] || 0) + 1
  })
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const k = d.toISOString().slice(0, 10)
    buckets[days - 1 - i] = map[k] || 0
  }
  return buckets
}

function maxOf(a: number[], b: number[]): number {
  return Math.max(1, ...a, ...b)
}

onMounted(async () => {
  loading.value = true
  try {
    const [p, inv, ob, ib] = await Promise.all([
      getProducts(),
      getInventory({ page: 1, pageSize: 1000 }),
      getOutboundOrders({ page: 1, pageSize: 1000 }),
      getInboundOrders({ page: 1, pageSize: 1000 }),
    ])
    const products = (p as any)?.data ?? []
    const invList = (inv as any)?.data?.list ?? []
    const low = invList.filter((i: any) => (i.quantity ?? 0) < 10)
    stat.value = {
      productKinds: products.length,
      totalQty: invList.reduce((s: number, i: any) => s + (i.quantity ?? 0), 0),
      lowStock: low.length,
      outbound: (ob as any)?.data?.total ?? 0,
    }
    lowStockList.value = low.slice(0, 8).map((i: any) => ({
      productName: i.productName,
      locationCode: i.locationCode,
      quantity: i.quantity,
    }))
    inboundTrend.value = buildTrend((ib as any)?.data?.list ?? [])
    outboundTrend.value = buildTrend((ob as any)?.data?.list ?? [])
  } finally {
    loading.value = false
  }
})

const trendMax = ref(1)
function refreshMax() {
  trendMax.value = maxOf(inboundTrend.value, outboundTrend.value)
}
watch([inboundTrend, outboundTrend], refreshMax, { immediate: true })
</script>

<template>
  <div v-loading="loading">
    <!-- 统计卡 -->
    <el-row :gutter="18" class="wb-stat-row">
      <el-col :span="6">
        <div class="wb-stat-card">
          <div class="wb-stat-icon blue"><el-icon><Goods /></el-icon></div>
          <div>
            <div class="wb-stat-label">商品种类</div>
            <div class="wb-stat-value">{{ stat.productKinds }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="wb-stat-card">
          <div class="wb-stat-icon sky"><el-icon><Box /></el-icon></div>
          <div>
            <div class="wb-stat-label">库存总量</div>
            <div class="wb-stat-value">{{ stat.totalQty.toLocaleString() }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="wb-stat-card">
          <div class="wb-stat-icon amber"><el-icon><Warning /></el-icon></div>
          <div>
            <div class="wb-stat-label">低库存预警</div>
            <div class="wb-stat-value">{{ stat.lowStock }}</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="wb-stat-card">
          <div class="wb-stat-icon green"><el-icon><Document /></el-icon></div>
          <div>
            <div class="wb-stat-label">出库单总数</div>
            <div class="wb-stat-value">{{ stat.outbound }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="18">
      <!-- 低库存预警 -->
      <el-col :span="10">
        <h3 class="wb-section-title"><el-icon><Warning /></el-icon> 低库存预警</h3>
        <el-table :data="lowStockList" empty-text="暂无低库存商品" style="width: 100%">
          <el-table-column prop="productName" label="商品" min-width="120" />
          <el-table-column prop="locationCode" label="库位" width="120" />
          <el-table-column label="库存 / 进度" min-width="160">
            <template #default="{ row }">
              <el-progress
                :percentage="Math.min(100, Math.round((row.quantity / 10) * 100))"
                :stroke-width="10"
                :color="row.quantity < 5 ? '#dc2626' : '#d97706'"
              />
              <span class="wb-qty">{{ row.quantity }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-col>

      <!-- 近 7 日出入库趋势 -->
      <el-col :span="14">
        <h3 class="wb-section-title"><el-icon><Document /></el-icon> 近 7 日出入库趋势</h3>
        <div class="wb-chart">
          <div v-for="(d, i) in 7" :key="i" class="wb-chart-col">
            <div class="wb-chart-bars">
              <div
                class="wb-bar wb-bar-in"
                :style="{ height: (inboundTrend[i - 1] / trendMax) * 100 + '%' }"
                :title="`入库 ${inboundTrend[i - 1]}`"
              />
              <div
                class="wb-bar wb-bar-out"
                :style="{ height: (outboundTrend[i - 1] / trendMax) * 100 + '%' }"
                :title="`出库 ${outboundTrend[i - 1]}`"
              />
            </div>
            <div class="wb-chart-label">{{ ['一', '二', '三', '四', '五', '六', '日'][i - 1] }}</div>
          </div>
          <div class="wb-chart-legend">
            <span><i class="wb-dot in" /> 入库</span>
            <span><i class="wb-dot out" /> 出库</span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.wb-stat-row {
  margin-bottom: 22px;
}
.wb-stat-label {
  color: var(--app-text-secondary, #64748b);
  font-size: 13px;
  margin-bottom: 6px;
}
.wb-stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--app-text, #1e293b);
  line-height: 1;
}
.wb-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 14px;
}
.wb-qty {
  font-size: 12px;
  color: var(--app-text-secondary, #64748b);
  margin-left: 6px;
}
.wb-chart {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  height: 220px;
  padding: 10px 4px 0;
}
.wb-chart-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}
.wb-chart-bars {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  width: 100%;
  justify-content: center;
}
.wb-bar {
  width: 16px;
  border-radius: 4px 4px 0 0;
  transition: height 0.4s ease;
  min-height: 2px;
}
.wb-bar-in {
  background: linear-gradient(180deg, #60a5fa, #2563eb);
}
.wb-bar-out {
  background: linear-gradient(180deg, #34d399, #16a34a);
}
.wb-chart-label {
  margin-top: 8px;
  font-size: 12px;
  color: var(--app-text-secondary, #64748b);
}
.wb-chart-legend {
  display: flex;
  gap: 18px;
  justify-content: center;
  margin-top: 10px;
  font-size: 12px;
  color: var(--app-text-secondary, #64748b);
}
.wb-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 3px;
  margin-right: 4px;
  vertical-align: middle;
}
.wb-dot.in {
  background: #2563eb;
}
.wb-dot.out {
  background: #16a34a;
}
</style>
