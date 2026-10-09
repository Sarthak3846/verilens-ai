FROM node:20-alpine AS b
WORKDIR /a
COPY package.json . 
RUN npm install
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npx vite build
FROM nginx:alpine
COPY --from=b /a/dist /usr/share/nginx/html
RUN printf 'server{listen 80;root /usr/share/nginx/html;location /{try_files $uri /index.html;}}' > /etc/nginx/conf.d/default.conf
