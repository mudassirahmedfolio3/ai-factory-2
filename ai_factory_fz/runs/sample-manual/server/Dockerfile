# SAMPLE FILE: written by hand to try the DeepEval tests. NOT output of the pipeline.
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npx prisma generate && npm run build

FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
COPY --from=build /app/prisma ./prisma
COPY --from=build /app/node_modules/.prisma ./node_modules/.prisma
EXPOSE 3000
# Run database migrations, then start the server on $PORT.
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/main.js"]
