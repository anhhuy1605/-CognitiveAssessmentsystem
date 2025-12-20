export const clerkConfigOptions = {
  // Enable multiple sessions if needed
  allowMultipleSessions: false,
  
  // Set default redirect URLs
  signInUrl: '/sign-in',
  signUpUrl: '/sign-up',
  afterSignInUrl: '/dashboard',
  afterSignUpUrl: '/profile-check',
  afterSignOutUrl: '/',
  
  // Development settings
  debug: process.env.NODE_ENV === 'development',
  
  // Session management
  sessionExpiryInSeconds: 60 * 60 * 24 * 7, // 7 days
};

export default clerkConfigOptions;
