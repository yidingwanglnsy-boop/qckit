import { createRouter, createWebHashHistory } from 'vue-router'
import Home from './views/Home.vue'
import Relations from './views/Relations.vue'
import Affinity from './views/Affinity.vue'
import Pareto from './views/Pareto.vue'
import Settings from './views/Settings.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/tools/relations', component: Relations },
    { path: '/tools/affinity',  component: Affinity  },
    { path: '/tools/pareto',    component: Pareto    },
    { path: '/settings', component: Settings }
  ]
})
