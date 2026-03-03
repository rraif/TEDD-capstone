# --- Stage 1: Build the React Code ---
FROM node:20-alpine AS builder

WORKDIR /app

# 1. Accept the build argument from docker-compose
ARG VITE_API_URL
# 2. Set it as an environment variable so Vite can "bake" it into the JS
ENV VITE_API_URL=$VITE_API_URL

# 3. Copy package files from the client folder (context is root)
COPY client/package*.json ./
RUN npm install

# 4. Copy the client source code
COPY client/ .

# 5. Build the production-ready static files
RUN npm run build

# --- Stage 2: Serve with NGINX ---
FROM nginx:alpine

# 6. Remove the default Nginx index page
RUN rm -rf /usr/share/nginx/html/*

# 7. Copy your custom Nginx config from the root folder
COPY client/nginx.conf /etc/nginx/conf.d/default.conf

# 8. Copy the compiled React files (dist) from Stage 1 into Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]