# ====== Build stage ======
FROM node:18 AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build


# ====== Production stage ======
FROM nginx:1.25-alpine

# Remove default nginx config and static content
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Custom nginx config to proxy API/static to backend
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
