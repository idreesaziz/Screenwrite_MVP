# Frontend Dockerfile - React Router 7 SSR App
# Optimized for GCP Cloud Run deployment

FROM node:20-slim AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

# ---- Dependencies ----
FROM base AS deps
WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile

# ---- Build ----
FROM base AS build
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments for environment variables (set at build time)
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_BACKEND_URL

ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

RUN pnpm run build

# ---- Production ----
FROM base AS production
WORKDIR /app

ENV NODE_ENV=production

# Copy built application
COPY --from=build /app/build ./build
COPY --from=build /app/package.json ./package.json

# Install only production dependencies
COPY --from=deps /app/node_modules ./node_modules

# Cloud Run uses port 8080 by default
ENV PORT=8080
EXPOSE 8080

# Run the React Router server
CMD ["pnpm", "run", "start"]
