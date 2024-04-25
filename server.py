import os
import subprocess
import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# Define a custom HTTP request handler
class TriliumHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        msg = 'Trilium notes app is running on Qoddi! You requested %s' % (self.path)
        self.wfile.write(msg.encode())

class TriliumWorker:
    def setup_trilium(self):
        trilium_data_dir = "/root/trilium-data"
        os.makedirs(trilium_data_dir, exist_ok=True)
        
        subprocess.run(['apt', 'update', '-y'], check=True)
        subprocess.run(['apt', 'install', '-y', 'curl', 'jq', 'xz-utils', 'file'], check=True)
        
        # Fetch the latest release of Trilium
        latest_release_url = 'https://api.github.com/repos/zadam/trilium/releases/latest'
        with urllib.request.urlopen(latest_release_url) as response:
            latest_release = json.loads(response.read().decode())
            for asset in latest_release['assets']:
                if asset['name'].startswith('trilium-linux-x64-server-'):
                    trilium_url = asset['browser_download_url']
                    break
            
        # Download and extract Trilium
        subprocess.run(['curl', '-L', trilium_url, '-o', 'trilium.tar.xz'], check=True)
        subprocess.run(['tar', '-Jxvf', 'trilium.tar.xz', '--strip-components=1'], check=True)
        
        # Download the custom startup script
        startup_script_url = 'https://gist.githubusercontent.com/mem69/023434b1eb72125de193c6b5780b0b00/raw/trilium.sh'
        subprocess.run(['curl', '-o', 'trilium.sh', startup_script_url], check=True)
        subprocess.run(['chmod', '+x', 'trilium.sh'], check=True)

        # Start Trilium using the custom script (in a non-blocking manner)
        self.trilium_process = subprocess.Popen(['./trilium.sh'])

    def run_server(self):
        port = int(os.getenv('PORT', 8080))
        with HTTPServer(('', port), TriliumHandler) as httpd:
            print('Listening on port %s' % port)
            httpd.serve_forever()

    def stop_trilium(self):
        if self.trilium_process:
            self.trilium_process.terminate()


trilium_worker = TriliumWorker()
trilium_worker.setup_trilium()
try:
    trilium_worker.run_server()
finally:
    trilium_worker.stop_trilium()
