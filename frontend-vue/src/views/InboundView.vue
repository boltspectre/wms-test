<script setup lang="ts">
/**
 * ============================================
 *  入库管理页 — 已实现（任务1）
 * ============================================
 *
 * 需求：
 * 1. 表单：供应商名称 + 入库明细列表
 * 2. 每行明细：选择商品（下拉远程搜索）→ 选择仓库 → 选择库位（级联）→ 输入数量
 * 3. 支持添加/删除明细行
 * 4. 提交按钮（调用 createInboundOrder API）
 *
 * 说明：
 * - 商品下拉支持远程搜索（调 getProducts），并累积缓存避免已选项 label 丢失
 * - 仓库选择后级联加载该仓库的库位列表（调 getLocations）
 * - 提交前做必填校验，成功后提示并重置表单
 */
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getProducts,
  getWarehouses,
  getLocations,
  createInboundOrder,
  type Product,
  type Warehouse,
  type Location,
} from '@/api'

const supplierName = ref('')
const items = ref<any[]>([])
const submitting = ref(false)

// 商品下拉：累积缓存（避免已选项 label 丢失）
const productMap = ref<Map<number, Product>>(new Map())
const productOptions = ref<Product[]>([])
const productLoading = ref(false)

// 仓库下拉：全量加载（数量少）
const warehouseOptions = ref<Warehouse[]>([])

const loadWarehouses = async () => {
  try {
    const res = await getWarehouses()
    warehouseOptions.value = res.data
  } catch (e: any) {
    ElMessage.error('仓库加载失败: ' + (e.response?.data?.message || e.message))
  }
}

// 初始加载全量商品
const loadAllProducts = async () => {
  try {
    const res = await getProducts()
    res.data.forEach((p) => productMap.value.set(p.id, p))
    productOptions.value = Array.from(productMap.value.values())
  } catch (e: any) {
    ElMessage.error('商品加载失败: ' + (e.response?.data?.message || e.message))
  }
}

// 商品下拉远程搜索（累积进缓存）
const remoteProductMethod = async (query: string) => {
  productLoading.value = true
  try {
    const res = await getProducts(query || undefined)
    res.data.forEach((p) => productMap.value.set(p.id, p))
    productOptions.value = Array.from(productMap.value.values())
  } catch (e: any) {
    ElMessage.error('商品搜索失败: ' + (e.response?.data?.message || e.message))
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
  try {
    const res = await getLocations(item.warehouseId)
    item.locations = res.data
  } catch (e: any) {
    ElMessage.error('库位加载失败: ' + (e.response?.data?.message || e.message))
  }
}

const handleSubmit = async () => {
  // 前端校验
  if (!supplierName.value.trim()) {
    ElMessage.warning('请填写供应商名称')
    return
  }
  if (items.value.length === 0) {
    ElMessage.warning('请至少添加一条入库明细')
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
      supplierName: supplierName.value.trim(),
      items: items.value.map((it) => ({
        productId: it.productId,
        quantity: it.quantity,
        locationCode: it.locationCode,
      })),
    }
    const res = await createInboundOrder(payload)
    ElMessage.success(`入库单创建成功，单号：${res?.data?.orderNo || ''}`)
    // 重置表单
    supplierName.value = ''
    items.value = []
    addItem()
  } catch (e: any) {
    ElMessage.error('创建失败: ' + (e.response?.data?.message || e.message))
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadWarehouses()
  loadAllProducts()
  addItem() // 默认给一行空明细
})
</script>

<template>
  <div>
    <h3>入库管理</h3>

    <el-form label-width="100px" style="max-width: 960px">
      <el-form-item label="供应商名称" required>
        <el-input v-model="supplierName" placeholder="请输入供应商名称" style="max-width: 400px" />
      </el-form-item>

      <el-form-item label="入库明细">
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
      提交入库单
    </el-button>

    <el-empty v-if="items.length === 0" description="请点击“添加明细”按钮添加入库商品" />
  </div>
</template>
