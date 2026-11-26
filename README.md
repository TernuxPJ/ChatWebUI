<div align="center">
  <img src="docs/icon.png" alt="Unicollect ChatWebUI Icon" width="112" height="112" />

  <h1>Unicollect ChatWebUI</h1>
  <p><strong>100% Persian (RTL-First) Google Gemini-Inspired AI Web Panel, OpenAI-Compatible Router &amp; 24/7 GitHub Pages Deployment</strong></p>
  <p>Created by <strong>Muvixo</strong> · Pure Vanilla HTML / CSS / JavaScript + FastAPI + Ollama</p>

  <p>
    <a href="https://theoryvex.github.io/ChatWebUI/"><strong>Live Site</strong></a> ·
    <a href="https://theoryvex.github.io/ChatWebUI/chat/"><strong>Web Chat</strong></a> ·
    <a href="https://theoryvex.github.io/ChatWebUI/api-docs/"><strong>API Docs</strong></a> ·
    <a href="https://theoryvex.github.io/ChatWebUI/public-key/"><strong>Public Key</strong></a>
  </p>
</div>

---

## Highlights & Features

- **Persian RTL-First Gemini Design System**: Built with flat matte Dark (`#0E0E10`) and crisp Light (`#FFFFFF`) themes, clean Gemini Blue (`#007BFF` / `#8AB4F8`) accents, `1px` hairline borders, zero gradients, zero neon glows, logical RTL CSS properties, and 60fps `opacity` / `scale` transitions (`cubic-bezier(0.16, 1, 0.3, 1)`).
- **100% Offline-Ready Assets**: Locally bundled `Vazirmatn.woff2`, `JetBrainsMono.woff2`, inline SVGs, and all **3,793 Apple emoji PNGs** (`app/static/emojis/apple/` and `pages/assets/emojis/apple/`) with zero external CDN dependencies.
- **6 Specialized Models & Smart 3-Way Router**:
  - Automatic `Science` → `Math` → `Chat` routing that prioritizes physics, quantum mechanics, chemistry, and biology prompts even when they include LaTeX or integrals.
  - **Zero-Reload RAM Pinning**: Checks Ollama's live `/api/ps` before switching, defaults to `OLLAMA_MAX_LOADED_MODELS=2`, and prevents the lightweight router model from evicting hot primary models from RAM.
  - **Guidance-Only Policy**: System prompts enforce polite, accurate, well-structured guidance and conceptual explanations without writing raw code.
- **Offline LaTeX & Chemistry Rendering**: Full support for display/inline LaTeX (`$$...$$`, `\[...\]`, `\(...\)`, bare `\boxed{...}`, `\begin{align}...\end{align}`), `mhchem` chemistry (`\ce{...}`), RTL-safe chemical ions (`Fe²⁺`, `OH⁻`), and automatic live preview inside the composer.
- **Real-Time Activity Counter**: Shows live online users and concurrent active replies directly in the top bar via `/health`.
- **OpenAI / 9router Compatible API**: Drop-in `/v1/chat/completions`, `/v1/models`, `/api/v1/chat`, `/api/v1/chat/stream`, and `/api/chat/route` with interactive Swagger UI at `/docs`.
- **24/7 Self-Chaining GitHub Actions + Cloudflare Tunnel**: Automatic handoff, health watchdog, and instant GitHub Pages publishing (`deploy.yml`, `heartbeat.yml`, `pages.yml`).

---

## Model Registry

| Model ID | Display Label | Category | Tier |
| :--- | :--- | :--- | :--- |
| `unicollect-chat-mini` | Unicollect Chat Mini | Chat | Fast (Mini) |
| `unicollect-chat-1.2` | Unicollect Chat 1.2 | Chat | Advanced (1.2) |
| `unicollect-math-mini` | Unicollect Math Mini | Math | Fast (Mini) |
| `unicollect-math-1.2` | Unicollect Math 1.2 | Math | Advanced (1.2) |
| `unicollect-science-mini` | Unicollect Science Mini | Science | Fast (Mini) |
| `unicollect-science-1.2` | Unicollect Science 1.2 | Science | Advanced (1.2) |

---

## Quick Start (GitHub Pages + 24/7 Tunnel)

1. Push this repository to the `main` branch on GitHub.
2. Go to **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**.
3. Go to **Settings → Pages → Build and deployment**, set **Source** to **Deploy from a branch**, choose **`gh-pages`** and **`/ (root)`**, then click **Save**.
4. *(Optional)* Repository secrets under **Settings → Secrets and variables → Actions**:
   - `PANEL_TOKEN` — protect the web panel with an access token.
   - `PUBLIC_API_KEY` — set a fixed `sk-uc-...` API key (auto-generated if omitted).
   - `PAT_TOKEN` — optional Personal Access Token (`workflow` scope) for cross-run handoff beyond `github.token`.
5. Run **Actions → Ollama Web Panel 24/7 + Cloudflare Tunnel → Run workflow**.

---

## Local Development & Testing

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run in Demo Mode (no Ollama required)
PANEL_DEMO_MODE=1 uvicorn app.main:app --reload --port 8000

# Or run with local Ollama
bash scripts/start_ollama.sh &
ollama pull "$MODEL_NAME"
uvicorn app.main:app --port 8000
```

### Sync Assets & Run Test Suite
```bash
python scripts/sync_chat.py
python scripts/sync_chat.py --check
PANEL_DEMO_MODE=1 pytest -q
```
