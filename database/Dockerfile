FROM postgres:16

# Copy initialization script
COPY init.sql /docker-entrypoint-initdb.d/

# Set locale for proper sorting
ENV LANG=en_US.utf8
