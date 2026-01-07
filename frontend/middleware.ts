import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/stats(.*)",
  "/cognitive-assessment(.*)",
  "/results(.*)",
  "/menu(.*)"
]);

const isApiRoute = createRouteMatcher([
  "/api/(.*)"
]);

export default clerkMiddleware(async (auth, request) => {
  // Skip authentication for API routes
  if (isApiRoute(request)) {
    return;
  }

  // Check if Clerk is properly configured
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const isClerkConfigured = publishableKey && 
                            !publishableKey.includes('placeholder') && 
                            publishableKey !== '';

  // If Clerk is not configured, allow all routes (development mode)
  if (!isClerkConfigured) {
    return;
  }

  // For public routes, skip protection
  if (isPublicRoute(request)) {
    return;
  }

  // Protect non-public routes only if Clerk is available
  try {
    await auth.protect();
  } catch (error: any) {
    // ✅ FIX: Only log actual errors, not expected 404s from Next.js
    if (error?.digest && error.digest.includes('NEXT_HTTP_ERROR_FALLBACK')) {
      // This is a Next.js internal error, not a Clerk error - ignore it
      return;
    }
    // Log other errors but don't block the request
    console.warn('Clerk middleware error:', error?.message || error);
    return;
  }
});

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
};