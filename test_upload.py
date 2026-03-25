"""
Minimal test: start a fresh server that just logs what it receives from a
browser multipart upload.  Runs on port 8001 so it doesn't clash with app.py.
"""
import io, logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

logging.basicConfig(level=logging.DEBUG)
app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def page():
    return """
    <html><body>
    <form id="f" enctype="multipart/form-data">
      <input type="file" name="file" id="file" accept="image/*">
      <button type="submit">Upload</button>
    </form>
    <pre id="out"></pre>
    <script>
    document.getElementById('f').addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(e.target);
      fd.append('model', 'isnet-general-use');
      fd.append('alpha_matting', 'false');
      const r = await fetch('/upload', {method:'POST', body: fd});
      document.getElementById('out').textContent = await r.text();
    });
    </script>
    </body></html>"""

@app.post("/upload")
async def upload(request: Request):
    # Method 1: request.form()
    form = await request.form()
    file = form.get("file")
    if file:
        data = await file.read()
        return JSONResponse({
            "method": "request.form()",
            "filename": file.filename,
            "content_type": file.content_type,
            "bytes_received": len(data),
            "first_16_bytes_hex": data[:16].hex() if data else "EMPTY",
            "model": str(form.get("model")),
            "alpha_matting": str(form.get("alpha_matting")),
        })
    
    # Fallback: show raw body
    body = await request.body()
    return JSONResponse({"error": "no file found in form", "raw_body_len": len(body)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
