import NewsResearch from "@/components/info/NewsResearch";
import NewsDetail from "@/components/info/NewsDetail";

interface PageProps {
  searchParams?: Promise<any>;
}

export default async function InfoNewsPage({ searchParams }: PageProps) {
  const sp = (await searchParams) as { page?: string; url?: string } | undefined;
  const page = sp?.page ?? '1';
  const url = sp?.url ?? undefined;

  if (url) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50">
        <NewsDetail articleUrl={url} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50">
      <NewsResearch />
    </div>
  );
}


