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
import Tree from './views/Tree.vue'
import Matrix from './views/Matrix.vue'
import Mda from './views/Mda.vue'
import Pdpc from './views/Pdpc.vue'
import Arrow from './views/Arrow.vue'
import History from './views/History.vue'
import Projects from './views/Projects.vue'
import ProjectDetail from './views/ProjectDetail.vue'
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
    { path: '/tools/tree',      component: Tree      },
    { path: '/tools/matrix',    component: Matrix    },
    { path: '/tools/mda',       component: Mda       },
    { path: '/tools/pdpc',      component: Pdpc      },
    { path: '/tools/arrow',     component: Arrow     },
    { path: '/history',  component: History },
    { path: '/projects',        component: Projects },
    { path: '/projects/:id',    component: ProjectDetail },
    { path: '/brand',    component: Brand },
    { path: '/settings', component: Settings }
  ]
})
