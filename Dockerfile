# GLB 模型查看器 Docker 镜像
# 基于 Node.js Alpine（轻量、安全）

FROM node:22-alpine

LABEL org.opencontainers.image.title="GLB Model Viewer"
LABEL org.opencontainers.image.description="A web-based GLB/GLTF 3D model viewer with model list browsing"
LABEL org.opencontainers.image.url="https://github.com/winter-tech/glb-viewer"

# 创建非 root 用户
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# 工作目录
WORKDIR /app

# 安装依赖（利用 Docker 缓存层）
COPY package.json ./
RUN npm install --omit=dev && npm cache clean --force

# 复制应用文件
COPY server.js ./
COPY public/ ./public/

# 创建模型目录并设置权限
RUN mkdir -p /app/models && \
    chown -R appuser:appgroup /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 3000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# 启动
CMD ["node", "server.js"]
