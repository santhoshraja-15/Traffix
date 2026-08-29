const path = require("path");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false,
  experimental: {
    cpus: 1,
  },
  // Pin the workspace root to this directory — a stray package-lock.json at
  // the repo root (unrelated to this app) otherwise makes Turbopack guess
  // wrong and warn on every build.
  turbopack: {
    root: path.join(__dirname),
  },
};

module.exports = nextConfig;
