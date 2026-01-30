import { defineConfig } from 'vitepress'
import config from '../../config.json'

export default defineConfig({
  title: config.name,
  description: `${config.tagline} ${config.description}`,

  base: '/',

  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }]
  ],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Guide', link: '/guide/getting-started' },
      { text: 'Exercises', link: '/exercises/' },
      { text: 'GitHub', link: 'https://github.com/Flow-Club/vibereps' }
    ],

    sidebar: [
      {
        text: 'Introduction',
        items: [
          { text: 'What is VibeReps?', link: '/' },
          { text: 'Getting Started', link: '/guide/getting-started' }
        ]
      },
      {
        text: 'Configuration',
        items: [
          { text: 'Basic Setup', link: '/guide/configuration' },
          { text: 'Hooks', link: '/guide/hooks' },
          { text: 'Customization', link: '/guide/customization' }
        ]
      },
      {
        text: 'Exercises',
        items: [
          { text: 'Overview', link: '/exercises/' },
          { text: 'Adding Exercises', link: '/exercises/adding-exercises' },
          { text: 'Detection Tuning', link: '/exercises/tuning' }
        ]
      },
      {
        text: 'Advanced',
        items: [
          { text: 'Architecture', link: '/advanced/architecture' },
          { text: 'Remote Server', link: '/advanced/server' },
          { text: 'Usage Tracking', link: '/advanced/monitoring' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Flow-Club/vibereps' },
      { icon: 'x', link: 'https://x.com/vibereps' }
    ],

    footer: {
      message: 'Stay healthy and keep coding!',
      copyright: 'Made with 💪 by <a href="https://www.flow.club" target="_blank">Flow Club</a>'
    },

    search: {
      provider: 'local'
    }
  }
})
