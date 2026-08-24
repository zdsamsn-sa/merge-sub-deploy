"""
Modal deployment for Merge-sub (Node.js Express subscription merger).

Prerequisites:
  1. Install Modal CLI:  pip install modal
  2. Authenticate:       modal setup
  3. (Recommended) Create a secret for credentials:
       modal secret create merge-sub-secrets \\
         USERNAME=admin \\
         PASSWORD=your_strong_password \\
         SUB_TOKEN=mysecrettoken \\
         API_URL=https://sublink.eooce.com

Deploy (persistent URL):
  modal deploy modal_app.py

Serve (ephemeral, auto-reloads on code change):
  modal serve modal_app.py

After deploy, open the printed https://xxxx.modal.run URL.
Default login: admin / admin  (change via secret or the change-password page).
Data (subscriptions, credentials) is stored on a Modal Volume and survives redeploys.
"""

import modal
import subprocess
import os

APP_NAME = "merge-sub"
PORT = 3000

# Persistent volume for /app/data (subscriptions + credentials)
volume = modal.Volume.from_name("merge-sub-data", create_if_missing=True)

# Image with Node.js 20 + application source
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("curl", "ca-certificates")
    .run_commands(
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        "node --version && npm --version",
    )
    .add_local_dir(
        local_path=".",  # project root when you run modal from this folder
        remote_path="/app",
        ignore=[
            "**/node_modules/**",
            "**/.git/**",
            "**/data/**",
            "workers/**",
            "install.sh",
            "Dockerfile",
            ".github/**",
            "**/*.pyc",
            "**/__pycache__/**",
            "README.md",
        ],
    )
    .run_commands("cd /app && npm install --omit=dev")
)

app = modal.App(APP_NAME)


@app.function(
    image=image,
    volumes={"/app/data": volume},
    timeout=86400,  # 24h max container lifetime (Modal will recycle as needed)
    # Uncomment after creating the secret (modal secret create merge-sub-secrets ...):
    # secrets=[modal.Secret.from_name("merge-sub-secrets")],
)
@modal.concurrent(max_inputs=50)
@modal.web_server(port=PORT, startup_timeout=90.0)
def web():
    """Launch the Node.js Express server. Modal proxies traffic to this port."""
    env = os.environ.copy()
    env["PORT"] = str(PORT)
    env["SERVER_PORT"] = str(PORT)
    env["DATA_DIR"] = "/app/data"
    # Fallbacks when no Modal Secret is attached / keys missing
    env.setdefault("USERNAME", "admin")
    env.setdefault("PASSWORD", "admin")
    # If SUB_TOKEN is not set, the Node app auto-generates one from hostname

    subprocess.Popen(
        ["node", "app.js"],
        cwd="/app",
        env=env,
    )


@app.local_entrypoint()
def main():
    print("=" * 60)
    print("Merge-sub Modal deployment helper")
    print("=" * 60)
    print()
    print("  modal serve  modal_app.py   # temporary URL, live-reload")
    print("  modal deploy modal_app.py   # persistent production URL")
    print()
    print("Optional secret (recommended):")
    print('  modal secret create merge-sub-secrets \\')
    print("    USERNAME=admin PASSWORD=change_me SUB_TOKEN=my_random_token")
    print()
    print("GitHub Actions needs repo secrets: MODAL_TOKEN_ID, MODAL_TOKEN_SECRET")
    print("=" * 60)
