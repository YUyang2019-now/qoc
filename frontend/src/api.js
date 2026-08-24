import axios from 'axios'

const api = axios.create({
  baseURL: '',
  withCredentials: true,
  timeout: 0
})

export function downloadFile(url) {
  return api.get(url, { responseType: 'blob' })
}

export default api
