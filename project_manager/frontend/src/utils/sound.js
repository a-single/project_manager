let ctx = null

// 双音提示音（Web Audio 合成，无需音频文件）
export function playNotifySound() {
  try {
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)()
    if (ctx.state === 'suspended') ctx.resume()
    const now = ctx.currentTime
    const freqs = [880, 660]
    freqs.forEach((f, i) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = f
      osc.connect(gain)
      gain.connect(ctx.destination)
      const start = now + i * 0.18
      gain.gain.setValueAtTime(0.0001, start)
      gain.gain.exponentialRampToValueAtTime(0.3, start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, start + 0.4)
      osc.start(start)
      osc.stop(start + 0.4)
    })
  } catch (e) {
    /* 浏览器限制自动播放时忽略 */
  }
}