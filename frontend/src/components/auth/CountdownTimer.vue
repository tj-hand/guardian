<script setup lang="ts">
import { computed } from 'vue'

/**
 * Countdown Timer Component
 *
 * Displays a countdown timer with visual states:
 * - Normal: Blue/default color (> 30 seconds)
 * - Warning: Orange/yellow color (1-30 seconds)
 * - Expired: Red color (0 seconds)
 *
 * Accessible with ARIA labels for screen readers
 */

// Props
interface Props {
  timeRemaining: number
  isLowTime?: boolean
  isExpired?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLowTime: false,
  isExpired: false
})

// Computed classes and labels
const timerClass = computed(() => {
  if (props.isExpired) return 'timer-expired'
  if (props.isLowTime) return 'timer-warning'
  return 'timer-normal'
})

const icon = computed(() => {
  if (props.isExpired) return '⚠️'
  if (props.isLowTime) return '⏱️'
  return '⏱️'
})

const ariaLabel = computed(() => {
  const minutes = Math.floor(props.timeRemaining / 60)
  const seconds = props.timeRemaining % 60

  if (props.isExpired) {
    return 'Token expired'
  }

  const minuteText = minutes === 1 ? '1 minute' : `${minutes} minutes`
  const secondText = seconds === 1 ? '1 second' : `${seconds} seconds`

  if (minutes > 0 && seconds > 0) {
    return `Time remaining: ${minuteText} and ${secondText}`
  } else if (minutes > 0) {
    return `Time remaining: ${minuteText}`
  } else {
    return `Time remaining: ${secondText}`
  }
})

const formattedTime = computed(() => {
  const minutes = Math.floor(props.timeRemaining / 60)
  const seconds = props.timeRemaining % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})
</script>

<template>
  <div class="countdown-timer" :class="timerClass" role="timer" :aria-label="ariaLabel" aria-live="polite">
    <span class="timer-icon">{{ icon }}</span>
    <span class="timer-text">
      <span v-if="isExpired" class="expired-text">Token expired</span>
      <span v-else>Time remaining: <strong>{{ formattedTime }}</strong></span>
    </span>
  </div>
</template>

<style scoped>
.countdown-timer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  margin-bottom: 1rem;
}

.timer-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.timer-text {
  font-weight: 500;
}

.timer-text strong {
  font-weight: 700;
  font-size: 1.05rem;
}

/* Normal state (> 30 seconds) */
.timer-normal {
  background-color: var(--color-info-bg, #d1ecf1);
  color: var(--color-info-text, #0c5460);
  border: 1px solid var(--color-info-border, #bee5eb);
}

/* Warning state (1-30 seconds) */
.timer-warning {
  background-color: var(--color-warning-bg, #fff3cd);
  color: var(--color-warning-text, #856404);
  border: 1px solid var(--color-warning-border, #ffeaa7);
  animation: pulse-warning 1.5s ease-in-out infinite;
}

/* Expired state (0 seconds) */
.timer-expired {
  background-color: var(--color-error-bg, #f8d7da);
  color: var(--color-error-text, #721c24);
  border: 1px solid var(--color-error-border, #f5c6cb);
}

.expired-text {
  font-weight: 700;
}

/* Warning pulse animation */
@keyframes pulse-warning {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.85;
  }
}

/* Responsive design */
@media (max-width: 480px) {
  .countdown-timer {
    font-size: 0.875rem;
    padding: 0.625rem 0.875rem;
  }

  .timer-icon {
    font-size: 1.1rem;
  }

  .timer-text strong {
    font-size: 1rem;
  }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .timer-normal {
    border-width: 2px;
  }

  .timer-warning {
    border-width: 2px;
  }

  .timer-expired {
    border-width: 2px;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .timer-warning {
    animation: none;
  }

  .countdown-timer {
    transition: none;
  }
}
</style>
