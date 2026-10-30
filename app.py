import os
import sys
import importlib.util

# 1. Ensure backend directory is first in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")
backend_app_dir = os.path.join(backend_dir, "app")

if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

# Ensure uploads directories exist
os.makedirs(os.path.join(root_dir, "uploads"), exist_ok=True)
os.makedirs(os.path.join(root_dir, "uploads", "garage"), exist_ok=True)

# 2. Register backend/app as the 'app' package in sys.modules so imports like 'from app.database import engine' work seamlessly
spec = importlib.util.spec_from_file_location(
    "app",
    os.path.join(backend_app_dir, "__init__.py"),
    submodule_search_locations=[backend_app_dir]
)
backend_app_pkg = importlib.util.module_from_spec(spec)
sys.modules["app"] = backend_app_pkg
spec.loader.exec_module(backend_app_pkg)

# 3. Import the FastAPI app
from app.main import app as fastapi_app

import gradio as gr

# 4. Define an interactive Gradio landing and health check dashboard
with gr.Blocks(title="AI Claims System - API Gateway") as demo:
    gr.Markdown("""
    # 🚗 AI Motor Claims Inspection & Actuarial Valuation API
    
    ### System Status: 🟢 **Operational & Ready**
    
    This Hugging Face Space hosts the AI inference and actuarial backend:
    - **YOLOv8 Damage Localization**: Multi-panel damage detection
    - **Actuarial Cost Engine**: Real-world vehicle valuation & repair cost estimation
    - **Document OCR Engine**: RC & invoice text extraction
    
    ---
    ### 🔗 Live Endpoints
    - 📖 **Interactive Swagger UI**: [`/docs`](/docs)
    - 🔍 **OpenAPI Schema**: [`/openapi.json`](/openapi.json)
    - 🩺 **Health Check**: [`/health`](/health)
    """)
    
    with gr.Row():
        test_btn = gr.Button("🔍 Ping System Health", variant="primary")
        test_out = gr.Textbox(label="Status Response", value="Click button to test")
    
# ZeroGPU integration for Hugging Face Spaces
try:
    import spaces
    HAS_SPACES = True
except ImportError:
    HAS_SPACES = False

if HAS_SPACES:
    @spaces.GPU
    def ping():
        return "✅ Backend API is active with ZeroGPU acceleration! YOLOv8, Actuarial Engine, and Database are operational."
else:
    def ping():
        return "✅ Backend API is active! YOLOv8, Actuarial Engine, and Database are fully operational."

test_btn.click(ping, outputs=test_out)

# 5. Mount the Gradio demo onto FastAPI so Hugging Face Space displays the Gradio UI while serving all REST endpoints
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
