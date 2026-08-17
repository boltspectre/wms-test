import axios from 'axios'
import { ElNotification } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器：成功统一提取 data；失败在**右上角弹出通知**（ElNotification 默认位置即右上角）
api.interceptors.response.use(
  (res) => res.data,
  (error) => {
    // 优先取 FastAPI 的 detail，其次业务 message，最后网络错误
    const data = error.response?.data
    const msg = data?.detail || data?.message || error.message || '网络错误'
    ElNotification.error({
      title: '操作失败',
      message: String(msg),
      duration: 4000,
    })
    console.error('API Error:', msg)
    return Promise.reject(error)
  }
)

export default api
