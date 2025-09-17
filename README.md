# Náramková Móda

A modern full-stack e-shop for handmade bracelets.

**Frontend:** React (Vite + TailwindCSS)  
**Backend:** Flask (served by Gunicorn behind Nginx)  
**Database:** SQLite managed via Alembic migrations  
**Static/Media:** Nginx-served uploads at `/uploads`

---

## Overview
Náramková Móda is a fast, mobile-first storefront designed for a clean shopping experience and a pragmatic back office. The frontend is a single-page application (SPA) and the backend exposes a REST API for products, categories, media, and administrative actions. The stack favors simplicity, reliability, and straightforward scaling.

> **Site language:** Czech only.

---

## Key Features
- **Product Catalog** — categories, product detail pages, basic filtering and SEO-friendly structure.
- **Responsive Gallery** — lazy loading, optimized images (pipeline prepared for WebP/AVIF).
- **UX Flow “Categories → Gallery”** — smooth visual transition without a hard divider.
- **Cart & Checkout (foundation)** — client logic ready with matching API endpoints in the backend.
- **Admin (Flask)** — manage products, categories, payments, and invoices.
- **Email Integration** — password reset, order confirmations via SMTP.
- **Invoices** — PDF generation scaffolding.
- **Uploads** — secure, direct Nginx delivery under `/uploads`.
- **Environment-driven Config** — switch behavior across environments via env vars.

---

## High-Level Architecture

Frontend (React/Vite/Tailwind) → Nginx (serves SPA and /uploads)
↓ calls /api
Backend (Flask via Gunicorn on 127.0.0.1:5050)
↓
SQLite + Alembic

- **Nginx** serves the built SPA and reverse-proxies `/api` to Gunicorn.
- **Uploads** are served from an Nginx alias (same-origin URLs).
- **SQLite** is the default database; schema is versioned with Alembic.

---

## Tech Stack
- **Frontend:** React 18+, Vite, TailwindCSS 3.x, Axios (optionally JSZip & file-saver for client file workflows)
- **Backend:** Python 3.11+, Flask 2.x, Flask-SQLAlchemy, Alembic, Flask-Mail
- **Server & Runtime:** Gunicorn, Nginx, systemd (Linux)
- **Database:** SQLite (replaceable later with Postgres/MySQL if needed)

---

## Repository Structure

.
├─ backend/
│ ├─ backend/... # application package (blueprints, models, services)
│ ├─ migrations/ # Alembic migrations
│ ├─ instance/ # SQLite DB (git-ignored)
│ ├─ requirements.txt
│ └─ wsgi.py # Gunicorn entry (imports create_app)
├─ frontend/
│ ├─ src/ # React components (Categories, Gallery, Cart, etc.)
│ ├─ index.html
│ ├─ package.json
│ └─ vite.config.js
├─ .gitignore
└─ README.md


---

## API Overview (selection)
- `GET /api/products` — list products (pagination/limits/basic filters)
- `GET /api/products/{id}` — product detail
- `GET /api/categories` — list categories
- `POST /api/auth/login` — authentication (if enabled)
- Static assets and user media are exposed under **`/uploads`** via Nginx

*Notes:* The API follows REST conventions with JSON payloads and clear status codes. It is structured for easy extension (e.g., OpenAPI/Swagger specification can be added).

---

## Data & Media
- **Database:** SQLite file resides under `backend/instance/` (excluded from VCS).
- **Images & Files:** stored outside the app and served by Nginx at `/uploads` with long-cache headers for immutable assets.

---

## Security (Essentials)
- Secrets (e.g., `SECRET_KEY`, SMTP credentials) are managed strictly via environment variables and never committed to VCS.
- Nginx proxies only `/api`; static SPA and `/uploads` are served directly.
- Recommended hardening options include strict response headers (CSP), rate limiting, and 2FA for admin accounts.

---

## Performance & UX
- Mobile-first layouts, responsive components, and snappy SPA navigation.
- Image optimization pipeline prepared (thumbnails/WebP/AVIF).
- Long-term caching for static assets and media.

---

## Roadmap
- Payment integration and automatic invoice dispatch after bank confirmation.
- Full administration for orders and invoicing.
- Search and advanced catalog filters.
- OpenAPI specification for the REST API.
- Extended server-side image pipeline (thumbnails, retina, AVIF).

---


 
