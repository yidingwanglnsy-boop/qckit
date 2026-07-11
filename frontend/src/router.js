import { createRouter, createWebHashHistory } from 'vue-router'
import Home from './views/Home.vue'
import Relations from './views/Relations.vue'
import Affinity from './views/Affinity.vue'
import Pareto from './views/Pareto.vue'
import Radar from './views/Radar.vue'
import W5H2 from './views/W5H2.vue'
import Rca from './views/Rca.vue'
import Fishbone from './views/Fishbone.vue'
import QccGuide from './views/QccGuide.vue'
import Brand from './views/Brand.vue'
import Settings from './views/Settings.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/tools/relations', component: Relations },
    { path: '/tools/affinity',  component: Affinity  },
    { path: '/tools/pareto',    component: Pareto    },
    { path: '/tools/radar',     component: Radar     },
    { path: '/tools/w5h2',      component: W5H2      },
    { path: '/tools/rca',       component: Rca       },
    { path: '/tools/fishbone',  component: Fishbone  },
    { path: '/tools/qcc-guide', component: QccGuide  },
    { path: '/brand',    component: Brand },
    { path: '/settings', component: Settings }
  ]
})
