from __future__ import annotations

import json
import os
from typing import TypeVar

from pydantic import BaseModel

from backend.models import (
    LearningRecommendationResponse,
    QuizQuestion,
    QuizResponse,
    LearningStep,
)

T = TypeVar("T", bound=BaseModel)


class GeminiService:
    """All Gemini interaction is kept in this class so the API layer stays simple."""

    def __init__(self) -> None:
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
        self.demo_mode = os.getenv("DEMO_MODE", "false").strip().lower() == "true"
        api_key = os.getenv("GEMINI_API_KEY", "").strip()

        self.configured = bool(api_key)
        self.client = None
        if api_key:
            try:
                from google import genai
            except ImportError as exc:
                raise RuntimeError(
                    "google-genai is not installed. Run: pip install -r requirements.txt"
                ) from exc
            self.client = genai.Client(api_key=api_key)

    def _ensure_ready(self) -> None:
        if self.demo_mode:
            return
        if not self.client:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Add it to .env or set DEMO_MODE=true."
            )

    def _generate_text(
        self,
        prompt: str,
        *,
        temperature: float = 0.4,
        max_output_tokens: int = 1200,
    ) -> str:
        self._ensure_ready()

        if self.demo_mode:
            return self._demo_text(prompt)

        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            ),
        )

        text = getattr(response, "text", None)
        if not text or not text.strip():
            raise RuntimeError("Gemini returned an empty response.")

        return text.strip()

    def _generate_structured(
        self,
        prompt: str,
        schema: type[T],
        *,
        temperature: float = 0.35,
        max_output_tokens: int = 2400,
    ) -> T:
        self._ensure_ready()

        if self.demo_mode:
            return self._demo_structured(prompt, schema)

        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )

        # google-genai exposes generated text through response.text.
        raw = getattr(response, "text", None)
        if not raw:
            raise RuntimeError("Gemini returned no structured response.")

        try:
            return schema.model_validate_json(raw)
        except Exception:
            # Defensive cleanup for a model response containing JSON fences.
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.removeprefix("```json").removeprefix("```")
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            try:
                return schema.model_validate(json.loads(cleaned))
            except Exception as exc:
                raise RuntimeError(
                    f"Gemini returned invalid structured data: {exc}"
                ) from exc

    def answer_question(self, question: str) -> str:
        prompt = f"""
You are EduGenie, a friendly AI tutor.

Answer the student's question accurately and clearly.
Use simple language first. Add a short example when it improves understanding.
If the question is ambiguous, state the assumption.
Do not invent citations.

Student question:
{question}
"""
        return self._generate_text(prompt, temperature=0.35, max_output_tokens=900)

    def explain_topic(self, topic: str) -> str:
        prompt = f"""
You are EduGenie, an AI tutor.

Explain this topic for a learner using simple language.

Use these sections:
1. Simple definition
2. How it works
3. Example
4. Key points to remember

Avoid unnecessary jargon.

Topic:
{topic}
"""
        return self._generate_text(prompt, temperature=0.4, max_output_tokens=1300)

    def summarize_text(self, text: str) -> str:
        prompt = f"""
Summarize the following study material.

Rules:
- Keep the important facts.
- Remove repetition.
- Use concise bullets where helpful.
- Do not add information that is not in the supplied text.

Study material:
{text}
"""
        return self._generate_text(prompt, temperature=0.25, max_output_tokens=1100)

    def generate_quiz(self, text: str, question_count: int) -> QuizResponse:
        prompt = f"""
Create exactly {question_count} multiple-choice questions from the study material.

Rules:
- Exactly 4 options per question.
- The answer must exactly match one option.
- Questions should test understanding.
- Add a short explanation for the correct answer.
- Return only the requested JSON structure.

Study material:
{text}
"""
        result = self._generate_structured(
            prompt,
            QuizResponse,
            temperature=0.3,
            max_output_tokens=2500,
        )

        if len(result.questions) != question_count:
            raise RuntimeError(
                f"Gemini returned {len(result.questions)} questions instead of {question_count}."
            )

        for item in result.questions:
            if len(item.options) != 4:
                raise RuntimeError("Each quiz question must contain exactly four options.")
            if item.answer not in item.options:
                raise RuntimeError("Quiz answer does not match any option.")

        return result

    def get_learning_recommendations(
        self, topic: str
    ) -> LearningRecommendationResponse:
        prompt = f"""
You are EduGenie, an adaptive learning-path designer.

Create a practical learning path for:
{topic}

Include beginner, intermediate, and advanced stages when appropriate.

For each stage provide:
- level
- estimated time
- key topics in learning order
- resource types or well-known resource names

Do not fabricate URLs.

Also provide:
- a short overview
- adaptive tips that help a learner adjust pace and practice depth

Return only the requested JSON structure.
"""
        result = self._generate_structured(
            prompt,
            LearningRecommendationResponse,
            temperature=0.4,
            max_output_tokens=3000,
        )
        result.topic = topic
        return result

    @staticmethod
    def _demo_text(prompt: str) -> str:
        lowered = prompt.lower()

        if "summarize" in lowered:
            return (
                "• Demo summary: the supplied study material was condensed into its "
                "main ideas.\n"
                "• In real mode, Gemini will summarize the exact text you provide.\n"
                "• Switch DEMO_MODE=false and add GEMINI_API_KEY for live AI output."
            )

        if "explain" in lowered:
            return (
                "Simple definition: This is a demo explanation generated locally.\n\n"
                "How it works: EduGenie sends the topic to the Gemini-backed backend "
                "when live mode is enabled.\n\n"
                "Example: Replace DEMO_MODE=true with false to receive a real Gemini "
                "explanation.\n\n"
                "Key points: The browser never receives your Gemini API key."
            )

        return (
            "Demo answer: EduGenie is running correctly. This response is local because "
            "DEMO_MODE=true. Add a Gemini API key and set DEMO_MODE=false for live AI."
        )

    @staticmethod
    def _demo_structured(prompt: str, schema: type[T]) -> T:
        if schema is QuizResponse:
            return schema.model_validate(
                {
                    "questions": [
                        {
                            "question": "What is EduGenie designed to provide?",
                            "options": [
                                "Learning assistance",
                                "Video editing",
                                "File compression",
                                "Game development",
                            ],
                            "answer": "Learning assistance",
                            "explanation": "EduGenie is a learning assistant.",
                        },
                        {
                            "question": "Which component communicates with Gemini?",
                            "options": [
                                "FastAPI backend",
                                "CSS file",
                                "Browser title",
                                "Footer",
                            ],
                            "answer": "FastAPI backend",
                            "explanation": "The backend keeps the Gemini API key server-side.",
                        },
                        {
                            "question": "What does the quiz module create?",
                            "options": [
                                "Multiple-choice questions",
                                "Database tables",
                                "Images",
                                "Audio tracks",
                            ],
                            "answer": "Multiple-choice questions",
                            "explanation": "The quiz module generates MCQs from study content.",
                        },
                    ]
                }
            )

        if schema is LearningRecommendationResponse:
            return schema.model_validate(
                {
                    "topic": "Demo topic",
                    "overview": "A sample adaptive path for testing the application.",
                    "steps": [
                        {
                            "level": "Beginner",
                            "estimated_time": "1-2 weeks",
                            "key_topics": [
                                "Fundamentals",
                                "Terminology",
                                "Simple exercises",
                            ],
                            "resources": [
                                "Interactive tutorials",
                                "Beginner documentation",
                            ],
                        },
                        {
                            "level": "Intermediate",
                            "estimated_time": "2-3 weeks",
                            "key_topics": [
                                "Practical projects",
                                "Problem solving",
                                "Review",
                            ],
                            "resources": [
                                "Practice platforms",
                                "Project-based tutorials",
                            ],
                        },
                        {
                            "level": "Advanced",
                            "estimated_time": "3-4 weeks",
                            "key_topics": [
                                "Optimization",
                                "Advanced projects",
                                "Independent study",
                            ],
                            "resources": [
                                "Official documentation",
                                "Advanced books",
                            ],
                        },
                    ],
                    "adaptive_tips": [
                        "Slow down and revisit fundamentals when practice feels difficult.",
                        "Increase project complexity after the basics become comfortable.",
                        "Use spaced review to retain important concepts.",
                    ],
                }
            )

        raise RuntimeError(f"Unsupported demo schema: {schema.__name__}")
