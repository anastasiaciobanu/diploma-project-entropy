FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:1
ENV SDL_AUDIODRIVER=dummy
ENV DOOMWADDIR=/usr/share/games/doom

WORKDIR /opt/entro

# install system packages required for python, frida, crispy doom, freedoom and noVNC
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    git \
    build-essential \
    cmake \
    pkg-config \
    python3 \
    python3-pip \
    python3-venv \
    libsdl2-dev \
    libsdl2-mixer-dev \
    libsdl2-net-dev \
    libpng-dev \
    zlib1g-dev \
    freedoom \
    xvfb \
    openbox \
    x11vnc \
    novnc \
    websockify \
    xterm \
    procps \
    psmisc \
    && rm -rf /var/lib/apt/lists/*

# install the python dependency used by run_manager.py
RUN pip3 install --break-system-packages frida==17.7.2

# recreate the same doom path expected by scripts/run_manager.py
RUN mkdir -p /opt/entro/doom/build

# clone and build crispy doom inside the container
RUN git clone https://github.com/fabiangreffrath/crispy-doom.git /opt/entro/doom/build/crispy-doom \
    && cmake -S /opt/entro/doom/build/crispy-doom \
             -B /opt/entro/doom/build/crispy-doom/build \
             -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /opt/entro/doom/build/crispy-doom/build --parallel

# copy only the experiment scripts and docker entrypoint
COPY scripts/ /opt/entro/scripts/
COPY docker/entrypoint.sh /opt/entro/docker/entrypoint.sh

# create the output folder used by run_manager.py
RUN mkdir -p /opt/entro/runs \
    && chmod +x /opt/entro/docker/entrypoint.sh

EXPOSE 6080

ENTRYPOINT ["/opt/entro/docker/entrypoint.sh"]
CMD ["menu"]
