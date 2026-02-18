# ============================================================
# Dockerfile — crypto-dash frontend (Node 20, dev mode)
# ============================================================

FROM node:20-alpine

WORKDIR /app

# Install deps first (cache layer)
COPY package*.json ./
RUN npm install

# Copy source (overridden by volume mount in dev)
COPY . .

EXPOSE 3000

# Vite dev server with HMR
CMD ["npm", "run", "dev"]
