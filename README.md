# Sales Sheet Viewer

A small Node app that takes an e-commerce Excel/CSV sales export via drag-and-drop and displays its contents in the browser. Files are parsed in memory on the server and never written to disk.

- **Backend:** Express + Multer (upload) + SheetJS/xlsx (parse)
- **Frontend:** single static HTML page, no build step
- **Supported files:** `.xlsx`, `.xls`, `.csv`, up to 20 MB
- Multi-sheet workbooks render as tabs; display is capped at 1,000 rows per sheet

## Run locally

Requires Node 18+.

```bash
npm install
npm start
```

Open http://localhost:3000 and drop a file in.

## File structure

```
sales-viewer/
├── server.js          # Express server + /api/upload parse endpoint
├── package.json
└── public/
    └── index.html     # drag-and-drop UI + table rendering
```

---

## Host it yourself

Pick whichever matches how you want to run it. All keep the app on your own machine/server.

### Option A — Run on your own VM (DigitalOcean, EC2, a home server)

1. Install Node 18+ on the box:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```
2. Copy this folder up (e.g. `scp -r sales-viewer user@your-server:~/`).
3. Install deps and start:
   ```bash
   cd sales-viewer && npm install && npm start
   ```
4. Keep it running after you log out with **PM2**:
   ```bash
   sudo npm install -g pm2
   pm2 start server.js --name sales-viewer
   pm2 save && pm2 startup   # run the command it prints, so it survives reboots
   ```
5. Put **Nginx** in front so you can use port 80/443 and add HTTPS:
   ```nginx
   server {
     listen 80;
     server_name your-domain.com;
     location / {
       proxy_pass http://localhost:3000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
     }
   }
   ```
   Then `sudo certbot --nginx -d your-domain.com` for a free Let's Encrypt cert.

### Option B — Docker (portable, one command)

Add this `Dockerfile` to the folder:

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

Build and run:

```bash
docker build -t sales-viewer .
docker run -d -p 3000:3000 --restart unless-stopped --name sales-viewer sales-viewer
```

App is on http://localhost:3000. Point Nginx/Caddy at it the same way as Option A for a domain + HTTPS.

### Option C — Home machine, quick share

Run `npm start`, then expose it temporarily with a tunnel (no server needed):

```bash
npx localtunnel --port 3000
# or: cloudflared tunnel --url http://localhost:3000
```

Good for demos; use Option A or B for anything permanent.

## Notes

- Set a custom port with `PORT=8080 npm start`.
- To change the row display cap or upload size limit, edit the `1000` slice and the `limits.fileSize` value in `server.js`.
- The parse endpoint returns clean JSON errors for unsupported types and oversized files, which the UI surfaces inline.
