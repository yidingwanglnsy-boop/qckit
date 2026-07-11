<template>
  <div class="qc-page">
    <!-- 顶部：标题 + 当前配置状态 -->
    <div class="hero">
      <div>
        <div class="hero-title">🤖 大模型接入配置</div>
        <div class="hero-sub">跟着 3 步走，5 分钟接入 AI，之后所有 QC 工具都能用</div>
      </div>
      <div class="hero-status">
        <div class="dot" :class="{ ok: hasConfig, warn: !hasConfig }"></div>
        <div v-if="hasConfig">
          <div class="status-hd">✅ 已配置</div>
          <div class="status-sub">{{ currentProviderName }} · {{ savedConfig.model || '未指定模型' }}</div>
        </div>
        <div v-else>
          <div class="status-hd">⚠️ 还没配置</div>
          <div class="status-sub">下面选一家开始</div>
        </div>
      </div>
    </div>

    <!-- 步骤 1：选平台 -->
    <div class="step-card">
      <div class="step-hd">
        <div class="step-num">1</div>
        <div>
          <div class="step-title">选一家 AI 平台</div>
          <div class="step-hint">不知道选哪家？→ 国内用户推荐 <b>阿里百炼</b>（新用户免费额度多，速度快）</div>
        </div>
      </div>
      <div class="provider-grid">
        <div v-for="p in providers" :key="p.key"
             class="provider-card" :class="{ active: pickedKey === p.key }"
             @click="pickProvider(p)">
          <div class="provider-badge" v-if="p.recommended">推荐</div>
          <div class="provider-emoji">{{ p.emoji }}</div>
          <div class="provider-name">{{ p.name }}</div>
          <div class="provider-desc">{{ p.tagline }}</div>
        </div>
      </div>
    </div>

    <!-- 步骤 2：按平台的傻瓜指南 -->
    <div class="step-card" v-if="picked">
      <div class="step-hd">
        <div class="step-num">2</div>
        <div>
          <div class="step-title">按下面步骤在 <b>{{ picked.name }}</b> 拿到 API Key 和 Model</div>
          <div class="step-hint">
            <a :href="picked.url" target="_blank" class="big-link">
              🚀 打开 {{ picked.name }} 官网 →
            </a>
          </div>
        </div>
      </div>

      <div class="steps-inner">
        <div v-for="(s, i) in picked.steps" :key="i" class="mini-step">
          <div class="mini-num">{{ i + 1 }}</div>
          <div class="mini-body">
            <div class="mini-text" v-html="s.text"></div>
            <div class="mini-tip" v-if="s.tip">💡 {{ s.tip }}</div>
          </div>
        </div>
      </div>

      <div class="pitfall" v-if="picked.pitfall">
        <b>⚠️ 特别注意：</b>{{ picked.pitfall }}
      </div>
    </div>

    <!-- 步骤 3：填 3 个格 -->
    <div class="step-card" v-if="picked">
      <div class="step-hd">
        <div class="step-num">3</div>
        <div>
          <div class="step-title">把拿到的信息填在下面，点保存</div>
          <div class="step-hint">填错也没关系，随时能回来改</div>
        </div>
      </div>

      <div class="form-grid">
        <div class="field">
          <label>
            🔑 API Key
            <span class="req">*必填</span>
          </label>
          <el-input v-model="form.api_key" :placeholder="apiKeyPlaceholder"
                    show-password autocomplete="off" size="large" />
          <div class="field-hint">在 {{ picked.name }} 官网复制的密钥（形如 sk-xxx…）</div>
        </div>

        <div class="field">
          <label>
            📦 Model {{ picked.key === 'volc' ? '（接入点 ID）' : '（模型名称）' }}
            <span class="req">*必填</span>
          </label>
          <el-input v-model="form.model" :placeholder="picked.model_hint" size="large" />
          <div class="field-hint" v-html="picked.model_hint_desc"></div>
        </div>

        <div class="field field-collapsed" v-if="showAdvanced">
          <label>Base URL（一般不用改）</label>
          <el-input v-model="form.base_url" size="large" />
          <div class="field-hint">点上面平台已自动填好</div>
        </div>

        <div class="field field-collapsed" v-if="showAdvanced">
          <label>Temperature（回答的稳定度）</label>
          <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" size="large" />
          <div class="field-hint">0.2 = 稳定（推荐）；0.7 = 更有创意；数值越大越发散</div>
        </div>
      </div>

      <div class="form-actions">
        <el-button link @click="showAdvanced = !showAdvanced">
          {{ showAdvanced ? '↑ 收起高级选项' : '⚙ 高级选项（Base URL / Temperature）' }}
        </el-button>
        <div style="flex:1;"></div>
        <el-button size="large" :disabled="!form.api_key || !form.model"
                   :loading="testing" @click="testConnection">
          <el-icon><Connection /></el-icon>&nbsp;测试连接
        </el-button>
        <el-button size="large" type="primary" :loading="saving"
                   :disabled="!form.api_key || !form.model" @click="save">
          <el-icon><Check /></el-icon>&nbsp;保存并启用
        </el-button>
      </div>

      <div class="result-box" v-if="testResult" :class="testResult.ok ? 'ok' : 'fail'">
        <b>{{ testResult.ok ? '✅ 连接成功' : '❌ 连接失败' }}</b>
        <div style="margin-top:4px;">{{ testResult.msg }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, saveConfig, api } from '../api'

const providers = [
  {
    key: 'bailian', name: '阿里百炼', emoji: '☁️',
    tagline: '阿里云 Qwen 系列 · 国内首选',
    recommended: true,
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    url: 'https://bailian.console.aliyun.com/',
    model_hint: 'qwen-plus',
    model_hint_desc: '常用：<code>qwen-plus</code>（推荐）、<code>qwen-max</code>（最强）、<code>qwen-turbo</code>（最快）',
    steps: [
      { text: '点击上面按钮打开百炼官网，用<b>支付宝或阿里云账号</b>登录', tip: '第一次会让你开通服务，一路确认就行' },
      { text: '左侧菜单找到 <b>"API-KEY"</b> → 点<b>"创建我的 API-KEY"</b>', tip: '创建后立刻复制保存，关掉页面就看不见了' },
      { text: '把复制的 Key（<code>sk-xxxx…</code>）粘贴到下面 <b>API Key</b> 输入框' },
      { text: 'Model 填 <code>qwen-plus</code>（不用去别的地方查，就用这个）' },
    ],
    pitfall: '百炼有两套 API 协议，我们已经帮你选好了 OpenAI 兼容模式，Base URL 不用改。',
  },
  {
    key: 'volc', name: '火山引擎', emoji: '🌋',
    tagline: '字节豆包 / DeepSeek / GLM 都能用',
    base_url: 'https://ark.cn-beijing.volces.com/api/v3',
    url: 'https://console.volcengine.com/ark',
    model_hint: 'ep-2024xxxxxx-xxxx',
    model_hint_desc: '⚠️ Model <b>不是</b>填"豆包-Pro"这种名字，而是填 <code>ep-xxx</code> 接入点 ID',
    steps: [
      { text: '点击上面按钮打开火山方舟，用<b>手机号/抖音</b>注册并实名认证' },
      { text: '左侧 <b>"在线推理"</b> → <b>"创建推理接入点"</b>，选一个模型（如"豆包-1.5-Pro"）', tip: '每选一个模型 = 一个独立的接入点' },
      { text: '创建完成后，会得到一个 <b>接入点 ID</b>（形如 <code>ep-20241228xxxxxx-xxxx</code>），复制它', tip: '这个 ID 就是下面要填的 Model' },
      { text: '左侧 <b>"API Key 管理"</b> → 创建 API Key，也复制' },
      { text: 'API Key 和接入点 ID 分别填到下面对应输入框' },
    ],
    pitfall: '火山最容易踩的坑：Model 一定要填 ep-xxx 那串 ID，不能填模型名字！',
  },
  {
    key: 'deepseek', name: 'DeepSeek', emoji: '🐋',
    tagline: '价格便宜、代码能力强',
    base_url: 'https://api.deepseek.com/v1',
    url: 'https://platform.deepseek.com/',
    model_hint: 'deepseek-chat',
    model_hint_desc: '常用：<code>deepseek-chat</code>（通用）、<code>deepseek-reasoner</code>（深度推理）',
    steps: [
      { text: '打开 DeepSeek 官网注册（手机号即可，无需实名）' },
      { text: '左侧 <b>"API keys"</b> → 创建新的 Key，复制' },
      { text: 'Model 填 <code>deepseek-chat</code>' },
    ],
    pitfall: '',
  },
  {
    key: 'moonshot', name: 'Kimi (Moonshot)', emoji: '🌙',
    tagline: '超长文本擅长（128K 上下文）',
    base_url: 'https://api.moonshot.cn/v1',
    url: 'https://platform.moonshot.cn/',
    model_hint: 'moonshot-v1-8k',
    model_hint_desc: '常用：<code>moonshot-v1-8k</code>、<code>-32k</code>、<code>-128k</code>（数字越大能读越长的文档）',
    steps: [
      { text: '打开 Kimi 开放平台注册' },
      { text: '左侧 <b>"API Key 管理"</b> → 新建，复制 Key' },
      { text: 'Model 填 <code>moonshot-v1-8k</code>（够用）' },
    ],
    pitfall: '',
  },
  {
    key: 'openai', name: 'OpenAI (GPT)', emoji: '🌐',
    tagline: '国际大厂，需科学上网',
    base_url: 'https://api.openai.com/v1',
    url: 'https://platform.openai.com/',
    model_hint: 'gpt-4o-mini',
    model_hint_desc: '常用：<code>gpt-4o-mini</code>（性价比）、<code>gpt-4o</code>（最强）',
    steps: [
      { text: '需要海外信用卡和魔法（大陆用户不推荐）' },
      { text: 'platform.openai.com → API keys → Create new secret key' },
    ],
    pitfall: '大陆网络无法直接访问，需要代理才能使用。',
  },
  {
    key: 'local', name: '本地模型', emoji: '💻',
    tagline: 'vLLM / Ollama 本地跑，无需 API Key',
    base_url: 'http://localhost:8000/v1',
    url: 'https://github.com/ollama/ollama',
    model_hint: 'qwen2.5:7b',
    model_hint_desc: '填你本地部署的模型名，如 Ollama 里的 <code>qwen2.5:7b</code>',
    steps: [
      { text: '本地已经用 Ollama 或 vLLM 跑起了模型' },
      { text: 'Base URL 改成你的服务地址（Ollama 默认 <code>http://localhost:11434/v1</code>）' },
      { text: 'API Key 随便填一个（如 <code>ollama</code>）' },
      { text: 'Model 填模型名（如 <code>qwen2.5:7b</code>）' },
    ],
    pitfall: '如果 QCKit 用 docker 部署，本地模型地址要用 <code>host.docker.internal</code> 而不是 localhost。',
  },
]

const form = ref({ base_url: '', api_key: '', model: '', temperature: 0.2, timeout: 120 })
const savedConfig = ref({})
const apiKeyPlaceholder = ref('sk-...')
const saving = ref(false)
const testing = ref(false)
const testResult = ref(null)
const showAdvanced = ref(false)
const pickedKey = ref('')     // 用户主动选择的平台 key，独立于 base_url

const picked = computed(() =>
  providers.find(p => p.key === pickedKey.value))
const hasConfig = computed(() =>
  !!(savedConfig.value.api_key && savedConfig.value.model))
const currentProviderName = computed(() => {
  const p = providers.find(x => x.base_url === savedConfig.value.base_url)
  return p ? p.name : '自定义'
})

onMounted(async () => {
  const cfg = await getConfig()
  savedConfig.value = { ...cfg.llm }
  Object.assign(form.value, cfg.llm)
  if (cfg.llm.api_key) apiKeyPlaceholder.value = cfg.llm.api_key   // 掩码
  form.value.api_key = ''
  // 已有配置时自动锚定到匹配的平台，找不到则默认百炼
  const match = providers.find(p => p.base_url === cfg.llm.base_url)
  pickedKey.value = match ? match.key : (cfg.llm.base_url ? '' : '')
})

function pickProvider(p) {
  pickedKey.value = p.key
  form.value.base_url = p.base_url
  testResult.value = null
}

async function save() {
  saving.value = true
  try {
    await saveConfig(form.value)
    ElMessage.success(`✅ 已保存，${picked.value?.name || 'AI'} 就绪`)
    const cfg = await getConfig()
    savedConfig.value = { ...cfg.llm }
    if (cfg.llm.api_key) apiKeyPlaceholder.value = cfg.llm.api_key
    form.value.api_key = ''
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally { saving.value = false }
}

async function testConnection() {
  testing.value = true; testResult.value = null
  try {
    // 先保存再测（后端只用已保存配置）
    await saveConfig(form.value)
    const r = await api.post('/tools/qcc_guide/analyze',
      { topic: '连接测试', experience: '新手', focus: '一句话' },
      { timeout: 30000 })
    testResult.value = {
      ok: true,
      msg: `AI 已响应，共生成 ${r.data.stages?.length || 0} 段思路。`,
    }
    const cfg = await getConfig()
    savedConfig.value = { ...cfg.llm }
    form.value.api_key = ''
  } catch (e) {
    testResult.value = {
      ok: false,
      msg: `${e.response?.data?.detail || e.message}（检查 API Key / Model / 网络）`,
    }
  } finally { testing.value = false }
}
</script>

<style scoped>
.qc-page { padding: 4px; max-width: 960px; margin: 0 auto; }

/* Hero */
.hero {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff; padding: 22px 26px; border-radius: 12px; margin-bottom: 14px;
  box-shadow: 0 4px 14px rgba(99,102,241,.25);
}
.hero-title { font-size: 20px; font-weight: 700; }
.hero-sub { font-size: 13px; opacity: .9; margin-top: 6px; }
.hero-status { display: flex; align-items: center; gap: 10px;
  background: rgba(255,255,255,.15); padding: 10px 14px; border-radius: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.ok { background: #34d399; box-shadow: 0 0 8px #34d399; }
.dot.warn { background: #fbbf24; }
.status-hd { font-size: 13px; font-weight: 600; }
.status-sub { font-size: 11.5px; opacity: .85; margin-top: 2px; }

/* Step card */
.step-card {
  background: #fff; border-radius: 12px; padding: 20px 24px;
  margin-bottom: 14px; border: 1px solid #eef2f7;
  box-shadow: 0 1px 3px rgba(0,0,0,.03);
}
.step-hd { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 16px; }
.step-num {
  background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #fff;
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 18px; flex-shrink: 0;
}
.step-title { font-size: 15.5px; font-weight: 700; color: #0f172a; }
.step-hint { font-size: 12.5px; color: #64748b; margin-top: 4px; line-height: 1.6; }
.big-link {
  color: #6366f1; font-weight: 600; text-decoration: none;
  font-size: 13.5px; padding: 4px 10px; background: #eef2ff;
  border-radius: 4px; display: inline-block; margin-top: 6px;
}
.big-link:hover { background: #e0e7ff; }

/* Provider grid */
.provider-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
@media (max-width: 720px) { .provider-grid { grid-template-columns: repeat(2, 1fr); } }
.provider-card {
  border: 2px solid #e5e7eb; border-radius: 10px; padding: 16px 14px;
  cursor: pointer; transition: all .15s; position: relative;
  background: #fff; text-align: center;
}
.provider-card:hover { border-color: #a78bfa; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,.06); }
.provider-card.active {
  border-color: #6366f1; background: linear-gradient(180deg, #f5f3ff, #fff);
  box-shadow: 0 0 0 3px rgba(99,102,241,.15);
}
.provider-badge {
  position: absolute; top: -8px; right: 12px;
  background: #f59e0b; color: #fff; font-size: 10px; font-weight: 700;
  padding: 2px 8px; border-radius: 10px;
}
.provider-emoji { font-size: 28px; line-height: 1; }
.provider-name { font-size: 14px; font-weight: 700; color: #0f172a; margin-top: 8px; }
.provider-desc { font-size: 11.5px; color: #64748b; margin-top: 4px; line-height: 1.4; }

/* Mini step (指南内的每一小步) */
.steps-inner { display: flex; flex-direction: column; gap: 12px; }
.mini-step { display: flex; gap: 12px; }
.mini-num {
  background: #eef2ff; color: #6366f1; font-weight: 700;
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; flex-shrink: 0;
}
.mini-body { flex: 1; padding-top: 2px; }
.mini-text { color: #334155; font-size: 13.5px; line-height: 1.75; }
.mini-text :deep(code) {
  background: #f1f5f9; padding: 1px 6px; border-radius: 3px;
  font-family: ui-monospace, monospace; font-size: 12px; color: #7c2d12;
}
.mini-tip { color: #78350f; font-size: 12px; margin-top: 4px;
  padding: 4px 10px; background: #fffbeb; border-radius: 4px; border-left: 3px solid #f59e0b; }

.pitfall {
  margin-top: 16px; background: #fef2f2; border: 1px solid #fecaca;
  padding: 12px 14px; border-radius: 6px; font-size: 12.5px;
  color: #7f1d1d; line-height: 1.7;
}

/* Form */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 720px) { .form-grid { grid-template-columns: 1fr; } }
.field label {
  display: block; font-size: 13px; font-weight: 600; color: #334155;
  margin-bottom: 6px;
}
.field .req { color: #dc2626; font-size: 11px; font-weight: 500; margin-left: 4px; }
.field-hint {
  color: #94a3b8; font-size: 11.5px; margin-top: 6px; line-height: 1.5;
}
.field-hint :deep(code) {
  background: #f1f5f9; padding: 1px 6px; border-radius: 3px;
  font-family: ui-monospace, monospace; font-size: 11px; color: #7c2d12;
}
.form-actions {
  display: flex; gap: 10px; margin-top: 20px; align-items: center;
  padding-top: 16px; border-top: 1px solid #f1f5f9;
}
.result-box {
  margin-top: 14px; padding: 12px 14px; border-radius: 6px;
  font-size: 13px; line-height: 1.6;
}
.result-box.ok { background: #f0fdf4; color: #14532d; border-left: 3px solid #22c55e; }
.result-box.fail { background: #fef2f2; color: #7f1d1d; border-left: 3px solid #dc2626; }
</style>
