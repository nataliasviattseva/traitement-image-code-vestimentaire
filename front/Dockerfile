# Use the official Dart image to build the Flutter web app
FROM dart:stable AS build

# Install Flutter
RUN git clone https://github.com/flutter/flutter.git /usr/local/flutter
ENV PATH="/usr/local/flutter/bin:/usr/local/flutter/bin/cache/dart-sdk/bin:${PATH}"

# Enable flutter web
RUN flutter config --enable-web

# Set the working directory
WORKDIR /app

# Copy pubspec files
COPY flutter_app_ia/pubspec.* ./

# Install dependencies
RUN flutter pub get

# Copy the entire Flutter app
COPY flutter_app_ia/ ./

# Build the web app
RUN flutter build web

# Use nginx to serve the built web app
FROM nginx:alpine

# Copy the built web app to nginx
COPY --from=build /app/build/web /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 3000
EXPOSE 3000

# Start nginx
CMD ["nginx", "-g", "daemon off;"]