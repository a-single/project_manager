// 轻量提示：避免 WebView alert() 出现「网址为：xxxxx，网页显示：」前缀
let el = null
let timer = null

export function toast(msg, duration = 2000) {
  if (!el) {
    el = document.createElement('div')
    el.className = 'app-toast'
    document.body.appendChild(el)
  }
  el.textContent = msg
  el.classList.add('show')
  clearTimeout(timer)
  timer = setTimeout(() => el.classList.remove('show'), duration)
}