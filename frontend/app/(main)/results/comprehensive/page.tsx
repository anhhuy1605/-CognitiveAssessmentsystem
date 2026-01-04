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
			
			// Try to fetch from API first (Next.js route that proxies to Flask)
			try {
				const response = await fetch('/api/mmse/chatbot/sessions');
				const data = await response.json();
				
				if (data.success && data.sessions) {
					setSessionList(data.sessions);
					// Also save to localStorage for offline access
					localStorage.setItem('completed_sessions', JSON.stringify(data.sessions));
					setLoading(false);
					return;
				}
			} catch (apiErr) {
				console.warn('API fetch failed, trying localStorage:', apiErr);
			}
			
			// Fallback to localStorage
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

	const handleLoadTestSession = async () => {
		try {
			setLoading(true);
			setError(null);

			// Create test session via API
			const response = await fetch('/api/mmse/chatbot/test/create-full-session', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
				},
			});

			const data = await response.json();

			if (data.success && data.session_id) {
				// Redirect to comprehensive results with test session ID
				router.push(`/results/comprehensive?sessionId=${data.session_id}`);
			} else {
				setError(data.error || 'Không thể tạo test session');
				setLoading(false);
			}
		} catch (err) {
			console.error('Error creating test session:', err);
			setError('Lỗi khi tạo test session từ server');
			setLoading(false);
		}
	};

	const fetchComprehensiveResults = async () => {
		try {
			setLoading(true);
			setError(null);

			console.log('Fetching comprehensive results for sessionId:', sessionId);

			// Fetch from comprehensive results API (Next.js route that proxies to Flask)
			const response = await fetch(`/api/mmse/chatbot/results/${sessionId}`);
			
			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}
			
			const data = await response.json();
			
			console.log('Comprehensive results API response:', {
				success: data.success,
				hasData: !!data.data,
				sessionId: data.session_id,
				error: data.error
			});

			if (data.success && data.data) {
				console.log('Setting results data:', {
					hasAssessment: !!data.data.assessment_result,
					hasFeatures: !!data.data.feature_summary,
					hasMultimodal: !!data.data.multimodal_analysis
				});
				setResultsData(data.data);
				setShowSessionList(false);
			} else {
				const errorMsg = data.error || 'Không thể tải kết quả';
				console.error('API returned error:', errorMsg, data);
				setError(errorMsg);
			}
		} catch (err) {
			console.error('Error fetching comprehensive results:', err);
			setError(err instanceof Error ? err.message : 'Lỗi khi tải kết quả từ server');
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
					<div className="flex justify-between items-center mb-6">
						<h1 className="text-3xl font-bold text-gray-900">Chọn Session để xem báo cáo</h1>
						<button
							onClick={handleLoadTestSession}
							disabled={loading}
							className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
						>
							{loading ? (
								<>
									<Loader2 className="w-4 h-4 animate-spin" />
									<span>Đang tạo...</span>
								</>
							) : (
								<>
									<span>🧪 Load Test Session</span>
								</>
							)}
						</button>
					</div>
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
							<p className="text-sm text-blue-600 mt-4">
								Hoặc click "🧪 Load Test Session" để xem dữ liệu test mẫu
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

