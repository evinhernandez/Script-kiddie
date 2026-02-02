FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci || npm install
EXPOSE 3000
CMD ["npm","run","dev","--","-H","0.0.0.0","-p","3000"]
