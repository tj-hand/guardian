# Guardian Frontend - Layer 1 Module
# Builds a Vue 3 library module to be mounted into Evoke (Layer 0)

# =============================================================================
# Development Stage
# =============================================================================
FROM node:20-alpine as development

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port for standalone dev
EXPOSE 5173

# Development command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# =============================================================================
# Build Stage - Library Build
# =============================================================================
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build as library module
RUN npm run build:lib

# =============================================================================
# Layer Output Stage
# Produces the built module for integration with Evoke
# =============================================================================
FROM alpine:3.19 as layer

WORKDIR /guardian

# Copy built library and type definitions
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./

# Copy source for reference/debugging in development
COPY --from=build /app/src ./src

# Layer metadata
LABEL layer.name="guardian"
LABEL layer.level="1"
LABEL layer.type="frontend"
LABEL layer.description="Passwordless authentication module"

# This image is meant to be used as a source for COPY --from in Evoke's Dockerfile
# Example usage in Evoke Dockerfile:
#   FROM guardian-frontend:latest as guardian
#   COPY --from=guardian /guardian /app/layers/guardian
