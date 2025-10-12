// ==================================
// frontend/next.config.js
// ==================================
/**
 * Next.js Production Configuration
 * Optimized for Vercel deployment
 * @type {import('next').NextConfig}
 */

const nextConfig = {
  // ==================================
  // PRODUCTION SETTINGS
  // ==================================
  reactStrictMode: true,
  swcMinify: true,  // Faster minification with SWC
  
  // ==================================
  // IMAGES OPTIMIZATION
  // ==================================
  images: {
    // Add your image CDN domains here
    domains: [
      // Add your domains that serve images
      // 'yourdomain.com',
      // 'api.yourdomain.com',
      // Vercel Blob domains (if using)
      // 'public.blob.vercel-storage.com',
    ],
    // Modern formats for better compression
    formats: ['image/avif', 'image/webp'],
    // Cache optimized images for 60 seconds
    minimumCacheTTL: 60,
    // Responsive image sizes
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  
  // ==================================
  // SECURITY HEADERS
  // ==================================
  async headers() {
    return [
      {
        // Apply headers to all routes
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()'
          },
        ],
      },
    ]
  },
  
  // ==================================
  // REDIRECTS (HTTP → HTTPS)
  // ==================================
  async redirects() {
    return [
      // Redirect non-www to www (or vice versa) - uncomment if needed
      // {
      //   source: '/:path*',
      //   has: [
      //     {
      //       type: 'host',
      //       value: 'yourdomain.com',  // without www
      //     },
      //   ],
      //   destination: 'https://www.yourdomain.com/:path*',
      //   permanent: true,
      // },
    ]
  },
  
  // ==================================
  // REWRITES (API PROXY - optional)
  // ==================================
  // Uncomment if you want to proxy backend requests through Next.js
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/backend/:path*',
  //       destination: `${process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL}/:path*`,
  //     },
  //   ]
  // },
  
  // ==================================
  // ENVIRONMENT VARIABLES
  // ==================================
  // Public env vars (exposed to browser)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_PYTHON_BACKEND_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
  
  // ==================================
  // WEBPACK CONFIGURATION
  // ==================================
  webpack: (config, { dev, isServer, webpack }) => {
    // Bundle analyzer (only if ANALYZE=true)
    if (process.env.ANALYZE === 'true' && !dev && !isServer) {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer')
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: './analyze.html',
          openAnalyzer: false,
        })
      )
    }
    
    // Ignore node modules that shouldn't be bundled
    config.externals = config.externals || []
    if (isServer) {
      config.externals.push('better-sqlite3')  // Don't bundle SQLite for server
    }
    
    return config
  },
  
  // ==================================
  // COMPILER OPTIONS
  // ==================================
  compiler: {
    // Remove console logs in production (keep errors & warnings)
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },
  
  // ==================================
  // EXPERIMENTAL FEATURES
  // ==================================
  experimental: {
    // Optimize CSS imports
    optimizeCss: true,
    // Optimize package imports to reduce bundle size
    optimizePackageImports: [
      'lucide-react',
      '@radix-ui/react-icons',
      'recharts',
      'chart.js',
    ],
  },
  
  // ==================================
  // OUTPUT
  // ==================================
  // 'standalone' for Docker deployment (optional)
  // output: 'standalone',
  
  // ==================================
  // PERFORMANCE
  // ==================================
  compress: true,  // Enable gzip compression
  poweredByHeader: false,  // Remove X-Powered-By header
  generateEtags: true,  // Generate ETags for caching
  
  // ==================================
  // TYPESCRIPT
  // ==================================
  typescript: {
    // Warn about type errors but don't fail build
    // Set to false in production for stricter checks
    ignoreBuildErrors: false,
  },
  
  // ==================================
  // ESLINT
  // ==================================
  eslint: {
    // Fail build on ESLint errors in production
    ignoreDuringBuilds: false,
  },
  
  // ==================================
  // PAGE EXTENSIONS
  // ==================================
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
  
  // ==================================
  // TRAILING SLASH
  // ==================================
  trailingSlash: false,  // /about vs /about/
  
  // ==================================
  // INTERNATIONALIZATION (i18n)
  // ==================================
  // Uncomment if you need multi-language support
  // i18n: {
  //   locales: ['en', 'vi'],
  //   defaultLocale: 'en',
  // },
}

// ==================================
// SENTRY INTEGRATION (optional)
// ==================================
// Uncomment if using Sentry for error tracking
// const { withSentryConfig } = require('@sentry/nextjs')
// 
// const sentryWebpackPluginOptions = {
//   silent: true,
//   org: process.env.SENTRY_ORG,
//   project: process.env.SENTRY_PROJECT,
// }
// 
// module.exports = withSentryConfig(nextConfig, sentryWebpackPluginOptions)

// ==================================
// BUNDLE ANALYZER PLUGIN
// ==================================
// Uncomment to enable bundle analysis
// const withBundleAnalyzer = require('@next/bundle-analyzer')({
//   enabled: process.env.ANALYZE === 'true',
// })
// module.exports = withBundleAnalyzer(nextConfig)

module.exports = nextConfig

// ==================================
// USAGE NOTES
// ==================================
/**
 * Environment Variables to set in Vercel:
 * 
 * REQUIRED:
 * - DATABASE_URL: PostgreSQL connection string (from Neon)
 * - NEXT_PUBLIC_PYTHON_BACKEND_URL: Railway backend URL
 * - NEXT_PUBLIC_APP_URL: Your Vercel URL
 * - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: Clerk auth key
 * - CLERK_SECRET_KEY: Clerk secret
 * - BLOB_READ_WRITE_TOKEN: Vercel Blob token
 * 
 * OPTIONAL:
 * - OPENAI_API_KEY: If calling from Next.js API routes
 * - GOOGLE_API_KEY: If calling from Next.js API routes
 * - NEXT_PUBLIC_SENTRY_DSN: Error tracking
 * - ANALYZE: Set to 'true' to analyze bundle size
 * 
 * Build Commands:
 * - npm run build: Standard build
 * - ANALYZE=true npm run build: Build with bundle analysis
 * 
 * Image Domains:
 * - Add any domains that serve images to images.domains
 * - This is required for next/image optimization
 * 
 * Security:
 * - All security headers are configured
 * - CORS is handled by backend (Flask-CORS)
 * - HTTPS is enforced via Strict-Transport-Security
 * 
 * Performance:
 * - SWC minification (faster than Terser)
 * - Automatic code splitting
 * - Image optimization with AVIF/WebP
 * - Gzip compression enabled
 * - Console logs removed in production
 */

