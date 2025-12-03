export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  try {
    // Accept any payload and return ok for build-time typing
    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) {
    return new Response(JSON.stringify({ success: false }), { status: 500 });
  }
}


