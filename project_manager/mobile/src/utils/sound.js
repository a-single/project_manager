let ctx = null

/** 在用户首次触摸/点击时调用，解锁移动端 WebView 的音频自动播放限制 */
export function unlockAudio() {
  try {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext
      if (!AC) return
      ctx = new AC()
    }
    if (ctx.state === 'suspended') ctx.resume()
  } catch {
    /* 忽略解锁失败 */
  }
}

/** 播放一段极短的静音，进一步激活 AudioContext（配合 unlockAudio 使用） */
export function primeAudio() {
  try {
    unlockAudio()
    if (!ctx) return
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    gain.gain.value = 0.0001
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.05)
  } catch {
    /* 忽略 */
  }
}

export function playNotifySound() {
  try {
    unlockAudio()
    if (!ctx) return
    const t0 = ctx.currentTime
    const mk = (freq, start, dur, vol = 0.35) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0.0001, t0 + start)
      gain.gain.exponentialRampToValueAtTime(vol, t0 + start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, t0 + start + dur)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(t0 + start)
      osc.stop(t0 + start + dur + 0.05)
    }
    // 轻快双音提醒
    mk(880, 0, 0.16)
    mk(1174.7, 0.18, 0.22)
  } catch {
    /* 忽略声音失败 */
  }
}