#!/usr/bin/env python3
"""
GLB 模型扫描脚本
扫描指定目录下所有 .glb/.gltf 文件，生成 models.json 清单。

用法:
    python3 scan.py /path/to/models          # 扫描指定目录
    python3 scan.py /path/to/models --base-url /models/   # 指定 Web 访问的基础 URL
    python3 scan.py /path/to/models -o ./models.json      # 指定输出路径
"""

import os
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime


def get_file_id(filepath: str) -> str:
    """生成文件唯一标识"""
    return hashlib.md5(filepath.encode()).hexdigest()[:12]


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def scan_models(root_dir: str, base_url: str = "") -> list:
    """
    扫描目录，返回模型文件列表
    """
    root = Path(root_dir).resolve()
    models = []

    extensions = {".glb", ".gltf"}

    for filepath in sorted(root.rglob("*")):
        if filepath.is_file() and filepath.suffix.lower() in extensions:
            rel_path = str(filepath.relative_to(root))
            full_path = str(filepath)
            file_stat = filepath.stat()

            # 构建 Web URL
            if base_url:
                web_url = base_url.rstrip("/") + "/" + rel_path.replace("\\", "/")
            else:
                web_url = rel_path.replace("\\", "/")

            models.append({
                "id": get_file_id(full_path),
                "name": filepath.stem,
                "filename": filepath.name,
                "path": rel_path.replace("\\", "/"),
                "url": web_url,
                "ext": filepath.suffix.lower(),
                "size": file_stat.st_size,
                "sizeFormatted": format_size(file_stat.st_size),
                "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            })

    return models


def generate_watch_script(target_dir: str, base_url: str = "") -> str:
    """
    生成一个 Python 监听脚本，可以在 NAS 上持续运行，
    当模型目录发生变化时自动更新 models.json
    """
    return f'''#!/usr/bin/env python3
"""自动监听模型目录变化并更新 models.json"""
import os, json, time, sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 引入同目录的 scan 逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scan import scan_models

TARGET = {target_dir!r}
BASE_URL = {base_url!r}
OUTPUT = {os.path.join(target_dir, "models.json")!r}

class Handler(FileSystemEventHandler):
    def on_any_event(self, event):
        if event.src_path.endswith(('.glb', '.gltf')):
            rebuild()

def rebuild():
    models = scan_models(TARGET, BASE_URL)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump({{"models": models, "total": len(models), "updated": time.strftime("%Y-%m-%d %H:%M:%S")}}, f, ensure_ascii=False, indent=2)
    print(f"[{{time.strftime('%H:%M:%S')}}] 已更新: {{len(models)}} 个模型")

if __name__ == "__main__":
    rebuild()
    observer = Observer()
    observer.schedule(Handler(), TARGET, recursive=True)
    observer.start()
    print(f"监听中: {{TARGET}}")
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
'''


def main():
    parser = argparse.ArgumentParser(description="扫描 GLB/GLTF 模型文件，生成清单 JSON")
    parser.add_argument("directory", help="要扫描的目录路径")
    parser.add_argument("--base-url", "-u", default="",
                        help="模型文件在 Web 上的访问基础 URL（如 /models/ 或 https://nas.local/models/）")
    parser.add_argument("--output", "-o", default=None,
                        help="输出 JSON 文件路径（默认输出到扫描目录下的 models.json）")
    parser.add_argument("--gen-watcher", "-w", action="store_true",
                        help="同时生成文件监听脚本 watcher.py")

    args = parser.parse_args()
    target = os.path.abspath(args.directory)

    if not os.path.isdir(target):
        print(f"错误: 目录不存在 - {target}")
        exit(1)

    models = scan_models(target, args.base_url)

    result = {
        "models": models,
        "total": len(models),
        "scanned": target,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    output_path = args.output or os.path.join(target, "models.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"✅ 扫描完成: {len(models)} 个模型")
    print(f"📁 输出文件: {output_path}")
    for m in models:
        print(f"   📦 {m['filename']}  ({m['sizeFormatted']})")

    if args.gen_watcher:
        watcher_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else ".", "watcher.py")
        watcher_code = generate_watch_script(target, args.base_url)
        with open(watcher_path, "w", encoding="utf-8") as f:
            f.write(watcher_code)
        print(f"🔍 监听脚本已生成: {watcher_path}")
        print(f"   运行方式: python3 {watcher_path}")


if __name__ == "__main__":
    main()
