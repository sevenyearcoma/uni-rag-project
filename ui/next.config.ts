import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The UI talks to the Python backend, which lives outside Next.js
  async rewrites() {
    const backend = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [
      {
        source: "/backend/:path*",
        destination: `${backend}/:path*`,
      },
    ];
  },
};

export default nextConfig;
