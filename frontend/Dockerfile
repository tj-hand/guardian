# ========================================
# Guardian Frontend Dockerfile
# ========================================
# Multi-stage build for Vue 3 application
# Layer 1 module for Evoke integration
# Optimized for production with Nginx serving

# ========================================
# Stage 1: Development
# ========================================
FROM node:22-alpine AS development

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:5173 || exit 1

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ========================================
# Stage 2: Build
# ========================================
FROM node:22-alpine AS build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies needed for build)
RUN npm ci

# Copy application code
COPY . .

# Build application
RUN npm run build

# ========================================
# Stage 3: Layer Target (for Evoke)
# ========================================
# This stage exports the built Guardian module for Evoke integration
# Layer 0 containers (Evoke) can copy the dist folder from this stage
FROM node:22-alpine AS layer

# Set working directory
WORKDIR /app

# Copy built files from build stage
COPY --from=build /app/dist /app/dist
COPY --from=build /app/package.json /app/package.json

# Set module metadata
ENV GUARDIAN_MODULE_NAME="guardian-frontend" \
    GUARDIAN_MODULE_VERSION="1.0.0" \
    GUARDIAN_MODULE_TYPE="authentication-ui"

# Create a simple server for layer testing (optional)
RUN npm install -g serve

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:5173 || exit 1

# Serve built files for testing
CMD ["serve", "-s", "dist", "-l", "5173"]

# ========================================
# Stage 4: Production
# ========================================
FROM nginx:alpine AS production

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration (if custom config needed)
# COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ========================================
# Build Instructions
# ========================================
#
# Layer target (for Evoke integration):
#   docker build --target layer -t guardian-frontend:layer .
#   docker run --rm guardian-frontend:layer tar -cf - /app/dist | tar -xf - -C ./mounted-volume
#
# Development build:
#   docker build --target development -t guardian-frontend:dev .
#
# Production build:
#   docker build --target production -t guardian-frontend:prod .
#
# Run development container:
#   docker run -p 5173:5173 -v $(pwd):/app -v /app/node_modules guardian-frontend:dev
#
# Run production container:
#   docker run -p 80:80 guardian-frontend:prod
#
# ========================================
