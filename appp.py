from flask import Flask, jsonify
import requests
import socket
import json

app = Flask(__name__)

BASE_URL = "https://www.banxico.org.mx/cep/"
VALIDA_URL = "https://www.banxico.org.mx/cep/valida.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

KEYWORDS = ["captcha", "stickyImg", "recaptcha", "imagen de seguridad", "token", "g-recaptcha", "hcaptcha"]

STYLE = """
<style>
  body { font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 2rem; }
  h1 { color: #58a6ff; }
  h2 { color: #79c0ff; border-bottom: 1px solid #30363d; padding-bottom: 0.3rem; }
  a { color: #58a6ff; text-decoration: none; margin-right: 1rem; }
  a:hover { text-decoration: underline; }
  pre { background: #161b22; padding: 1rem; border-radius: 6px; overflow-x: auto; border: 1px solid #30363d; }
  .ok { color: #3fb950; }
  .warn { color: #d29922; }
  .err { color: #f85149; }
  .nav { margin-bottom: 2rem; background: #161b22; padding: 1rem; border-radius: 6px; border: 1px solid #30363d; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem; margin: 2px; }
  .badge-ok { background: #1f4c2b; color: #3fb950; }
  .badge-err { background: #4c1f1f; color: #f85149; }
</style>
"""

NAV = """
<div class="nav">
  <strong>🔬 Banxico Lab</strong> &nbsp;|&nbsp;
  <a href="/">/ Página principal</a>
  <a href="/headers">/headers</a>
  <a href="/dns">/dns</a>
  <a href="/validate">/validate</a>
  <a href="/compare">/compare</a>
</div>
"""

def make_page(title, body):
    return f"<html><head><title>{title}</title>{STYLE}</head><body>{NAV}<h1>{title}</h1>{body}</body></html>"


@app.route("/")
def index():
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        status_class = "ok" if r.status_code == 200 else "warn" if r.status_code < 500 else "err"
        body = f"""
        <h2>Resultado</h2>
        <p>Status: <span class="{status_class}"><strong>{r.status_code}</strong></span></p>
        <p>URL final: <code>{r.url}</code></p>
        <p>Longitud HTML: <strong>{len(r.text):,} caracteres</strong></p>
        <h2>Primeros 5,000 caracteres del HTML</h2>
        <pre>{r.text[:5000].replace('<','&lt;').replace('>','&gt;')}</pre>
        """
    except Exception as e:
        body = f'<p class="err">Error: {e}</p>'
    return make_page("/ — Página principal Banxico CEP", body)


@app.route("/headers")
def headers():
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        rows = "".join(f"<tr><td><code>{k}</code></td><td><code>{v}</code></td></tr>" for k, v in r.headers.items())
        body = f"""
        <h2>Headers de respuesta — Status {r.status_code}</h2>
        <table style="width:100%;border-collapse:collapse;">
          <tr style="color:#79c0ff"><th style="text-align:left;padding:6px;border-bottom:1px solid #30363d">Header</th><th style="text-align:left;padding:6px;border-bottom:1px solid #30363d">Valor</th></tr>
          {rows}
        </table>
        <h2>Headers enviados por nosotros</h2>
        <pre>{json.dumps(HEADERS, indent=2, ensure_ascii=False)}</pre>
        """
    except Exception as e:
        body = f'<p class="err">Error: {e}</p>'
    return make_page("/headers — HTTP Headers", body)


@app.route("/dns")
def dns():
    try:
        ip = socket.gethostbyname("www.banxico.org.mx")
        try:
            hostname, aliases, addresses = socket.gethostbyaddr(ip)
        except Exception:
            hostname, aliases, addresses = "N/A", [], [ip]

        render_ip = requests.get("https://api.ipify.org", timeout=10).text.strip()

        body = f"""
        <h2>DNS de Banxico</h2>
        <pre>Hostname:   www.banxico.org.mx
IP resuelta: {ip}
Reverse DNS: {hostname}
Aliases:     {', '.join(aliases) or 'ninguno'}
Addresses:   {', '.join(addresses)}</pre>

        <h2>IP saliente de Render</h2>
        <pre>IP pública de este servidor: {render_ip}</pre>
        """
    except Exception as e:
        body = f'<p class="err">Error: {e}</p>'
    return make_page("/dns — DNS & IP", body)


@app.route("/validate")
def validate():
    xml_prueba = """<?xml version="1.0" encoding="UTF-8"?>
<SPEI_Tercero>
  <Cedula>
    <datos_operacion
      sello=""
      fecha_operacion="20240101"
      descripcion_concepto="PRUEBA"
      monto="1.00"
      tipo_pago="3"
      clave_rastreo="PRUEBA123456"
      emisor_empresa=""
      emisor_banco="TEST"
      emisor_cuenta="000000000000000000"
      receptor_banco="TEST"
      receptor_cuenta="000000000000000000"
      receptor_nombre="PRUEBA"
    />
  </Cedula>
</SPEI_Tercero>"""

    try:
        resp = requests.post(
            VALIDA_URL,
            data={"xml": xml_prueba},
            headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
            allow_redirects=True,
        )
        status_class = "ok" if resp.status_code == 200 else "warn" if resp.status_code < 500 else "err"
        body = f"""
        <h2>POST a valida.do</h2>
        <p>Status: <span class="{status_class}"><strong>{resp.status_code}</strong></span></p>
        <p>URL final: <code>{resp.url}</code></p>
        <h2>XML enviado</h2>
        <pre>{xml_prueba.replace('<','&lt;').replace('>','&gt;')}</pre>
        <h2>Respuesta (primeros 3,000 chars)</h2>
        <pre>{resp.text[:3000].replace('<','&lt;').replace('>','&gt;')}</pre>
        """
    except Exception as e:
        body = f'<p class="err">Error: {e}</p>'
    return make_page("/validate — POST a valida.do", body)


@app.route("/compare")
def compare():
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        html_lower = r.text.lower()

        badges = ""
        found = []
        not_found = []
        for kw in KEYWORDS:
            if kw.lower() in html_lower:
                count = html_lower.count(kw.lower())
                badges += f'<span class="badge badge-err">⚠ {kw} ({count}x)</span> '
                found.append(kw)
            else:
                badges += f'<span class="badge badge-ok">✓ {kw}</span> '
                not_found.append(kw)

        summary = "ok" if not found else "err"
        summary_text = "No se detectaron mecanismos de protección conocidos." if not found else f"Se detectaron: {', '.join(found)}"

        body = f"""
        <h2>Análisis de la respuesta — Status {r.status_code}</h2>
        <p>Longitud HTML: <strong>{len(r.text):,} caracteres</strong></p>
        <h2>Palabras clave buscadas</h2>
        <p>{badges}</p>
        <h2>Conclusión</h2>
        <p class="{summary}"><strong>{summary_text}</strong></p>
        <h2>Detalle</h2>
        <pre>Encontradas ({len(found)}): {found}
No encontradas ({len(not_found)}): {not_found}</pre>
        """
    except Exception as e:
        body = f'<p class="err">Error: {e}</p>'
    return make_page("/compare — Análisis de protecciones", body)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
