/**
 * Valida CPF pelo algoritmo dos dígitos verificadores (módulo 11).
 * Retorna true se o CPF é válido (apenas números, 11 dígitos, dígitos corretos).
 */
export function isValidCpf(value: string): boolean {
  const digits = value.replace(/\D/g, '')
  if (digits.length !== 11) return false
  if (/^(\d)\1{10}$/.test(digits)) return false // todos iguais

  let sum = 0
  for (let i = 0; i < 9; i++) {
    sum += parseInt(digits[i], 10) * (10 - i)
  }
  let remainder = sum % 11
  const d1 = remainder < 2 ? 0 : 11 - remainder
  if (parseInt(digits[9], 10) !== d1) return false

  sum = 0
  for (let i = 0; i < 10; i++) {
    sum += parseInt(digits[i], 10) * (11 - i)
  }
  remainder = sum % 11
  const d2 = remainder < 2 ? 0 : 11 - remainder
  if (parseInt(digits[10], 10) !== d2) return false

  return true
}

/**
 * Formata uma string de dígitos como CPF: 000.000.000-00
 */
export function formatCpf(digits: string): string {
  const d = digits.replace(/\D/g, '').slice(0, 11)
  if (d.length <= 3) return d
  if (d.length <= 6) return `${d.slice(0, 3)}.${d.slice(3)}`
  if (d.length <= 9) return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`
  return `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`
}

/**
 * Retorna apenas os 11 dígitos do CPF (para envio à API).
 */
export function cpfDigits(value: string): string {
  return value.replace(/\D/g, '').slice(0, 11)
}
