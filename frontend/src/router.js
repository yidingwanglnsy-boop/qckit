import { createRouter, createWebHashHistory } from 'vue-router'
import Home from './views/Home.vue'
import Relations from './views/Relations.vue'
import Settings from './views/Settings.vue'

export default createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home },
    { path: '/tools/relations', component: Relations },
    { path: '/settings', component: Settings }
  ]
})
