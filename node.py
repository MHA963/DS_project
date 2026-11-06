"""Storage node: dumb blob store over HTTP (Flask).  PUT/GET/DELETE /blob/<key>.
A write is only acknowledged after the bytes are fsync'ed and the SHA-256 matches."""
import os, sys
from flask import Flask, request, Response, jsonify
from common import sha256

def make_app(root):
    os.makedirs(root, exist_ok=True)
    app = Flask(__name__)

    def path(key): return os.path.join(root, key)

    @app.put("/blob/<key>")
    def put(key):
        data = request.get_data()
        want = request.headers.get("X-Sha256")
        got = sha256(data)
        if want and want != got:
            return jsonify(error="checksum mismatch"), 422
        tmp = path(key) + ".tmp"
        with open(tmp, "wb") as f:
            f.write(data); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path(key))
        return jsonify(ok=True, size=len(data), sha256=got), 201

    @app.get("/blob/<key>")
    def get(key):
        p = path(key)
        if not os.path.exists(p): return jsonify(error="not found"), 404
        with open(p, "rb") as f: data = f.read()
        return Response(data, mimetype="application/octet-stream")

    @app.delete("/blob/<key>")
    def delete(key):
        try: os.remove(path(key))
        except FileNotFoundError: pass
        return jsonify(ok=True)

    @app.get("/health")
    def health(): return jsonify(ok=True)
    return app

if __name__ == "__main__":
    port, root = int(sys.argv[1]), sys.argv[2]
    from waitress import serve
    serve(make_app(root), host="127.0.0.1", port=port, threads=8, ident="node")
