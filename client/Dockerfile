# client/Dockerfile

FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Vite usually runs on 5173
EXPOSE 5173

# We use "dev" mode so you can edit code and see changes instantly
# The --host 0.0.0.0 is CRITICAL for Docker networking
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]