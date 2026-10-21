"""Início local sem mudar a política de execução do PowerShell."""
from pathlib import Path
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
def main():
    node = shutil.which('node')
    bundled = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
    if not node and bundled.exists(): node = str(bundled)
    if not node:
        raise SystemExit('Node.js não encontrado. Instale Node.js conforme o README.')
    if not (ROOT/'frontend/dist/index.html').exists():
        raise SystemExit('Execute o build do frontend conforme o README antes de iniciar.')
    for port in (8000,5173):
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1',port)) == 0:
                raise SystemExit(f'Porta {port} ocupada. Confira se o WV Gestão já está aberto.')
    processes=[]
    runtime=ROOT/'.runtime'
    runtime.mkdir(exist_ok=True)
    try:
        with (runtime/'backend.log').open('a',encoding='utf-8') as back, (runtime/'frontend.log').open('a',encoding='utf-8') as front:
            flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
            processes.append(subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000'],cwd=ROOT/'backend',stdout=back,stderr=back,creationflags=flags))
            processes.append(subprocess.Popen([node,'node_modules/vite/bin/vite.js','preview','--configLoader','runner','--host','127.0.0.1','--port','5173','--strictPort'],cwd=ROOT/'frontend',stdout=front,stderr=front,creationflags=flags))
            for _ in range(40):
                if any(p.poll() is not None for p in processes):
                    raise SystemExit('Um serviço não iniciou. Consulte os logs em .runtime.')
                try:
                    urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=1)
                    urllib.request.urlopen('http://127.0.0.1:5173',timeout=1)
                    break
                except OSError: time.sleep(.25)
            else: raise SystemExit('Tempo de início excedido. Consulte os logs em .runtime.')
            print('WV Gestão: http://127.0.0.1:5173',flush=True)
            print('Demonstração local. Deixe este terminal aberto. Ctrl+C encerra os dois serviços.',flush=True)
            webbrowser.open('http://127.0.0.1:5173')
            while all(p.poll() is None for p in processes): time.sleep(.5)
    except KeyboardInterrupt:
        print('\nEncerrando WV Gestão…')
    finally:
        for p in processes:
            if p.poll() is None: p.terminate()
        for p in processes:
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: p.kill()

if __name__=='__main__': main()
