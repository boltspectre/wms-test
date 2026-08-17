<script setup lang="ts">
/**
 * 库存查询页
 * 需求：
 * 1. 搜索栏：商品名称/SKU 模糊搜索 + 仓库下拉筛选
 * 2. 表格展示：商品名称、SKU、库位编码、仓库名、库存数量、更新时间
 * 3. 库存数量 < 10 的行高亮为红色
 * 4. 支持分页（后端分页）
 */
import { ref, onMounted, watch } from 'vue'
import {
  getInventory,
  getWarehouses,
  type InventoryItem,
  type Warehouse,
} from '@/api'

const keyword = ref('')
const warehouseId = ref<number | undefined>(undefined)
const loading = ref(false)
const inventoryList = ref<InventoryItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const warehouses = ref<Warehouse[]>([])

const loadInventory = async () => {
  loading.value = true
  try {
    const res = await getInventory({
      keyword: keyword.value || undefined,
      warehouseId: warehouseId.value,
      page: page.value,
      pageSize: pageSize.value,
    })
    inventoryList.value = res.data.list
    total.value = res.data.total
  } catch {
    // 错误提示由全局拦截器以右上角弹窗展示
  } finally {
    loading.value = false
  }
}

// 查询按钮 / 清空搜索：回到第一页再加载
const handleSearch = () => {
  page.value = 1
  loadInventory()
}

// 仓库切换：回到第一页再加载
const handleWarehouseChange = () => {
  page.value = 1
  loadInventory()
}

// 分页切换
const handlePageChange = () => {
  loadInventory()
}

// 低库存行高亮：数量 < 10 -> 红色
const getRowStyle = ({ row }: { row: InventoryItem }) => {
  if (row.quantity < 10) {
    return { backgroundColor: '#fef0f0', color: '#f56c6c', fontWeight: '600' }
  }
  return {}
}

// 防抖：输入停顿 300ms 后自动搜索（回到第一页）
let debounceTimer: ReturnType<typeof setTimeout> | undefined
watch(keyword, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    loadInventory()
  }, 300)
})

onMounted(async () => {
  try {
    const res = await getWarehouses()
    warehouses.value = res.data
  } catch {
    // 错误提示由全局拦截器以右上角弹窗展示
  }
  await loadInventory()
})
</script>

<template>
  <div>
    <h3>库存查询</h3>

    <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap">
      <el-input
        v-model="keyword"
        placeholder="搜索商品名称/SKU..."
        style="width: 300px"
        clearable
      />
      <el-select
        v-model="warehouseId"
        placeholder="选择仓库"
        clearable
        style="width: 200px"
        @change="handleWarehouseChange"
      >
        <el-option
          v-for="wh in warehouses"
          :key="wh.id"
          :label="wh.name"
          :value="wh.id"
        />
      </el-select>
      <el-button type="primary" @click="handleSearch">查询</el-button>
    </div>

    <el-table :data="inventoryList" v-loading="loading" border stripe :row-style="getRowStyle">
      <el-table-column prop="productName" label="商品名称" />
      <el-table-column prop="sku" label="SKU" width="150" />
      <el-table-column prop="locationCode" label="库位编码" width="150" />
      <el-table-column prop="warehouseName" label="仓库" width="120" />
      <el-table-column prop="quantity" label="库存数量" width="100" />
      <el-table-column prop="updatedAt" label="更新时间" width="180" />
    </el-table>

    <div style="margin-top: 16px; text-align: right">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <el-empty v-if="!loading && inventoryList.length === 0" description="暂无库存数据，请先完成入库操作" />
  </div>
</template>
