# Python + SUMO (built from source, GUI included) + MLflow environment

# Python image (is just Debian 12 image with Python 3.12.3 installed on top of it)
FROM python:3.12.3-bookworm

# 1. Build tools + SUMO's own build dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    libxerces-c-dev \
    libfox-1.6-dev \
    libproj-dev \
    libgdal-dev \
    libeigen3-dev \
    g++ \
    make \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Build SUMO 1.26.0 from source, installed to the same path used on the
# host machine (/usr/local/share/sumo) 
# ARG: Creates a variable only available during the build
# ENV: Creates an environemnt variable available during the build and 
# afterwards in the containers created from the image
ARG SUMO_VERSION=1_26_0
ENV SUMO_HOME=/usr/local/share/sumo
ENV PATH="${SUMO_HOME}/bin:${SUMO_HOME}/tools/assign:${SUMO_HOME}/tools:${PATH}"
# Download tar.gz file containing the source code using curl
RUN curl -fsSL "https://github.com/eclipse-sumo/sumo/archive/refs/tags/v${SUMO_VERSION}.tar.gz" \
        -o /tmp/sumo.tar.gz \
    && mkdir -p /tmp/sumo-src \
    # Extract /tmp/sumo.tar.gz, decompressing it with gzip, 
    # into /tmp/sumo-src, while removing the archive's first directory level.
    && tar -xzf /tmp/sumo.tar.gz -C /tmp/sumo-src --strip-components=1 \
    # cmake = build system
    # -S: Source directory (where is source code)
    # -B: Build directory
    # -DCMAKE_INSTALL_PREFIX=/usr/local/share/sumo: 
    # When I eventually run cmake --install, install SUMO under /usr/local/share/sumo
    # CONFIGURE CMAKE
    && cmake -S /tmp/sumo-src -B /tmp/sumo-build \
        -DCMAKE_INSTALL_PREFIX="${SUMO_HOME}" \
        && cmake --build /tmp/sumo-build -j"$(nproc)" \
        && cmake --install /tmp/sumo-build \
        # COMPILE the project using the build files in /tmp/sumo-build, using all available CPU cores.
    # INSTALL: copy the compiled files to their installation locations
    && rm -rf /tmp/sumo.tar.gz /tmp/sumo-src /tmp/sumo-build

# 3. Python dependencies
# Sets the cwd for every instruction that follows and it also becomes the default directory you land in 
# when you start a shell inside the container afterward
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

