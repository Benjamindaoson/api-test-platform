FROM node:22-bookworm-slim AS dependencies

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM dependencies AS builder
ARG NEXT_PUBLIC_MANAGEMENT_API_URL=http://localhost:8100
ENV NEXT_PUBLIC_MANAGEMENT_API_URL=$NEXT_PUBLIC_MANAGEMENT_API_URL
COPY . .
RUN pnpm build

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

RUN corepack enable
COPY --from=builder /app ./

EXPOSE 3000
CMD ["pnpm", "start"]
