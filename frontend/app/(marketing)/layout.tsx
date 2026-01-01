import Link from "next/link";
import { Newspaper } from "lucide-react";

type Props = {
    children: React.ReactNode  ;
};

const MarketingLayout = ({children}: Props) => {
    return (
        <div className="h-screen flex flex-col">
            {/* Global quick News link (all breakpoints) */}
            <div className="fixed top-4 right-4 z-[100]">
                <Link href="/info/news" aria-label="Tin tức & nghiên cứu" className="inline-flex items-center justify-center rounded-xl p-2 bg-indigo-600 text-white shadow-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <Newspaper className="w-5 h-5" />
                </Link>
            </div>
            <main className="flex-1 overflow-y-auto">
                {children}
            </main>
        </div>

    )
}
export default MarketingLayout;
