import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString) {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleDateString('es-VE', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function getSeverityColor(severity) {
  const colors = {
    HIGH: 'severity-high',
    MEDIUM: 'severity-medium',
    LOW: 'severity-low',
    INFO: 'severity-info',
  }
  return colors[severity] || 'severity-info'
}

export function getSeverityLabel(severity) {
  const labels = {
    HIGH: 'Alto',
    MEDIUM: 'Medio',
    LOW: 'Bajo',
    INFO: 'Info',
  }
  return labels[severity] || severity
}

export function getStatusColor(status) {
  const colors = {
    pending: 'text-yellow-400',
    running: 'text-blue-400',
    completed: 'text-green-400',
    ok: 'text-green-400',
    warning: 'text-amber-400',
    error: 'text-red-400',
  }
  return colors[status] || 'text-gray-400'
}

export function getStatusLabel(status) {
  const labels = {
    pending: 'Pendiente',
    running: 'En progreso',
    completed: 'Completado',
    ok: 'OK',
    warning: 'Advertencia',
    error: 'Error',
  }
  return labels[status] || status
}
