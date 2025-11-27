import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useTokenTimer } from '@/composables/useTokenTimer'

describe('useTokenTimer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('initializes with default duration (120 seconds)', () => {
    const { timeRemaining, isRunning, isExpired, isLowTime } = useTokenTimer()

    expect(timeRemaining.value).toBe(120)
    expect(isRunning.value).toBe(false)
    expect(isExpired.value).toBe(false)
    expect(isLowTime.value).toBe(false)
  })

  it('starts timer with default duration', () => {
    const { timeRemaining, isRunning, startTimer } = useTokenTimer()

    startTimer()

    expect(timeRemaining.value).toBe(120)
    expect(isRunning.value).toBe(true)
  })

  it('starts timer with custom duration', () => {
    const { timeRemaining, isRunning, startTimer } = useTokenTimer()

    startTimer(60)

    expect(timeRemaining.value).toBe(60)
    expect(isRunning.value).toBe(true)
  })

  it('counts down every second', () => {
    const { timeRemaining, startTimer } = useTokenTimer()

    startTimer(120)
    expect(timeRemaining.value).toBe(120)

    // Advance time by 1 second
    vi.advanceTimersByTime(1000)
    expect(timeRemaining.value).toBe(119)

    // Advance time by 5 more seconds
    vi.advanceTimersByTime(5000)
    expect(timeRemaining.value).toBe(114)
  })

  it('sets isLowTime to true when time is 30 seconds or less', () => {
    const { timeRemaining, isLowTime, startTimer } = useTokenTimer()

    startTimer(35)
    expect(isLowTime.value).toBe(false)

    // Advance to 30 seconds
    vi.advanceTimersByTime(5000)
    expect(timeRemaining.value).toBe(30)
    expect(isLowTime.value).toBe(true)

    // Advance to 15 seconds
    vi.advanceTimersByTime(15000)
    expect(timeRemaining.value).toBe(15)
    expect(isLowTime.value).toBe(true)
  })

  it('sets isExpired to true when time reaches 0', () => {
    const { timeRemaining, isExpired, isRunning, startTimer } = useTokenTimer()

    startTimer(3)
    expect(isExpired.value).toBe(false)

    // Advance to 0
    vi.advanceTimersByTime(3000)
    expect(timeRemaining.value).toBe(0)
    expect(isExpired.value).toBe(true)

    // Timer should stop automatically
    expect(isRunning.value).toBe(false)
  })

  it('does not go below 0', () => {
    const { timeRemaining, startTimer } = useTokenTimer()

    startTimer(2)

    // Advance past expiration
    vi.advanceTimersByTime(5000)
    expect(timeRemaining.value).toBe(0)
  })

  it('formats time correctly as MM:SS', () => {
    const { formattedTime, startTimer } = useTokenTimer()

    startTimer(125)
    expect(formattedTime.value).toBe('2:05')

    vi.advanceTimersByTime(5000)
    expect(formattedTime.value).toBe('2:00')

    vi.advanceTimersByTime(60000)
    expect(formattedTime.value).toBe('1:00')

    vi.advanceTimersByTime(55000)
    expect(formattedTime.value).toBe('0:05')
  })

  it('formats single digit seconds with leading zero', () => {
    const { formattedTime, startTimer } = useTokenTimer()

    startTimer(9)
    expect(formattedTime.value).toBe('0:09')

    vi.advanceTimersByTime(2000)
    expect(formattedTime.value).toBe('0:07')
  })

  it('stops the timer', () => {
    const { timeRemaining, isRunning, startTimer, stopTimer } = useTokenTimer()

    startTimer(60)
    expect(isRunning.value).toBe(true)

    vi.advanceTimersByTime(5000)
    expect(timeRemaining.value).toBe(55)

    stopTimer()
    expect(isRunning.value).toBe(false)

    // Time should not advance after stopping
    vi.advanceTimersByTime(5000)
    expect(timeRemaining.value).toBe(55)
  })

  it('resets the timer without starting', () => {
    const { timeRemaining, isRunning, startTimer, resetTimer } = useTokenTimer()

    startTimer(60)
    vi.advanceTimersByTime(20000)
    expect(timeRemaining.value).toBe(40)
    expect(isRunning.value).toBe(true)

    resetTimer()
    expect(timeRemaining.value).toBe(120) // Default duration
    expect(isRunning.value).toBe(false)
  })

  it('resets the timer with custom duration', () => {
    const { timeRemaining, isRunning, startTimer, resetTimer } = useTokenTimer()

    startTimer(60)
    vi.advanceTimersByTime(20000)

    resetTimer(90)
    expect(timeRemaining.value).toBe(90)
    expect(isRunning.value).toBe(false)
  })

  it('returns current time remaining via getTimeRemaining', () => {
    const { getTimeRemaining, startTimer } = useTokenTimer()

    startTimer(100)
    expect(getTimeRemaining()).toBe(100)

    vi.advanceTimersByTime(25000)
    expect(getTimeRemaining()).toBe(75)
  })

  it('stops existing timer when starting a new one', () => {
    const { timeRemaining, startTimer } = useTokenTimer()

    startTimer(60)
    vi.advanceTimersByTime(10000)
    expect(timeRemaining.value).toBe(50)

    // Start a new timer
    startTimer(120)
    expect(timeRemaining.value).toBe(120)

    vi.advanceTimersByTime(10000)
    expect(timeRemaining.value).toBe(110)
  })

  it('cleans up timer on unmount', () => {
    const { startTimer, stopTimer } = useTokenTimer()

    startTimer(60)

    // Simulate component unmount by calling stopTimer
    stopTimer()

    // Verify timer is stopped
    expect(vi.getTimerCount()).toBe(0)
  })

  it('handles rapid start/stop calls', () => {
    const { timeRemaining, isRunning, startTimer, stopTimer } = useTokenTimer()

    startTimer(60)
    stopTimer()
    startTimer(120)
    stopTimer()
    startTimer(30)

    expect(timeRemaining.value).toBe(30)
    expect(isRunning.value).toBe(true)

    vi.advanceTimersByTime(5000)
    expect(timeRemaining.value).toBe(25)
  })

  it('isLowTime is false when expired', () => {
    const { isLowTime, isExpired, startTimer } = useTokenTimer()

    startTimer(1)
    expect(isLowTime.value).toBe(true)

    vi.advanceTimersByTime(1000)
    expect(isExpired.value).toBe(true)
    expect(isLowTime.value).toBe(false) // isLowTime requires time > 0
  })
})
