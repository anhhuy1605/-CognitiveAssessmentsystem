module.exports = {
  "apps": [
    {
      "name": "mmse-backend",
      "script": "src/index.js",
      "cwd": "/opt/backend",
      "instances": "max",
      "exec_mode": "cluster",
      "env": {
        "NODE_ENV": "production",
        "PORT": "5000"
      },
      "error_file": "/var/log/mmse/error.log",
      "out_file": "/var/log/mmse/out.log",
      "log_file": "/var/log/mmse/combined.log",
      "time": true,
      "max_memory_restart": "1G",
      "node_args": "--max-old-space-size=1024"
    }
  ]
}