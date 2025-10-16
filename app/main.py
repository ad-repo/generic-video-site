import os
import mimetypes
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR_ENV = "VIDEO_BASE_DIR"
VIDEOS_ROOT = os.environ.get(BASE_DIR_ENV) or "/Volumes/docker/video-site/data"

app = FastAPI(title="Generic Video Site")

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


def walk_videos(base_dir: Path) -> List[dict]:
	if not base_dir.exists() or not base_dir.is_dir():
		return []
	items: List[dict] = []
	# Recursively find videos at any depth; preserve full directory structure
	candidates: List[Path] = sorted(list(base_dir.rglob("*.mp4")) + list(base_dir.rglob("*.MP4")))
	for video_path in candidates:
		rel_path = video_path.relative_to(base_dir)
		parts = rel_path.parts
		# Full directory path (excluding filename)
		dir_path = "/".join(parts[:-1]) if len(parts) > 1 else ""
		# Individual path components for hierarchy
		path_components = parts[:-1] if len(parts) > 1 else []
		title = video_path.stem
		subtitles = []
		for ext in (".vtt", ".srt", ".VTT", ".SRT"):
			cand = video_path.with_suffix(ext)
			if cand.exists():
				subtitles.append(str(cand.relative_to(base_dir)))
		
		# Find resources in the same directory
		resources = []
		video_dir = video_path.parent
		try:
			for resource_file in video_dir.iterdir():
				if resource_file.is_file():
					file_ext = resource_file.suffix.lower()
					file_name = resource_file.name.lower()
					
					# Only include HTML and PDF files that are clearly resources
					if file_ext in ['.html', '.htm', '.pdf']:
						# Exclude files that are clearly not resources
						exclude_patterns = ['transcript', 'subtitle', 'caption', 'vtt', 'srt']
						if not any(pattern in file_name for pattern in exclude_patterns):
							resources.append({
								"name": resource_file.name,
								"path": str(resource_file.relative_to(base_dir)),
								"type": file_ext,
								"size": resource_file.stat().st_size
							})
		except Exception as e:
			print(f"Error scanning resources in {video_dir}: {e}")
		
		items.append({
			"class": parts[0] if parts else "Unknown",  # Keep for backward compatibility
			"title": title,
			"path": str(rel_path),
			"dir_path": dir_path,
			"path_components": path_components,
			"subtitles": subtitles,
			"resources": resources,
		})
	return items


@app.get("/healthz")
def healthz():
	return {"ok": True}


@app.get("/api/library")
async def api_library(q: Optional[str] = Query(default=None), sort: str = Query(default="class,title")):
	base = Path(VIDEOS_ROOT)
	items = walk_videos(base)

	if q:
		q_lower = q.lower()
		items = [i for i in items if q_lower in i["title"].lower() or q_lower in i["class"].lower()]

	# simple multi-key sort: keys separated by comma, supports 'class' and 'title'
	keys = [k.strip() for k in sort.split(",") if k.strip() in ("class", "title")]
	for key in reversed(keys):
		if key == "title":
			# Sort titles numerically by leading number, then alphabetically
			def sort_key(item):
				title = item[key]
				# Extract leading number for numerical sorting
				match = title.split()[0] if title else "0"
				try:
					# Try to parse as number, fallback to 0
					leading_num = int(match) if match.isdigit() else 0
					return (leading_num, title)
				except:
					return (0, title)
			items.sort(key=sort_key)
		else:
			items.sort(key=lambda x: x[key])

	return {"items": items}


@app.get("/api/refresh")
async def api_refresh():
	# Stateless: front-end will just re-fetch library; endpoint exists for semantics
	return {"refreshed": True}


@app.get("/api/debug")
async def api_debug():
	# Debug endpoint to check what resources are being found
	base = Path(VIDEOS_ROOT)
	items = walk_videos(base)
	
	# Count resources
	total_resources = 0
	items_with_resources = 0
	for item in items:
		if item.get('resources'):
			total_resources += len(item['resources'])
			items_with_resources += 1
	
	return {
		"total_items": len(items),
		"items_with_resources": items_with_resources,
		"total_resources": total_resources,
		"sample_items": items[:3] if items else []
	}


@app.get("/video/{path:path}")
async def stream_video(path: str, request: Request):
	file_path = Path(VIDEOS_ROOT) / path
	if not file_path.exists() or not file_path.is_file():
		raise HTTPException(status_code=404, detail="Video not found")

	file_size = file_path.stat().st_size
	range_header = request.headers.get("range")

	def iter_file(start: int, end: int):
		with open(file_path, "rb") as f:
			f.seek(start)
			remaining = end - start + 1
			chunk_size = 1024 * 1024
			while remaining > 0:
				read_size = min(chunk_size, remaining)
				data = f.read(read_size)
				if not data:
					break
				remaining -= len(data)
				yield data

	if range_header:
		try:
			units, range_spec = range_header.split("=")
			start_str, end_str = range_spec.split("-")
			start = int(start_str) if start_str else 0
			end = int(end_str) if end_str else file_size - 1
			end = min(end, file_size - 1)
		except Exception:
			raise HTTPException(status_code=416, detail="Invalid Range header")

		headers = {
			"Content-Range": f"bytes {start}-{end}/{file_size}",
			"Accept-Ranges": "bytes",
			"Content-Length": str(end - start + 1),
			"Content-Type": "video/mp4",
		}
		return StreamingResponse(iter_file(start, end), status_code=206, headers=headers)

	headers = {
		"Accept-Ranges": "bytes",
		"Content-Length": str(file_size),
		"Content-Type": "video/mp4",
	}
	return StreamingResponse(iter_file(0, file_size - 1), headers=headers)


@app.get("/subs/{path:path}")
async def serve_subtitles(path: str):
	file_path = Path(VIDEOS_ROOT) / path
	if not file_path.exists() or not file_path.is_file():
		raise HTTPException(status_code=404, detail="Subtitle not found")
	mime, _ = mimetypes.guess_type(str(file_path))
	# Default to text/vtt if we cannot guess
	mime = mime or ("text/vtt" if file_path.suffix == ".vtt" else "text/plain")
	return FileResponse(str(file_path), media_type=mime)


@app.get("/resources/{path:path}")
async def serve_resources(path: str):
	file_path = Path(VIDEOS_ROOT) / path
	if not file_path.exists() or not file_path.is_file():
		raise HTTPException(status_code=404, detail="Resource not found")
	
	# Security check - ensure file is in allowed extensions
	allowed_extensions = ['.html', '.htm', '.pdf']
	if file_path.suffix.lower() not in allowed_extensions:
		raise HTTPException(status_code=403, detail="File type not allowed")
	
	mime, _ = mimetypes.guess_type(str(file_path))
	return FileResponse(str(file_path), media_type=mime)


@app.get("/")
async def index():
	index_file = static_dir / "index.html"
	if not index_file.exists():
		return HTMLResponse("<h1>Vibe Video Site</h1><p>Static assets missing.</p>")
	return HTMLResponse(index_file.read_text(encoding="utf-8"))
