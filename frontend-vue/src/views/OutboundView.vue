<script setup lang="ts">
/**
 * ============================================
 *  出库管理页 — 已实现（选做 A：出库单 + 并发安全）
 * ============================================
 *
 * 需求：
 * 1. 表单：客户名称 + 出库明细列表
 * 2. 每行明细：选择商品（下拉远程搜索）→ 选择仓库 → 选择库位（级联）→ 输入数量
 * 3. 支持添加/删除明细行
 * 4. 提交按钮（调用 createOutboundOrder API，后端原子扣减库存 + 并发安全）
 * 5. 下方展示最近出库单列表
 *
 * 说明：
 * - 商品/仓库/库位的级联与入库页一致
 * - 接口报错统一由 src/api/client.ts 拦截器以**右上角弹窗（ElNotification）**提示，本页不再重复弹错
 * - 提交成功用 ElMessage 提示单号并重置表单
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getProducts,
  getWarehouses,
  getLocations,
  createOutboundOrder,
  getOutboundOrders,
  type Product,
  type Warehouse,
  type Location,
} from '@/api'

const customerName = ref('')
const items = ref<any[]>([])
const submitting = ref(false)

// 商品下拉：累积缓存（避免已选项 label 丢失）
const productMap = ref<Map<number, Product>>(new Map())
const productOptions = ref<Product[]>([])
const productLoading = ref(false)

// 仓库下拉：全量加载（数量少）
const warehouseOptions = ref<Warehouse[]>([])

// 最近出库单
const orders = ref<any[]>([])
const loadingOrders = ref(false)

const loadWarehouses = async () => {
  const res = await getWarehouses()
  warehouseOptions.value = res.data
}

// 初始加载全量商品
const loadAllProducts = async () => {
  const res = await getProducts()
  res.data.forEach((p) => productMap.value.set(p.id, p))
  productOptions.value = Array.from(productMap.value.values())
}

// 商品下拉远程搜索（累积进缓存）
const remoteProductMethod = async (query: string) => {
  productLoading.value = true
  try {
    const res = await getProducts(query || undefined)
    res.data.forEach((p) => productMap.value.set(p.id, p))
    productOptions.value = Array.from(productMap.value.values())
  } finally {
    productLoading.value = false
  }
}

const addItem = () => {
  items.value.push({
    productId: undefined,
    warehouseId: undefined,
    locationCode: '',
    quantity: undefined,
    locations: [] as Location[],
  })
}

const removeItem = (index: number) => {
  items.value.splice(index, 1)
}

// 仓库变化 → 级联加载库位
const onWarehouseChange = async (item: any) => {
  item.locationCode = ''
  item.locations = []
  if (!item.warehouseId) return
  const res = await getLocations(item.warehouseId)
  item.locations = res.data
}

const handleSubmit = async () => {
  // 前端校验
  if (!customerName.value.trim()) {
    ElMessage.warning('请填写客户名称')
    return
  }
  if (items.value.length === 0) {
    ElMessage.warning('请至少添加一条出库明细')
    return
  }
  for (let i = 0; i < items.value.length; i++) {
    const it = items.value[i]
    if (!it.productId) {
      ElMessage.warning(`第 ${i + 1} 行：请选择商品`)
      return
    }
    if (!it.warehouseId) {
      ElMessage.warning(`第 ${i + 1} 行：请选择仓库`)
      return
    }
    if (!it.locationCode) {
      ElMessage.warning(`第 ${i + 1} 行：请选择库位`)
      return
    }
    if (it.quantity == null || it.quantity < 1) {
      ElMessage.warning(`第 ${i + 1} 行：数量必须大于 0`)
      return
    }
  }

  submitting.value = true
  try {
    const payload = {
      customerName: customerName.value.trim(),
      items: items.value.map((it) => ({
        productId: it.productId,
        quantity: it.quantity,
        locationCode: it.locationCode,
      })),
    }
    const res = await createOutboundOrder(payload)
    ElMessage.success(`出库单创建成功，单号：${res?.data?.orderNo || ''}`)
    // 重置表单
    customerName.value = ''
    items.value = []
    addItem()
    // 刷新下方列表
    await loadOutboundOrders()
  } finally {
    submitting.value = false
  }
}

const loadOutboundOrders = async () => {
  loadingOrders.value = true
  try {
    const res = await getOutboundOrders({ page: 1, pageSize: 20 })
    orders.value = res.data.list
  } finally {
    loadingOrders.value = false
  }
}

onMounted(async () => {
  loadWarehouses()
  loadAllProducts()
  addItem() // 默认给一行空明细
  await loadOutboundOrders()
})
</script>

<template>
  <div>
    <h3>出库管理</h3>

    <el-form label-width="100px" style="max-width: 960px">
      <el-form-item label="客户名称" required>
        <el-input v-model="customerName" placeholder="请输入客户名称" style="max-width: 400px" />
      </el-form-item>

      <el-form-item label="出库明细">
        <el-button type="primary" @click="addItem">+ 添加明细</el-button>
      </el-form-item>
    </el-form>

    <!-- 明细行 -->
    <el-card
      v-for="(item, index) in items"
      :key="index"
      style="margin-bottom: 12px"
    >
      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
        <span style="color: #909399">第 {{ index + 1 }} 行</span>

        <!-- 商品下拉（远程搜索） -->
        <el-select
          v-model="item.productId"
          filterable
          remote
          :remote-method="remoteProductMethod"
          :loading="productLoading"
          placeholder="选择 / 搜索商品"
          style="width: 240px"
          clearable
        >
          <el-option
            v-for="p in productOptions"
            :key="p.id"
            :label="`${p.name} (${p.sku})`"
            :value="p.id"
          />
        </el-select>

        <!-- 仓库下拉 → 库位级联 -->
        <el-select
          v-model="item.warehouseId"
          filterable
          placeholder="选择仓库"
          style="width: 180px"
          clearable
          @change="onWarehouseChange(item)"
        >
          <el-option
            v-for="w in warehouseOptions"
            :key="w.id"
            :label="`${w.name} (${w.code})`"
            :value="w.id"
          />
        </el-select>

        <el-select
          v-model="item.locationCode"
          placeholder="选择库位"
          style="width: 180px"
          clearable
          :disabled="!item.warehouseId"
        >
          <el-option
            v-for="loc in item.locations"
            :key="loc.code"
            :label="loc.code"
            :value="loc.code"
          />
        </el-select>

        <!-- 数量 -->
        <el-input-number v-model="item.quantity" :min="1" placeholder="数量" style="width: 140px" />

        <el-button type="danger" size="small" @click="removeItem(index)">删除</el-button>
      </div>
    </el-card>

    <el-button
      type="success"
      :loading="submitting"
      @click="handleSubmit"
      :disabled="items.length === 0"
    >
      提交出库单
    </el-button>

    <el-empty v-if="items.length === 0" description="请点击“添加明细”按钮添加出库商品" />

    <!-- 最近出库单 -->
    <h3 style="margin-top: 32px">最近出库单</h3>
    <el-table :data="orders" v-loading="loadingOrders" border stripe>
      <el-table-column prop="orderNo" label="单号" width="180" />
      <el-table-column prop="customerName" label="客户名称" />
      <el-table-column prop="status" label="状态" width="120" />
      <el-table-column prop="createdAt" label="创建时间" width="200" />
    </el-table>
  </div>
</template>
