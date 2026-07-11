/**
 * 通用 CSV/XLSX 文件解析 —— 无后端往返, 纯前端 SheetJS + 手写 CSV。
 *
 * parseFile(file) → { rows: [[cell,...]], headers: [...] }
 *   自动嗅探 .csv/.xlsx, 首行作为 headers
 */
import * as XLSX from 'xlsx'

export async function parseFile (file) {
  const name = (file.name || '').toLowerCase()
  const buf = await file.arrayBuffer()
  if (name.endsWith('.csv')) {
    const text = new TextDecoder('utf-8').decode(buf)
    return parseCSV(text)
  }
  // xlsx / xls
  const wb = XLSX.read(buf, { type: 'array' })
  const sheet = wb.Sheets[wb.SheetNames[0]]
  const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' })
  return { rows, headers: rows[0] || [] }
}

function parseCSV (text) {
  const rows = []
  for (const line of text.split(/\r?\n/)) {
    if (!line.trim()) continue
    // 简单实现: 逗号或 tab 分, 支持双引号包裹
    const cells = []
    let cur = '', inQ = false
    for (let i = 0; i < line.length; i++) {
      const c = line[i]
      if (c === '"') { inQ = !inQ; continue }
      if (!inQ && (c === ',' || c === '\t')) { cells.push(cur); cur = ''; continue }
      cur += c
    }
    cells.push(cur)
    rows.push(cells)
  }
  return { rows, headers: rows[0] || [] }
}
