// app/page.tsx
"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Brain, CheckCircle, Fish, Shell, TrendingUp, Shield, Target, X } from "lucide-react";
import { useRouter } from "next/navigation";
import PersonalInfoForm from "@/components/PersonalInfoForm";
import { motion } from "framer-motion";

// Dynamically import Clerk components to avoid SSG issues
const ClerkLoaded = dynamic(
	() => import("@clerk/nextjs").then((mod) => mod.ClerkLoaded),
	{ ssr: false }
);
const SignedIn = dynamic(
	() => import("@clerk/nextjs").then((mod) => mod.SignedIn),
	{ ssr: false }
);
const SignedOut = dynamic(
	() => import("@clerk/nextjs").then((mod) => mod.SignedOut),
	{ ssr: false }
);
const SignInButton = dynamic(
	() => import("@clerk/nextjs").then((mod) => mod.SignInButton),
	{ ssr: false }
);
const SignUpButton = dynamic(
	() => import("@clerk/nextjs").then((mod) => mod.SignUpButton),
	{ ssr: false }
);

interface UserState {
	isLoggedIn: boolean;
	hasCompletedProfile: boolean;
	userInfo: any;
}

export default function Home() {
	const [userState, setUserState] = useState<UserState>({
		isLoggedIn: false,
		hasCompletedProfile: false,
		userInfo: null,
	});
	const [showForm, setShowForm] = useState(false);
	const [isClient, setIsClient] = useState(false);
	const router = useRouter();

	// Mark as client-side rendered
	useEffect(() => {
		setIsClient(true);
	}, []);

	useEffect(() => {
		// Only access localStorage on client side
		if (typeof window !== 'undefined') {
			try {
				const completed = localStorage.getItem("profileCompleted") === "true";
				setUserState((prev) => ({ ...prev, hasCompletedProfile: completed }));
			} catch {}
		}
	}, []);

	const handleFormSuccess = () => {
		setUserState((prev) => ({ ...prev, hasCompletedProfile: true }));
		setShowForm(false);
		router.push("/menu");
	};

	const renderCTA = () => {
		if (userState.isLoggedIn && userState.hasCompletedProfile) {
			return (
				<Button
					size="default"
					variant="primaryOutline"
					className="w-full bg-white/10 border-2 border-white/30 text-white hover:bg-white/20 hover:border-white/50 font-semibold shadow-xl backdrop-blur-md transform hover:scale-105 transition-all duration-200 text-xs py-2"
					onClick={() => router.push("/menu")}
				>
					Tiếp tục chăm sóc trí nhớ
				</Button>
			);
		}

		if (userState.isLoggedIn && !userState.hasCompletedProfile) {
			return (
				<div className="space-y-3">
					<Button
						size="default"
						variant="secondary"
						className="w-full bg-gradient-to-r from-yellow-400 via-orange-400 to-yellow-500 text-white hover:from-yellow-500 hover:via-orange-500 hover:to-yellow-600 font-bold shadow-xl backdrop-blur-md border-0 transform hover:scale-105 transition-all duration-200 text-xs py-2"
						onClick={() => setShowForm(true)}
					>
						📝 Hoàn tất hồ sơ
					</Button>
				</div>
			);
		}

		// Not logged in → show Clerk modal buttons (only on client side)
		if (!isClient) {
			return (
				<div className="flex flex-col gap-y-2">
					<Button
						size="default"
						variant="secondary"
						className="w-full bg-gradient-to-r from-yellow-400 via-orange-400 to-yellow-500 text-white font-bold shadow-xl backdrop-blur-md border-0 text-xs py-2"
						disabled
					>
						Đang tải...
					</Button>
				</div>
			);
		}

		return (
			<ClerkLoaded>
				<SignedOut>
					<div className="flex flex-col gap-y-2">
						<SignUpButton mode="modal">
							<Button
								size="default"
								variant="secondary"
								className="w-full bg-gradient-to-r from-yellow-400 via-orange-400 to-yellow-500 text-white hover:from-yellow-500 hover:via-orange-500 hover:to-yellow-600 font-bold shadow-xl backdrop-blur-md border-0 transform hover:scale-105 transition-all duration-200 text-xs py-2"
							>
								📝 Đăng ký
							</Button>
						</SignUpButton>
						<SignInButton mode="modal">
							<Button
								size="default"
								variant="primaryOutline"
								className="w-full bg-white/10 border-2 border-white/30 text-white hover:bg-white/20 hover:border-white/50 font-semibold shadow-xl backdrop-blur-md transform hover:scale-105 transition-all duration-200 text-xs py-2"
							>
								🔑 Đăng nhập
							</Button>
						</SignInButton>
					</div>
				</SignedOut>
				<SignedIn>
					<div className="flex flex-col gap-y-2">
						{!userState.hasCompletedProfile ? (
							<Button
								size="default"
								variant="secondary"
								className="w-full bg-gradient-to-r from-yellow-400 via-orange-400 to-yellow-500 text-white hover:from-yellow-500 hover:via-orange-500 hover:to-yellow-600 font-bold shadow-xl backdrop-blur-md border-0 transform hover:scale-105 transition-all duration-200 text-xs py-2"
								onClick={() => setShowForm(true)}
							>
								📝 Hoàn tất hồ sơ
							</Button>
						) : (
							<Button
								size="default"
								variant="primaryOutline"
								className="w-full bg-white/10 border-2 border-white/30 text-white hover:bg-white/20 hover:border-white/50 font-semibold shadow-xl backdrop-blur-md transform hover:scale-105 transition-all duration-200 text-xs py-2"
								onClick={() => router.push('/menu')}
							>
								➡️ Tiếp tục
							</Button>
						)}
					</div>
				</SignedIn>
			</ClerkLoaded>
		);
	};

	return (
		<div className="min-h-screen w-full bg-gradient-to-br from-blue-900 via-blue-700 via-cyan-600 to-teal-500 relative overflow-x-hidden overflow-y-auto">
			{/* Enhanced Underwater Ocean Effects */}
			<div className="absolute inset-0 overflow-hidden">
				{/* Animated Water Waves */}
				<div className="absolute top-0 left-0 w-full h-full">
					<svg className="absolute top-0 left-0 w-full h-full" viewBox="0 0 1200 600" preserveAspectRatio="none">
						<defs>
							<linearGradient id="oceanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
								<stop offset="0%" stopColor="rgba(255,255,255,0.15)" />
								<stop offset="50%" stopColor="rgba(255,255,255,0.08)" />
								<stop offset="100%" stopColor="rgba(255,255,255,0.12)" />
							</linearGradient>
						</defs>
						{/* Primary wave layer */}
						<path d="M0,300 Q300,250 600,300 T1200,300 V600 H0 Z" fill="url(#oceanGradient)" className="animate-pulse">
							<animate attributeName="d" dur="10s" repeatCount="indefinite"
								values="M0,300 Q300,250 600,300 T1200,300 V600 H0 Z;
										M0,300 Q300,350 600,280 T1200,300 V600 H0 Z;
										M0,300 Q300,220 600,320 T1200,300 V600 H0 Z;
										M0,300 Q300,280 600,300 T1200,300 V600 H0 Z"/>
						</path>
						{/* Secondary wave layer */}
						<path d="M0,380 Q400,330 800,380 T1200,380 V600 H0 Z" fill="url(#oceanGradient)" opacity="0.7" className="animate-pulse">
							<animate attributeName="d" dur="8s" repeatCount="indefinite"
								values="M0,380 Q400,330 800,380 T1200,380 V600 H0 Z;
										M0,380 Q400,430 800,360 T1200,380 V600 H0 Z;
										M0,380 Q400,300 800,420 T1200,380 V600 H0 Z;
										M0,380 Q400,360 800,380 T1200,380 V600 H0 Z"/>
						</path>
						{/* Tertiary wave layer */}
						<path d="M0,450 Q500,400 1000,450 T1200,450 V600 H0 Z" fill="url(#oceanGradient)" opacity="0.5" className="animate-pulse">
							<animate attributeName="d" dur="10s" repeatCount="indefinite"
								values="M0,450 Q500,400 1000,450 T1200,450 V600 H0 Z;
										M0,450 Q500,480 1000,430 T1200,450 V600 H0 Z;
										M0,450 Q500,380 1000,470 T1200,450 V600 H0 Z;
										M0,450 Q500,420 1000,450 T1200,450 V600 H0 Z"/>
						</path>
					</svg>
				</div>

				{/* Swimming Golden Fish Icons */}
				<div className="absolute top-16 right-16 text-yellow-200/20 animate-bounce">
					<Fish className="w-20 h-20 rotate-12 animate-pulse" style={{animationDelay: '0s'}} />
				</div>
				<div className="absolute top-32 left-20 text-yellow-200/15 animate-bounce">
					<Fish className="w-14 h-14 -rotate-45 animate-pulse" style={{animationDelay: '1s'}} />
				</div>
				<div className="absolute top-1/3 right-1/4 text-yellow-200/12 animate-bounce">
					<Fish className="w-16 h-16 rotate-90 animate-pulse" style={{animationDelay: '2s'}} />
				</div>
				<div className="absolute top-2/3 left-1/3 text-yellow-200/18 animate-bounce">
					<Fish className="w-12 h-12 rotate-180 animate-pulse" style={{animationDelay: '0.5s'}} />
				</div>
				<div className="absolute bottom-32 right-20 text-yellow-200/10 animate-bounce">
					<Fish className="w-18 h-18 rotate-45 animate-pulse" style={{animationDelay: '1.5s'}} />
				</div>
				<div className="absolute bottom-48 left-1/4 text-yellow-200/14 animate-bounce">
					<Fish className="w-10 h-10 -rotate-90 animate-pulse" style={{animationDelay: '2.5s'}} />
				</div>
				<div className="absolute top-1/4 right-1/2 text-yellow-200/16 animate-bounce">
					<Fish className="w-8 h-8 rotate-135 animate-pulse" style={{animationDelay: '3s'}} />
				</div>
				<div className="absolute bottom-1/4 left-1/2 text-yellow-200/11 animate-bounce">
					<Fish className="w-15 h-15 rotate-225 animate-pulse" style={{animationDelay: '0.8s'}} />
				</div>

				{/* Shell decorations with gentle sway */}
				<div className="absolute bottom-32 left-16 text-yellow-200/12 animate-pulse">
					<Shell className="w-14 h-14 animate-pulse" style={{animationDelay: '3s'}} />
				</div>
				<div className="absolute bottom-56 right-1/3 text-yellow-200/08 animate-pulse">
					<Shell className="w-12 h-12 rotate-180 animate-pulse" style={{animationDelay: '2.5s'}} />
				</div>
				<div className="absolute top-3/4 left-1/4 text-yellow-200/10 animate-pulse">
					<Shell className="w-10 h-10 rotate-90 animate-pulse" style={{animationDelay: '4s'}} />
				</div>

				{/* Enhanced bubbles with varying sizes and colors */}
				<div className="absolute top-28 right-1/3 w-4 h-4 bg-white/35 rounded-full animate-bounce border border-white/40"></div>
				<div className="absolute top-1/2 left-1/4 w-3 h-3 bg-cyan-200/30 rounded-full animate-bounce border border-cyan-200/40" style={{animationDelay: '0.5s'}}></div>
				<div className="absolute bottom-1/3 right-1/4 w-5 h-5 bg-blue-200/25 rounded-full animate-bounce border border-blue-200/35" style={{animationDelay: '1s'}}></div>
				<div className="absolute top-3/4 left-1/2 w-2 h-2 bg-teal-200/20 rounded-full animate-bounce border border-teal-200/30" style={{animationDelay: '1.5s'}}></div>
				<div className="absolute bottom-1/4 left-1/3 w-3 h-3 bg-white/30 rounded-full animate-bounce border border-white/35" style={{animationDelay: '2s'}}></div>
				<div className="absolute top-1/3 right-1/2 w-2 h-2 bg-cyan-200/25 rounded-full animate-bounce border border-cyan-200/30" style={{animationDelay: '2.5s'}}></div>
				<div className="absolute bottom-2/3 left-20 w-4 h-4 bg-blue-200/20 rounded-full animate-bounce border border-blue-200/25" style={{animationDelay: '3s'}}></div>
				<div className="absolute top-1/6 right-20 w-3 h-3 bg-teal-200/15 rounded-full animate-bounce border border-teal-200/20" style={{animationDelay: '0.8s'}}></div>

				{/* Water ripples effect */}
				<div className="absolute inset-0 pointer-events-none">
					<div className="absolute top-8 left-8 w-40 h-40 border-2 border-white/6 rounded-full animate-ping" style={{animationDelay: '0s', animationDuration: '5s'}}></div>
					<div className="absolute top-32 right-16 w-32 h-32 border-2 border-cyan-200/4 rounded-full animate-ping" style={{animationDelay: '2s', animationDuration: '6s'}}></div>
					<div className="absolute bottom-24 left-1/4 w-36 h-36 border-2 border-blue-200/5 rounded-full animate-ping" style={{animationDelay: '1s', animationDuration: '7s'}}></div>
					<div className="absolute top-2/3 right-1/3 w-28 h-28 border-2 border-teal-200/3 rounded-full animate-ping" style={{animationDelay: '3s', animationDuration: '4s'}}></div>
				</div>
			</div>

			{/* Main Content */}
			<div className="relative z-10">
				{/* Hero Section */}
				<motion.div
					initial={{ opacity: 0, y: 50 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.8 }}
					className="text-center py-4 px-4"
				>
					<div className="max-w-4xl mx-auto">
						<motion.div
							initial={{ scale: 0.8 }}
							animate={{ scale: 1 }}
							transition={{ duration: 0.6, delay: 0.2 }}
						>
							<Brain className="w-16 h-16 mx-auto mb-4 text-yellow-300 animate-pulse" />
						</motion.div>
						<h1 className="text-3xl lg:text-5xl font-extrabold text-white mb-3 leading-tight">
							 <span className="text-yellow-300">Cá Vàng</span>
						</h1>
						<p className="text-lg lg:text-xl text-cyan-100 mb-2 font-medium">
							Ứng dụng nhỏ, ký ức lớn
						</p>
						<p className="text-base text-cyan-50 max-w-2xl mx-auto leading-relaxed">
							Chăm sóc trí nhớ,
							rèn luyện nhận thức mỗi ngày với công nghệ AI tiên tiến.
						</p>
					</div>
				</motion.div>

				{/* Features Section */}
				<motion.div
					initial={{ opacity: 0 }}
					animate={{ opacity: 1 }}
					transition={{ duration: 0.8, delay: 0.4 }}
					className="px-4 py-2"
				>
					<div className="max-w-6xl mx-auto">
						<h2 className="text-xl lg:text-2xl font-bold text-center text-cyan-200  mb-6">
							Tính năng nổi bật
						</h2>
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
							<motion.div
								whileHover={{ scale: 1.05, y: -5 }}
								transition={{ type: "spring", stiffness: 300 }}
							>
								<Card className="p-4 bg-white/10 backdrop-blur-md border-white/20 text-white hover:bg-white/15 transition-all duration-300">
									<div className="flex items-center mb-3">
										<div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full mr-3">
											<Target className="w-6 h-6 text-white" />
										</div>
										<h3 className="text-lg font-semibold">MMSE Assessment</h3>
									</div>
									<p className="text-cyan-100 text-sm leading-relaxed">
										Đánh giá nhận thức toàn diện với trí tuệ nhân tạo và phân tích âm thanh tiên tiến.
									</p>
								</Card>
							</motion.div>

							<motion.div
								whileHover={{ scale: 1.05, y: -5 }}
								transition={{ type: "spring", stiffness: 300 }}
							>
								<Card className="p-4 bg-white/10 backdrop-blur-md border-white/20 text-white hover:bg-white/15 transition-all duration-300">
									<div className="flex items-center mb-3">
										<div className="p-2 bg-gradient-to-br from-green-500 to-teal-500 rounded-full mr-3">
											<Shield className="w-6 h-6 text-white" />
										</div>
										<h3 className="text-lg font-semibold">Bảo mật tuyệt đối</h3>
									</div>
									<p className="text-cyan-100 text-sm leading-relaxed">
										Dữ liệu được mã hóa và bảo vệ an toàn với các tiêu chuẩn bảo mật cao nhất.
									</p>
								</Card>
							</motion.div>

							<motion.div
								whileHover={{ scale: 1.05, y: -5 }}
								transition={{ type: "spring", stiffness: 300 }}
							>
								<Card className="p-4 bg-white/10 backdrop-blur-md border-white/20 text-white hover:bg-white/15 transition-all duration-300">
									<div className="flex items-center mb-3">
										<div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full mr-3">
											<TrendingUp className="w-6 h-6 text-white" />
										</div>
										<h3 className="text-lg font-semibold">Theo dõi tiến độ</h3>
									</div>
									<p className="text-cyan-100 text-sm leading-relaxed">
										Theo dõi và phân tích sự cải thiện của trí nhớ qua thời gian với báo cáo chi tiết.
									</p>
								</Card>
							</motion.div>
						</div>
					</div>
				</motion.div>

				{/* Stats Section - Compact */}
				<motion.div
					initial={{ opacity: 0, y: 30 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.8, delay: 0.6 }}
					className="px-4 py-1"
				>
					
				</motion.div>

				{/* Benefits Section - Compact */}
				<motion.div
					initial={{ opacity: 0 }}
					animate={{ opacity: 1 }}
					transition={{ duration: 0.8, delay: 0.7 }}
					className="px-4 py-2"
				>
					<div className="max-w-4xl mx-auto">
						<div className="flex flex-wrap justify-center items-center gap-x-6 gap-y-2 text-sm">
							<div className="flex items-center space-x-2">
								<CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
								<span className="text-white">Đánh giá thông minh</span>
							</div>
							<div className="flex items-center space-x-2">
								<CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
								<span className="text-white">AI tiên tiến</span>
							</div>
							<div className="flex items-center space-x-2">
								<CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
								<span className="text-white">Dễ sử dụng</span>
							</div>
							<div className="flex items-center space-x-2">
								<CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
								<span className="text-white">Theo dõi liên tục</span>
							</div>
						</div>
					</div>
				</motion.div>

				{/* CTA Section - Compact */}
				<motion.div
					initial={{ opacity: 0, y: 30 }}
					animate={{ opacity: 1, y: 0 }}
					transition={{ duration: 0.8, delay: 0.8 }}
					className="px-4 py-3"
				>
					<div className="max-w-md mx-auto text-center">
						<h2 className="text-lg lg:text-xl font-bold text-white mb-2">Bắt đầu hành trình</h2>
						<p className="text-cyan-100 mb-4 text-xs">Tham gia cùng cộng đồng chăm sóc sức khỏe trí nhớ</p>
						<div className="flex flex-col gap-y-2">{renderCTA()}</div>
					</div>
				</motion.div>
			</div>

			{/* Centered modal for personal info form */}
			{showForm && (
				<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
					<div className="relative w-full max-w-2xl mx-4 rounded-2xl border border-white/60 bg-white/95 shadow-2xl">
						<button
							onClick={() => setShowForm(false)}
							className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-white/80 hover:bg-white text-gray-700 shadow"
							aria-label="Close"
						>
							<X className="h-4 w-4" />
						</button>
						<div className="px-5 pt-5 pb-4 border-b border-gray-200/60">
							<h3 className="text-lg font-semibold text-gray-900">Thông tin cá nhân</h3>
							<p className="text-xs text-gray-500 mt-1">Điền chính xác để cá nhân hóa trải nghiệm</p>
						</div>
						<div className="max-h-[70vh] overflow-y-auto p-4">
							<PersonalInfoForm onSubmitSuccess={handleFormSuccess} />
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
