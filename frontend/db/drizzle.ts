import 'server-only';
import { drizzle } from 'drizzle-orm/neon-http';
import { neon } from "@neondatabase/serverless"
import * as schema from "./schema"

// Lazy initialization to avoid build-time errors
// DATABASE_URL is only required at runtime, not during Next.js build
let db: ReturnType<typeof drizzle> | null = null;

function getDb() {
  if (db) return db;
  
  const databaseUrl = process.env.DATABASE_URL;
  
  // Only validate at runtime, not during build
  if (!databaseUrl) {
    // During build time, return a mock or throw a more helpful error
    if (process.env.NODE_ENV === 'production' && process.env.NEXT_PHASE === 'phase-production-build') {
      // Return null during build - API routes won't be called during build anyway
      console.warn('DATABASE_URL not set during build - this is expected');
      return null as any;
    }
    throw new Error('DATABASE_URL is not defined. Please set it in your environment variables.');
  }

  if (!databaseUrl.startsWith('postgresql://') && !databaseUrl.startsWith('postgres://')) {
    throw new Error('DATABASE_URL must start with postgresql:// or postgres://');
  }

  const sql = neon(databaseUrl);
  db = drizzle(sql, { schema });
  return db;
}

// Export a proxy that lazily initializes the db
const dbProxy = new Proxy({} as ReturnType<typeof drizzle>, {
  get(_, prop) {
    const database = getDb();
    if (!database) {
      throw new Error('Database not initialized - DATABASE_URL may not be set');
    }
    return (database as any)[prop];
  }
});

export default dbProxy;

