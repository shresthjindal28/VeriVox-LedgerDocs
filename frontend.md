# AI-PDF Document Intelligence Platform
## Frontend Implementation Specification

---

# 1. Objective

Build a production-grade frontend that integrates seamlessly with the existing AI-PDF backend.

The frontend must:

- Connect to all backend REST APIs
- Connect to WebSocket streaming endpoint
- Support PDF upload
- Support real-time conversational interaction
- Display grounded answers with highlighted source references
- Show reasoning and confidence score
- Visualize document integrity (SHA-256 verification)
- Use Zustand for global state
- Use React Query for server state management
- Apply performance optimization using DSA concepts

⚠️ Important:
Do NOT modify backend.
Frontend must strictly adapt to backend API contract.

---

# 2. Tech Stack (Strict)

- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Zustand (Global state)
- React Query (TanStack Query)
- WebSocket (native)
- PDF.js or react-pdf
- Axios
- Dynamic imports for heavy components

---

# 3. Architecture Requirements

## 3.1 Folder Structure

