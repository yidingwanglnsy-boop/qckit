/**
 * 挂靠到项目容器的通用逻辑 —— 供 8 个老 view 和 ToolPage 骨架复用。
 *
 * 调用: await tryAttachToProject('fishbone', formSnapshot, resultObj)
 * 若 sessionStorage 有 qckit.attach_target 则挂上, 否则静默返回。
 */
import { ElMessage } from 'element-plus'
import { attachToProject } from '../api'

export async function tryAttachToProject (toolKey, snapshot, result) {
  const raw = sessionStorage.getItem('qckit.attach_target')
  if (!raw) return false
  try {
    const t = JSON.parse(raw)
    await attachToProject(t.project_id, {
      tool: toolKey,
      snapshot: JSON.parse(JSON.stringify(snapshot || {})),
      result: result || {},
      stage: t.stage,
    })
    sessionStorage.removeItem('qckit.attach_target')
    ElMessage.success(`已挂到项目「${t.project_name}」`)
    return true
  } catch (e) {
    console.warn('[attach] failed', e)
    return false
  }
}
