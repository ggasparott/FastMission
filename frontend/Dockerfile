# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Aceitar build arg com valor padrão
ARG VITE_API_URL=https://fastmission-fastbackend.utvssk.easypanel.host

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Criar .env.production com a URL da API
RUN echo "VITE_API_URL=${VITE_API_URL}" > .env.production

# Debug - verificar se variável foi setada
RUN echo "📦 Build com VITE_API_URL:" && cat .env.production

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
