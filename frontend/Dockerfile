FROM nginx:alpine

# Copy the index.html as a template
COPY index.html /usr/share/nginx/html/index.html.template

# Default backend URL
ENV BACKEND_URL=http://localhost:8080

# Use envsubst to replace the URL at runtime
# We use a shell script to do the replacement and then start nginx
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /usr/share/nginx/html/index.html.template > /usr/share/nginx/html/index.html && exec nginx -g 'daemon off;'"]

EXPOSE 80
