const lifecycleEvent = process.env.npm_lifecycle_event;

/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: lifecycleEvent === "dev" ? ".next-dev" : lifecycleEvent === "build" ? ".next-build" : ".next",
};

export default nextConfig;
