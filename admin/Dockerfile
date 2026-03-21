FROM node:20-alpine

WORKDIR /app

COPY admin/package.json ./package.json
COPY admin/package-lock.json ./package-lock.json
RUN npm install

COPY admin/ ./

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
