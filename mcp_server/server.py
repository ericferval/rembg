import os
from urllib.parse import urlparse

import httpx
from mcp.server.mcpserver import MCPServerfrom rembg import remove

mcp = FastMCP("rembg", stateless_http=True, json_response=True)

@mcp.tool()
async def quitar_fondo(image_url: str) -> str:
    """Elimina el fondo de una imagen pública y devuelve un PNG en base64."""
    import base64
    import ipaddress
    import socket

    parsed = urlparse(image_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Se requiere una URL HTTPS pública")

    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("No se permiten direcciones privadas")

    async with httpx.AsyncClient(follow_redirects=False, timeout=30) as client:
        response = await client.get(image_url)
        response.raise_for_status()
        if len(response.content) > 5_000_000:
            raise ValueError("Imagen demasiado grande")
        if not response.headers.get("content-type", "").startswith("image/"):
            raise ValueError("La URL no contiene una imagen")
        result = remove(response.content)

    return base64.b64encode(result).decode("ascii")

if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = int(os.environ.get("PORT", "8000"))
    mcp.run(transport="streamable-http")
