"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Suspense } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import ComprehensiveResultsView from "@/components/results/ComprehensiveResultsView";
import { generatePDF } from "@/lib/pdf-generator";

function ComprehensiveResultsPageInner() {
	const params = useSearchParams();
	const router = useRouter();
	const sessionId = params?.get("sessionId") || "";
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [resultsData, setResultsData] = useState<any>(null);
	const [sessionList, setSessionList] = useState<Array<{sessionId: string, completedAt: string}>>([]);
	const [showSessionList, setShowSessionList] = useState(false);

	useEffect(() => {
		if (sessionId) {
			fetchComprehensiveResults();
		} else {
			// If no sessionId, fetch list of completed sessions
			fetchCompletedSessions();
			setShowSessionList(true);
		}
	}, [sessionId]);

	const fetchCompletedSessions = async () => {
		try {
			setLoading(true);
			// Try to get list of completed sessions from localStorage or API
			const storedSessions = localStorage.getItem('completed_sessions');
			if (storedSessions) {
				const sessions = JSON.parse(storedSessions);
				setSessionList(sessions);
			}
			setLoading(false);
		} catch (err) {
			console.error('Error fetching sessions:', err);
			setLoading(false);
		}
	};

	const fetchComprehensiveResults = async () => {
		try {
			setLoading(true);
			setError(null);

			// Fetch from comprehensive results API
			const response = await fetch(`/api/mmse/chatbot/results/${sessionId}`);
			const data = await response.json();

			if (data.success && data.data) {
				setResultsData(data.data);
				setShowSessionList(false);
			} else {
				setError(data.error || 'Không thể tải kết quả');
			}
		} catch (err) {
			console.error('Error fetching comprehensive results:', err);
			setError('Lỗi khi tải kết quả từ server');
		} finally {
			setLoading(false);
		}
	};

	const handleExportPDF = async () => {
		if (!resultsData) return;
		
		try {
			await generatePDF(resultsData, sessionId);
		} catch (err) {
			console.error('Error generating PDF:', err);
			alert('Lỗi khi xuất PDF. Vui lòng thử lại.');
		}
	};

	if (showSessionList && !sessionId) {
		return (
			<div className="min-h-screen bg-gray-50 p-6">
				<div className="max-w-4xl mx-auto">
					<h1 className="text-3xl font-bold text-gray-900 mb-6">Chọn Session để xem báo cáo</h1>
					{sessionList.length > 0 ? (
						<div className="space-y-4">
							{sessionList.map((session) => (
								<div
									key={session.sessionId}
									onClick={() => router.push(`/results/comprehensive?sessionId=${session.sessionId}`)}
									className="bg-white p-4 rounded-lg shadow cursor-pointer hover:shadow-lg transition-shadow"
								>
									<p className="font-semibold">Session: {session.sessionId}</p>
									<p className="text-sm text-gray-600">
										Hoàn thành: {new Date(session.completedAt).toLocaleString('vi-VN')}
									</p>
								</div>
							))}
						</div>
					) : (
						<div className="bg-white p-8 rounded-lg shadow text-center">
							<p className="text-gray-600">Chưa có session nào hoàn thành</p>
							<p className="text-sm text-gray-500 mt-2">
								Vui lòng hoàn thành bài đánh giá để xem báo cáo chi tiết
							</p>
						</div>
					)}
				</div>
			</div>
		);
	}

	if (loading) {
		return (
			<div className="flex items-center justify-center min-h-screen">
				<div className="text-center">
					<Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
					<p className="text-gray-600">Đang tải kết quả đánh giá...</p>
				</div>
			</div>
		);
	}

	if (error) {
		return (
			<div className="flex items-center justify-center min-h-screen">
				<div className="text-center max-w-md">
					<AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
					<p className="text-red-600 font-semibold mb-2">Lỗi</p>
					<p className="text-gray-600">{error}</p>
					<button
						onClick={() => router.push('/menu')}
						className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
					>
						Quay lại Menu
					</button>
				</div>
			</div>
		);
	}

	if (!resultsData) {
		return (
			<div className="flex items-center justify-center min-h-screen">
				<div className="text-center">
					<p className="text-gray-600 mb-4">Không tìm thấy dữ liệu kết quả</p>
					<button
						onClick={() => router.push('/menu')}
						className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
					>
						Quay lại Menu
					</button>
				</div>
			</div>
		);
	}

	return (
		<ComprehensiveResultsView 
			data={resultsData} 
			onExportPDF={handleExportPDF}
		/>
	);
}

export default function ComprehensiveResultsPage() {
	return (
		<Suspense fallback={
			<div className="flex items-center justify-center min-h-screen">
				<Loader2 className="w-12 h-12 animate-spin text-blue-600" />
			</div>
		}>
			<ComprehensiveResultsPageInner />
		</Suspense>
	);
}

