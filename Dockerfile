FROM node:lts-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY . .

EXPOSE 3000

RUN apk update && apk add --no-cache openssl curl wget && \
    rm -rf workers install.sh modal_app.py 2>/dev/null || true && \
    chmod +x app.js || true

ENV PORT=3000
ENV DATA_DIR=/app/data

CMD ["node", "app.js"]
