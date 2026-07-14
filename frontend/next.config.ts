import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Don't advertise the framework in response headers.
  poweredByHeader: false,

  // Hardcodes NEXT_PUBLIC_API_URL as a true build-time constant. Unlike a value merely
  // read from `.env`/Vercel dashboard vars (which silently falls back if unset or if a
  // deploy runs before the var is configured), `env` here performs a compile-time text
  // replacement of every `process.env.NEXT_PUBLIC_API_URL` reference via webpack's
  // DefinePlugin — after the build there's no runtime env lookup left to get wrong.
  env: {
    NEXT_PUBLIC_API_URL: "https://omnirag-87oc.onrender.com",
  },
};

export default nextConfig;
