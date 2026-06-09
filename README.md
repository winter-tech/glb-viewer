# GLB 模型查看器

一个基于 Three.js 的 GLB/GLTF 3D 模型在线查看器，支持 Docker Compose 一键部署。

## ✨ 功能

- 📂 **模型列表**：侧边栏浏览所有模型，支持搜索过滤
- 🖱 **自由操控**：旋转、缩放、平移，OrbitControls 流畅体验
- 🎨 **多种显示**：线框模式、网格参考、自动旋转
- 📊 **模型信息**：实时显示顶点数、三角面数、网格数、文件大小
- 📷 **一键截图**：导出当前视角为 PNG
- ⌨️ **快捷键**：B=侧边栏 R=重置 S=截图 W=线框 G=网格 A=旋转 F=适配
- 🐳 **Docker 部署**：一行命令启动，自动扫描模型目录

## 🚀 快速部署

### Docker Compose（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/glb-viewer.git
cd glb-viewer

# 2. 把 .glb/.gltf 模型文件放入 models/ 目录
cp /你的模型目录/*.glb ./models/

# 3. 启动
docker compose up -d

# 4. 浏览器访问 http://localhost:8080
```

### 静态部署（NAS / Nginx）

```bash
# 1. 扫描模型目录生成清单
python3 scan.py /你的模型目录 --base-url /models/

# 2. 将 public/ 目录和 models.json 部署到 Web 服务器
cp -r public/* models.json /var/www/glb-viewer/
```

## ⚙️ 配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `PORT` | `3000` | 服务端口（容器内） |
| `MODELS_DIR` | `/app/models` | 模型文件目录 |
| `CACHE_TTL` | `30` | 模型列表缓存时间（秒） |

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `B` | 折叠/展开侧边栏 |
| `R` | 重置视角 |
| `S` | 截图保存 |
| `W` | 线框模式 |
| `G` | 网格开关 |
| `A` | 自动旋转 |
| `F` | 适配窗口 |

## 📄 许可

MIT
