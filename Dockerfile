# Jason Stys: non-root ciphertext account service; builds UI separately, never includes runtime files.
FROM node:24-bookworm-slim AS ui
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html tsconfig.json vite.config.ts ./
COPY web ./web
COPY public ./public
COPY examples ./examples
COPY scripts/compile_schemas.mjs ./scripts/compile_schemas.mjs
RUN npm run build

FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AES_PRIVATE_DATA=/data AES_UI=/app/dist
WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home studio && mkdir /data && chown studio:studio /data
COPY --from=ui /build/dist ./dist
USER 10001:10001
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.server:application", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--no-proxy-headers", "--workers", "1", "--limit-concurrency", "50", "--timeout-keep-alive", "5"]
