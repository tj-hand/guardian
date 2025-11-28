import { ref, computed, onUnmounted as vueOnUnmounted, getCurrentInstance } from 'vue'

/**
 * Token expiration timer composable
 *
 * Provides countdown timer functionality for token validation with:
 * - Configurable duration (default 120 seconds / 2 minutes)
 * - Real-time countdown updates every second
 * - Warning state for low time (< 30 seconds)
 * - Expired state when time reaches 0
 * - Formatted time display (MM:SS)
 * - Proper cleanup on component unmount
 */
export function useTokenTimer() {
  // Constants
  const DEFAULT_DURATION = 120 // 2 minutes in seconds
  const LOW_TIME_THRESHOLD = 30 // Warning threshold in seconds

  // Reactive state
  const timeRemaining = ref<number>(DEFAULT_DURATION)
  const isRunning = ref<boolean>(false)

  // Internal timer reference
  let intervalId: ReturnType<typeof setInterval> | null = null

  // Computed properties
  const isLowTime = computed(() => timeRemaining.value > 0 && timeRemaining.value <= LOW_TIME_THRESHOLD)
  const isExpired = computed(() => timeRemaining.value <= 0)

  const formattedTime = computed(() => {
    const minutes = Math.floor(timeRemaining.value / 60)
    const seconds = timeRemaining.value % 60
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  })

  /**
   * Start the countdown timer
   * @param duration - Optional duration in seconds (defaults to 120)
   */
  const startTimer = (duration: number = DEFAULT_DURATION): void => {
    // Stop any existing timer first
    stopTimer()

    // Initialize time
    timeRemaining.value = duration
    isRunning.value = true

    // Start countdown interval
    intervalId = setInterval(() => {
      if (timeRemaining.value > 0) {
        timeRemaining.value--

        // Check if timer just reached 0
        if (timeRemaining.value === 0) {
          // Timer expired, stop it
          isRunning.value = false
          if (intervalId !== null) {
            clearInterval(intervalId)
            intervalId = null
          }
        }
      }
    }, 1000)
  }

  /**
   * Stop the countdown timer
   */
  const stopTimer = (): void => {
    if (intervalId !== null) {
      clearInterval(intervalId)
      intervalId = null
    }
    isRunning.value = false
  }

  /**
   * Reset the timer to initial state without starting
   */
  const resetTimer = (duration: number = DEFAULT_DURATION): void => {
    stopTimer()
    timeRemaining.value = duration
  }

  /**
   * Get current time remaining in seconds
   */
  const getTimeRemaining = (): number => {
    return timeRemaining.value
  }

  // Cleanup on component unmount (only if called within a component)
  if (getCurrentInstance()) {
    vueOnUnmounted(() => {
      stopTimer()
    })
  }

  return {
    // Reactive state
    timeRemaining,
    isRunning,

    // Computed properties
    isLowTime,
    isExpired,
    formattedTime,

    // Methods
    startTimer,
    stopTimer,
    resetTimer,
    getTimeRemaining
  }
}
