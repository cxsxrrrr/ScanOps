import { useState, useEffect, useCallback } from 'react'

const THEME_KEY = 'vigia-theme'

function getInitialTheme() {
    if (typeof window === 'undefined') return 'dark'
    const stored = localStorage.getItem(THEME_KEY)
    if (stored === 'dark' || stored === 'light') return stored
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(theme) {
    const root = document.documentElement
    if (theme === 'dark') {
        root.classList.add('dark')
        root.classList.remove('light')
    } else {
        root.classList.add('light')
        root.classList.remove('dark')
    }
    localStorage.setItem(THEME_KEY, theme)
}

export function useTheme() {
    const [theme, setThemeState] = useState(getInitialTheme)

    useEffect(() => {
        applyTheme(theme)
    }, [theme])

    const toggleTheme = useCallback(() => {
        setThemeState(prev => prev === 'dark' ? 'light' : 'dark')
    }, [])

    const setTheme = useCallback((t) => {
        setThemeState(t)
    }, [])

    return {
        theme,
        isDark: theme === 'dark',
        toggleTheme,
        setTheme,
    }
}