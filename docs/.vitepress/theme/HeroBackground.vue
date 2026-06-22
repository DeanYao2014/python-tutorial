<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const canvasRef = ref(null)
let ctx, w, h, raf, time = 0
let mouse = { x: -500, y: -500 }
let particles = []
let hero = null
let observer = null

const CONFIG = {
  particleCount: 110,
  connectionDist: 170,
  baseLineWidth: 0.9,
  particleBaseRadius: 2.6,
  speed: 0.22,
  mouseRadius: 210,
  mouseForce: 0.45
}

function isDark() {
  return document.documentElement.classList.contains('dark')
}

function createParticle(seed) {
  return {
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * CONFIG.speed,
    vy: (Math.random() - 0.5) * CONFIG.speed,
    radius: Math.random() * CONFIG.particleBaseRadius + 1.0,
    // 25% warm yellow (Python accent), 75% blue range
    hue: Math.random() < 0.25 ? 40 + Math.random() * 15 : 210 + Math.random() * 35,
    // Mark ~12% as "bright nodes" — larger, glowier
    bright: Math.random() < 0.12,
    phase: Math.random() * Math.PI * 2
  }
}

function initParticles() {
  particles = Array.from({ length: CONFIG.particleCount }, (_, i) => createParticle(i))
}

function drawGlow(p, alpha) {
  const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 3.5)
  const color = `hsla(${p.hue}, 60%, ${isDark() ? 65 : 40}%, ${alpha})`
  glow.addColorStop(0, color)
  glow.addColorStop(1, 'transparent')
  ctx.fillStyle = glow
  ctx.beginPath()
  ctx.arc(p.x, p.y, p.radius * 3.5, 0, Math.PI * 2)
  ctx.fill()
}

function animate() {
  if (!ctx) return
  time += 0.016
  const dark = isDark()

  ctx.clearRect(0, 0, w, h)

  // Update & draw connections
  for (let i = 0; i < particles.length; i++) {
    const p = particles[i]

    // Mouse interaction
    const dxM = p.x - mouse.x
    const dyM = p.y - mouse.y
    const distM = Math.sqrt(dxM * dxM + dyM * dyM)
    if (distM < CONFIG.mouseRadius && distM > 1) {
      const force = (1 - distM / CONFIG.mouseRadius) * CONFIG.mouseForce
      p.vx += (dxM / distM) * force
      p.vy += (dyM / distM) * force
    }

    // Subtle sinusoidal drift for organic feel
    p.vx += Math.sin(time * 0.5 + p.phase) * 0.003
    p.vy += Math.cos(time * 0.6 + p.phase) * 0.003

    p.vx *= 0.997
    p.vy *= 0.997

    // Clamp speed
    const spd = Math.sqrt(p.vx * p.vx + p.vy * p.vy)
    if (spd > CONFIG.speed * 2.5) {
      p.vx = (p.vx / spd) * CONFIG.speed * 2
      p.vy = (p.vy / spd) * CONFIG.speed * 2
    }

    p.x += p.vx
    p.y += p.vy

    // Wrap
    if (p.x < -40) p.x = w + 40
    if (p.x > w + 40) p.x = -40
    if (p.y < -40) p.y = h + 40
    if (p.y > h + 40) p.y = -40

    // Draw connections
    for (let j = i + 1; j < particles.length; j++) {
      const q = particles[j]
      const cdx = p.x - q.x
      const cdy = p.y - q.y
      const cdist = Math.sqrt(cdx * cdx + cdy * cdy)
      if (cdist < CONFIG.connectionDist) {
        const t = 1 - cdist / CONFIG.connectionDist
        const alpha = t * t * (dark ? 0.55 : 0.42)
        const hue = (p.hue + q.hue) / 2
        ctx.strokeStyle = dark
          ? `hsla(${hue}, 50%, 62%, ${alpha})`
          : `hsla(${hue}, 45%, 40%, ${alpha})`
        ctx.lineWidth = CONFIG.baseLineWidth * t
        ctx.beginPath()
        ctx.moveTo(p.x, p.y)
        ctx.lineTo(q.x, q.y)
        ctx.stroke()
      }
    }
  }

  // Draw particles (glow first, then core)
  for (const p of particles) {
    const sat = dark ? '50%' : '45%'
    const lit = dark ? '65%' : '38%'
    const baseAlpha = p.bright ? 0.65 : 0.45

    // Glow aura (always)
    drawGlow(p, baseAlpha)

    // Solid core
    ctx.fillStyle = `hsla(${p.hue}, ${sat}, ${lit}, 0.92)`
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
    ctx.fill()

    // Bright nodes get extra inner highlight
    if (p.bright) {
      ctx.fillStyle = `hsla(${p.hue}, 30%, 90%, 0.7)`
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.radius * 0.4, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  raf = requestAnimationFrame(animate)
}

function handleResize() {
  const canvas = canvasRef.value
  if (!canvas || !hero) return
  const rect = hero.getBoundingClientRect()
  w = rect.width
  h = rect.height
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = w * dpr
  canvas.height = h * dpr
  canvas.style.width = w + 'px'
  canvas.style.height = h + 'px'
  ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
}

function handleMouse(e) {
  if (!hero) return
  const rect = hero.getBoundingClientRect()
  mouse.x = e.clientX - rect.left
  mouse.y = e.clientY - rect.top
}

onMounted(async () => {
  await nextTick()
  const canvas = canvasRef.value
  if (!canvas) return

  hero = document.querySelector('.VPHero')
  if (hero) {
    hero.style.position = 'relative'
    hero.style.overflow = 'hidden'
    hero.insertBefore(canvas, hero.firstChild)
  }

  handleResize()
  initParticles()
  animate()

  window.addEventListener('resize', handleResize)
  window.addEventListener('mousemove', handleMouse, { passive: true })

  observer = new MutationObserver(() => {})
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onUnmounted(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', handleMouse)
  if (observer) observer.disconnect()
})
</script>

<template>
  <canvas
    ref="canvasRef"
    class="hero-canvas"
    aria-hidden="true"
  />
</template>

<style scoped>
.hero-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}
</style>
