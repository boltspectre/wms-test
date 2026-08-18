<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  Goods,
  Box,
  Download,
  Upload,
  Odometer,
  Sunny,
  MagicStick,
  Fold,
  Expand,
} from '@element-plus/icons-vue'

type Theme = 'original' | 'beautified'
const STORAGE_KEY = 'wms-ui-theme'

const theme = ref<Theme>((localStorage.getItem(STORAGE_KEY) as Theme) || 'original')
const isBeautified = computed(() => theme.value === 'beautified')

function applyTheme(t: Theme) {
  document.documentElement.setAttribute('data-theme', t)
  localStorage.setItem(STORAGE_KEY, t)
}
function setTheme(t: Theme) {
  theme.value = t
  applyTheme(t)
}
onMounted(() => applyTheme(theme.value))

const route = useRoute()

const baseMenus = [
  { path: '/products', title: '商品管理', icon: Goods },
  { path: '/inventory', title: '库存查询', icon: Box },
  { path: '/inbound', title: '入库管理', icon: Download },
  { path: '/outbound', title: '出库管理', icon: Upload },
]
const beautifiedMenus = [{ path: '/dashboard', title: '仪表盘', icon: Odometer }, ...baseMenus]

const collapse = ref(false)
</script>

<template>
  <el-container class="wb-root">
    <!-- 顶部栏：两种主题共用，右侧为醒目的主题切换开关 -->
    <el-header
      class="wb-topbar"
      :class="isBeautified ? 'beautified' : 'original'"
      :style="!isBeautified ? 'background:#409eff;color:#fff;display:flex;align-items:center;padding:0 20px;height:60px' : ''"
    >
      <div class="wb-brand">
        <el-icon class="wb-brand-logo"><Box /></el-icon>
        <span class="wb-brand-text">WMS 仓储管理系统</span>
      </div>

      <!-- 原版：水平菜单（保留面试官熟悉的样子） -->
      <el-menu
        v-if="!isBeautified"
        mode="horizontal"
        :default-active="route.path"
        router
        style="flex: 1; margin-left: 30px; border-bottom: none"
        background-color="#409eff"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-menu-item v-for="m in baseMenus" :key="m.path" :index="m.path">
          {{ m.title }}
        </el-menu-item>
      </el-menu>

      <div class="wb-topbar-right">
        <div class="wb-theme-switch" role="group" aria-label="主题切换">
          <button
            :class="['wb-ts-btn', { active: !isBeautified }]"
            @click="setTheme('original')"
          >
            <el-icon><Sunny /></el-icon><span>原版主题</span>
          </button>
          <button
            :class="['wb-ts-btn', { active: isBeautified }]"
            @click="setTheme('beautified')"
          >
            <el-icon><MagicStick /></el-icon><span>美化主题</span>
          </button>
        </div>
      </div>
    </el-header>

    <el-container class="wb-body">
      <!-- 美化：侧边栏（深色渐变 + 图标 + 可折叠） -->
      <el-aside v-if="isBeautified" :width="collapse ? '64px' : '220px'" class="wb-sidebar">
        <div class="wb-sidebar-logo">
          <el-icon><Box /></el-icon>
          <span v-show="!collapse">WMS</span>
        </div>
        <el-menu
          :default-active="route.path"
          router
          class="wb-smenu"
          :collapse="collapse"
          :collapse-transition="false"
        >
          <el-menu-item v-for="m in beautifiedMenus" :key="m.path" :index="m.path">
            <el-icon><component :is="m.icon" /></el-icon>
            <template #title>{{ m.title }}</template>
          </el-menu-item>
        </el-menu>
        <div class="wb-sidebar-collapse" @click="collapse = !collapse">
          <el-icon><component :is="collapse ? Expand : Fold" /></el-icon>
        </div>
      </el-aside>

      <el-main class="wb-main" :class="{ beautified: isBeautified }">
        <div class="wb-view-wrap">
          <router-view v-slot="{ Component }">
            <transition name="wb-fade" mode="out-in">
              <keep-alive>
                <component :is="Component" />
              </keep-alive>
            </transition>
          </router-view>
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', Arial, sans-serif;
}
.wb-brand {
  display: flex;
  align-items: center;
}
.wb-brand-text {
  font-weight: 700;
  font-size: 18px;
  white-space: nowrap;
}
.wb-brand-logo {
  font-size: 22px;
  margin-right: 8px;
}
/* 原版顶栏下品牌文字反白 */
.wb-topbar.original .wb-brand-text {
  color: #fff;
}
.wb-topbar.original .wb-brand-logo {
  color: #fff;
}
.wb-topbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
}
.wb-sidebar-collapse {
  position: absolute;
  bottom: 16px;
  left: 0;
  right: 0;
  text-align: center;
  color: var(--app-sidebar-text, #cbd5e1);
  cursor: pointer;
  padding: 8px 0;
}
.wb-sidebar-collapse:hover {
  color: #fff;
}
</style>
