import express from 'express';
import { readdir, stat } from 'node:fs/promises';
import { join, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));

const app = express();
const PORT = parseInt(process.env.PORT || '3000', 10);
const MODELS_DIR = process.env.MODELS_DIR || join(__dirname, 'models');
const CACHE_TTL = parseInt(process.env.CACHE_TTL || '30', 10) * 1000; // 默认 30 秒缓存

// ============ 静态文件 ============

// 前端页面
app.use(express.static(join(__dirname, 'public')));

// 模型文件（挂载的外部目录）
app.use('/models', express.static(MODELS_DIR, {
    setHeaders(res, filePath) {
        // 允许大文件
        if (filePath.endsWith('.glb')) {
            res.setHeader('Content-Type', 'model/gltf-binary');
        } else if (filePath.endsWith('.gltf')) {
            res.setHeader('Content-Type', 'model/gltf+json');
        }
        // CORS 头（便于跨域访问）
        res.setHeader('Access-Control-Allow-Origin', '*');
    }
}));

// ============ API ============

// 缓存
let cachedModels = null;
let cacheTime = 0;

async function scanModels() {
    const extensions = new Set(['.glb', '.gltf']);
    const models = [];

    try {
        const entries = await readdir(MODELS_DIR, { withFileTypes: true });

        for (const entry of entries) {
            if (entry.isFile()) {
                const ext = extname(entry.name).toLowerCase();
                if (extensions.has(ext)) {
                    const filePath = join(MODELS_DIR, entry.name);
                    let fileStat;
                    try {
                        fileStat = await stat(filePath);
                    } catch {
                        continue;
                    }
                    models.push({
                        id: Buffer.from(filePath).toString('base64').slice(0, 12),
                        name: entry.name.replace(ext, ''),
                        filename: entry.name,
                        url: `/models/${encodeURIComponent(entry.name)}`,
                        ext,
                        size: fileStat.size,
                        sizeFormatted: formatSize(fileStat.size),
                        modified: fileStat.mtime.toISOString(),
                    });
                }
            }
        }
    } catch (err) {
        console.error('[scan] 扫描模型目录失败:', err.message);
    }

    // 按文件名排序
    models.sort((a, b) => a.filename.localeCompare(b.filename, 'zh'));

    return models;
}

async function getModels() {
    const now = Date.now();
    if (cachedModels && (now - cacheTime) < CACHE_TTL) {
        return cachedModels;
    }
    cachedModels = await scanModels();
    cacheTime = now;
    return cachedModels;
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// GET /api/models - 获取模型列表
app.get('/api/models', async (_req, res) => {
    const models = await getModels();
    res.json({
        models,
        total: models.length,
        directory: MODELS_DIR,
        updated: new Date().toISOString(),
    });
});

// POST /api/refresh - 强制刷新缓存
app.post('/api/refresh', (_req, res) => {
    cachedModels = null;
    cacheTime = 0;
    res.json({ ok: true, message: '缓存已清除，下次请求将重新扫描' });
});

// GET /api/health - 健康检查
app.get('/api/health', (_req, res) => {
    res.json({ status: 'ok', uptime: process.uptime() });
});

// ============ 启动 ============

app.listen(PORT, '0.0.0.0', () => {
    console.log('');
    console.log('  🚀 GLB 模型查看器已启动');
    console.log(`  📡 地址: http://0.0.0.0:${PORT}`);
    console.log(`  📁 模型目录: ${MODELS_DIR}`);
    console.log(`  ⏱  缓存时间: ${CACHE_TTL / 1000}s`);
    console.log('');
});
