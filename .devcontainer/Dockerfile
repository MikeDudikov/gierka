FROM debian:trixie-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates curl wget git gnupg unzip xz-utils zstd pigz \
    python3 python3-venv python3-pip procps file findutils \
    libgtk-3-0t64 libnss3 libasound2t64 libgbm1 libx11-6 libxext6 \
    libxcursor1 libxrandr2 libxi6 libxrender1 libxcomposite1 libxss1 \
    libglu1-mesa libgl1 libegl1 libvulkan1 mesa-vulkan-drivers \
    libunwind8 libcurl4t64 libssl3t64 libatomic1 libxml2 \
    libnotify4 libsecret-1-0 fonts-dejavu-core \
    libmpc3 libmpfr6 libgmp10 libisl23 libzstd1 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace/gierka
