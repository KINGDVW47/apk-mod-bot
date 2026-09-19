# =============================================================================
# Dockerfile — APK Mod Bot (pou Railway / Render / Docker)
# =============================================================================

FROM python:3.11-slim

ENV APKTOOL_VERSION=2.10.0

RUN apt-get update && apt-get install -y --no-install-recommends \
        openjdk-17-jre-headless \
        curl \
        unzip \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L -o /usr/local/bin/apktool.jar \
        "https://github.com/iBotPeaches/Apktool/releases/download/v${APKTOOL_VERSION}/apktool_${APKTOOL_VERSION}.jar" \
    && printf '#!/usr/bin/env bash\njava -jar /usr/local/bin/apktool.jar "$@"\n' > /usr/local/bin/apktool \
    && chmod +x /usr/local/bin/apktool

ENV BUILD_TOOLS_VERSION=34.0.0
RUN curl -L -o /tmp/build-tools.zip \
        "https://dl.google.com/android/repository/build-tools_r${BUILD_TOOLS_VERSION}-linux.zip" \
    && mkdir -p /tmp/bt \
    && unzip -q /tmp/build-tools.zip -d /tmp/bt \
    && BT_DIR="/tmp/bt/android-14" \
    && cp "$BT_DIR/aapt" /usr/local/bin/aapt \
    && cp "$BT_DIR/aapt2" /usr/local/bin/aapt2 \
    && cp "$BT_DIR/zipalign" /usr/local/bin/zipalign \
    && cp "$BT_DIR/apksigner" /usr/local/bin/apksigner \
    && cp -r "$BT_DIR/lib" /usr/local/lib/android-lib 2>/dev/null || true \
    && chmod +x /usr/local/bin/aapt /usr/local/bin/aapt2 /usr/local/bin/zipalign /usr/local/bin/apksigner \
    && rm -rf /tmp/build-tools.zip /tmp/bt

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p work uploads state keys

ENV BOT_TOKEN=""

CMD ["bash", "start.sh"]
