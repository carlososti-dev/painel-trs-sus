"""Servidor local do app (painel + chat) para testar no seu computador.

Serve os arquivos desta pasta e responde em /api/claude como a função da Vercel.
Uso:
    export ANTHROPIC_API_KEY="sua-chave"        # obrigatório para o chat
    export CODIGO_ACESSO="um-codigo"             # opcional
    python3 servidor_local.py                    # abre em http://localhost:8000
"""
import http.server
import json
import os
import ssl
import urllib.error
import urllib.request
import webbrowser
from functools import partial
from pathlib import Path

PASTA = Path(__file__).resolve().parent
PORTA = int(os.environ.get("PORTA", "8000"))
FERRAMENTAS = {"consultar_indicadores", "residencia_pacientes", "listar_valores"}


def contexto_ssl():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class Handler(http.server.SimpleHTTPRequestHandler):
    def _json(self, status, obj):
        corpo = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if self.path.split("?")[0] == "/api/claude":
            return self._json(200, {"configurado": bool(os.environ.get("ANTHROPIC_API_KEY")),
                                    "precisa_codigo": bool(os.environ.get("CODIGO_ACESSO"))})
        return super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/claude":
            return self._json(404, {"erro": "Não encontrado."})
        chave = os.environ.get("ANTHROPIC_API_KEY", "")
        cod = os.environ.get("CODIGO_ACESSO", "")
        if not chave:
            return self._json(503, {"erro": "Chave da API não configurada."})
        if cod and self.headers.get("x-codigo-acesso") != cod:
            return self._json(401, {"erro": "Código de acesso inválido."})
        n = int(self.headers.get("Content-Length", 0))
        if n > 250000:
            return self._json(413, {"erro": "Conversa longa demais."})
        try:
            b = json.loads(self.rfile.read(n))
            assert isinstance(b.get("system"), str) and isinstance(b.get("messages"), list) and isinstance(b.get("tools"), list)
            assert len(b["system"]) <= 8000 and len(b["tools"]) <= 5 and all(t.get("name") in FERRAMENTAS for t in b["tools"])
        except Exception:
            return self._json(400, {"erro": "Pedido inválido."})
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({"model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"), "max_tokens": 2048,
                             "system": b["system"], "messages": b["messages"], "tools": b["tools"]}).encode(),
            headers={"x-api-key": chave, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120, context=contexto_ssl()) as r:
                j = json.loads(r.read())
            return self._json(200, {"content": j.get("content"), "stop_reason": j.get("stop_reason")})
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read()).get("error", {}).get("message")
            except Exception:
                msg = None
            return self._json(429 if e.code == 429 else 502, {"erro": msg or f"Falha na API ({e.code})."})
        except Exception as e:
            return self._json(502, {"erro": f"Não foi possível falar com a API: {e}"})

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), partial(Handler, directory=str(PASTA)))
    url = f"http://localhost:{PORTA}"
    print(f"App rodando em {url}  (Ctrl+C para parar)")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Aviso: ANTHROPIC_API_KEY não definida — o painel funciona, o chat não.")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    srv.serve_forever()
