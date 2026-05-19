# Hobbyt Frontend

The user-facing dashboard for Hobbyt, built with **Next.js** and **React**. See the [root README](../README.md) for what Hobbyt is and what it does.

---

## Development Setup

### Prerequisites
- Node.js v16+
- npm

### Install & Run
```bash
npm install
npm run dev
```
The app launches at **`http://localhost:3000`**.

### Environment
Create `.env.local` to point at the backend:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Production Build
```bash
npm run build && npm start
```
