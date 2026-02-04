# server/Dockerfile

# Use a standard Node version
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy package info first (for better caching)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the backend code
COPY --chown=node:node . .

# Expose the port the server runs on
EXPOSE 5000

USER node

# Start the server using nodemon (if you have it) or just node
CMD ["node", "index.js"]