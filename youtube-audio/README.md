# YouTube Audio Player

PWA para ouvir vídeos do YouTube em modo áudio, com ecrã bloqueado.

## Arquitetura

```
frontend/   → Netlify (PWA estática)
backend/    → Railway (Python + Flask + yt-dlp)
```

## Deploy

### 1. Backend (Railway)

1. No Railway, cria um novo projeto → "Deploy from GitHub repo"
2. Seleciona a pasta `backend/` (ou usa o root com `railway.json`)
3. Após deploy, copia o URL público (ex: `https://yt-audio-mario.up.railway.app`)

### 2. Frontend (Netlify)

1. Edita `frontend/index.html` — linha perto do fim:
   ```html
   <script>window.BACKEND_URL = "https://SEU-URL.up.railway.app";</script>
   ```
2. No Netlify, cria novo site → deploy da pasta `frontend/`

### 3. iPhone — Adicionar ao ecrã inicial

1. Abre o URL Netlify no Safari
2. Partilhar → "Adicionar ao ecrã de início"
3. A app fica com ícone e abre em modo standalone

## Funcionalidades

- Streaming de áudio imediato (sem download)
- Suporte a seek (avançar/recuar na barra de progresso)
- Controlos no ecrã de bloqueado (Media Session API)
- Recuar 15s / Avançar 30s
- Velocidade de reprodução: 0.75×, 1×, 1.25×, 1.5×, 2×
- Fila de reprodução com persistência (localStorage)
- PWA instalável no iPhone
