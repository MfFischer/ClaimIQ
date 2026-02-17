/** @type {import('next').NextConfig} */
const nextConfig = {
  // PWA headers — service worker scope
  async headers() {
    return [
      {
        source: '/sw.js',
        headers: [
          { key: 'Cache-Control', value: 'no-cache' },
          { key: 'Content-Type', value: 'application/javascript; charset=utf-8' },
        ],
      },
    ]
  },
}

module.exports = nextConfig
