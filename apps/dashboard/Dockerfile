FROM node:20-alpine AS base

FROM base AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
ARG NEXT_PUBLIC_KAIROS_API_URL
ENV NEXT_PUBLIC_KAIROS_API_URL=$NEXT_PUBLIC_KAIROS_API_URL
RUN npm run build

FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ARG NEXT_PUBLIC_KAIROS_API_URL
ENV NEXT_PUBLIC_KAIROS_API_URL=$NEXT_PUBLIC_KAIROS_API_URL

# Copy necessary files from builder
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./next.config.ts
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
