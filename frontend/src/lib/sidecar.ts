/**
 * Python sidecar management for Tauri desktop app.
 * Starts the FastAPI server as a child process when running as a Tauri app.
 * When running in browser (dev mode with Vite proxy), this is a no-op.
 */

const IS_TAURI = "__TAURI__" in window;

let sidecarProcess: unknown = null;

/**
 * Start the Python FastAPI backend as a sidecar process.
 * Only runs when inside Tauri; in browser dev mode, the proxy handles it.
 */
export async function startSidecar(): Promise<void> {
  if (!IS_TAURI) {
    console.log("[sidecar] Running in browser mode, skipping sidecar start");
    return;
  }

  try {
    const { Command } = await import("@tauri-apps/plugin-shell");

    // Spawn the Python FastAPI server
    const command = Command.create("python-sidecar", [
      "-m",
      "uvicorn",
      "api.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      "8000",
    ]);

    command.on("error", (error: string) => {
      console.error("[sidecar] Error:", error);
    });

    command.stdout.on("data", (line: string) => {
      console.log("[sidecar:stdout]", line);
    });

    command.stderr.on("data", (line: string) => {
      console.log("[sidecar:stderr]", line);
    });

    sidecarProcess = await command.spawn();
    console.log("[sidecar] Python API started");
  } catch (e) {
    console.error("[sidecar] Failed to start Python API:", e);
  }
}

/**
 * Stop the Python sidecar process.
 */
export async function stopSidecar(): Promise<void> {
  if (sidecarProcess && typeof (sidecarProcess as { kill: () => Promise<void> }).kill === "function") {
    try {
      await (sidecarProcess as { kill: () => Promise<void> }).kill();
      console.log("[sidecar] Python API stopped");
    } catch (e) {
      console.error("[sidecar] Failed to stop Python API:", e);
    }
    sidecarProcess = null;
  }
}
