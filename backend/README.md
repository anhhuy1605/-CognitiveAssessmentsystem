# Backend Directory

This directory contains the Express.js backend server for the MMSE system.

## Structure:
- `src/` - Source code
  - `routes/` - API route handlers
  - `middleware/` - Express middleware
  - `controllers/` - Business logic controllers
  - `services/` - Service layer (database, external APIs)
  - `utils/` - Utility functions
  - `models/` - Data models and validation
- `config/` - Configuration files
- `logs/` - Application logs

## Deployment: Hetzner VPS
- Express.js server
- Nginx reverse proxy
- PM2 process manager
- PostgreSQL database connection
