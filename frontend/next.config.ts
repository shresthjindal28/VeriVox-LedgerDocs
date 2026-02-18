import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  
  // Configure webpack for PDF.js
  webpack: (config) => {
    // Fallback for canvas (not available in browser)
    config.resolve.alias.canvas = false;
    return config;
  },
  
  // Turbopack configuration
  turbopack: {
    resolveAlias: {
      canvas: { browser: '' },
    },
  },
};

export default nextConfig;
