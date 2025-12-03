ALTER TABLE "training_samples" ADD COLUMN "session_id" varchar(255) NOT NULL;--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "user_id" varchar(255) NOT NULL;--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "user_email" varchar(255);--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "user_name" varchar(255);--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "question_id" integer;--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "question_text" text;--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "audio_filename" varchar(255);--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "audio_url" text;--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "auto_transcript" text;--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "manual_transcript" text;--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "created_at" timestamp with time zone DEFAULT now();--> statement-breakpoint
ALTER TABLE "training_samples" ADD COLUMN "updated_at" timestamp with time zone DEFAULT now();--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "sessionId";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "userId";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "userInfo";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "startedAt";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "completedAt";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "totalQuestions";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "answeredQuestions";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "completionRate";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "memoryScore";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "cognitiveScore";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "finalMmseScore";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "overallGptScore";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "questionResults";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "audioFiles";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "recordingsPath";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "cognitiveAnalysis";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "audioFeatures";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "status";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "usageMode";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "assessmentType";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "createdAt";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "updatedAt";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "userEmail";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "userName";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "questionId";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "questionText";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "audioFilename";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "audioUrl";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "autoTranscript";--> statement-breakpoint
ALTER TABLE "training_samples" DROP COLUMN "manualTranscript";