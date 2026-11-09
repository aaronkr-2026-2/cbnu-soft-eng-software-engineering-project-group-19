import json
import os
import base64
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AIConfigurationError(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


def _chat_completion(messages: list[dict], *, temperature: float = 0.2) -> dict:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise AIConfigurationError("AI_API_KEY is not configured")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": os.getenv("AI_MODEL", "gpt-4o-mini"),
        "response_format": {"type": "json_object"},
        "messages": messages,
        "temperature": temperature,
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read())
        return json.loads(result["choices"][0]["message"]["content"])
    except HTTPError as exc:
        raise AIProviderError(f"AI service returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AIProviderError("AI service did not return valid JSON") from exc


def translate_lesson(title: str, content: str, target_language: str) -> dict[str, str]:
    language_names = {"uz": "Uzbek", "en": "English", "ru": "Russian", "ko": "Korean"}
    if target_language not in language_names:
        raise ValueError("Unsupported translation language")
    result = _chat_completion([
        {"role": "system", "content": (
            f"Translate the lesson title and content into {language_names[target_language]}. "
            "Preserve meaning, headings, lists, markdown, URLs, code blocks, code identifiers, and examples. "
            "Do not summarize or add explanations. Return JSON with string fields title and content."
        )},
        {"role": "user", "content": json.dumps({"title": title[:200], "content": content[:30000]}, ensure_ascii=False)},
    ], temperature=0.1)
    translated_title, translated_content = result.get("title"), result.get("content")
    if not isinstance(translated_title, str) or not translated_title.strip() or not isinstance(translated_content, str) or not translated_content.strip():
        raise AIProviderError("AI service returned an incomplete lesson translation")
    return {"title": translated_title[:200], "content": translated_content}


def translate_course(title: str, description: str | None, category: str, target_language: str) -> dict[str, str | None]:
    language_names = {"uz": "Uzbek", "en": "English", "ru": "Russian", "ko": "Korean"}
    if target_language not in language_names:
        raise ValueError("Unsupported translation language")
    result = _chat_completion([
        {"role": "system", "content": (
            f"Translate the course title, description, and category into {language_names[target_language]}. "
            "Preserve meaning and do not add claims. Return JSON with string fields title, description, and category."
        )},
        {"role": "user", "content": json.dumps({"title": title[:200], "description": (description or "")[:4000], "category": category[:100]}, ensure_ascii=False)},
    ], temperature=0.1)
    translated_title, translated_description, translated_category = result.get("title"), result.get("description"), result.get("category")
    if not isinstance(translated_title, str) or not translated_title.strip() or not isinstance(translated_description, str) or not isinstance(translated_category, str) or not translated_category.strip():
        raise AIProviderError("AI service returned an incomplete course translation")
    return {"title": translated_title[:200], "description": translated_description or None, "category": translated_category[:100]}


def translate_assessment(title: str, questions: list[dict], target_language: str) -> dict:
    language_names = {"uz": "Uzbek", "en": "English", "ru": "Russian", "ko": "Korean"}
    if target_language not in language_names:
        raise ValueError("Unsupported translation language")
    source = [{"prompt": question["prompt"], "choices": question["choices"]} for question in questions]
    result = _chat_completion([
        {"role": "system", "content": (
            f"Translate the assessment title, question prompts, and choices into {language_names[target_language]}. "
            "Preserve the exact question count, choice count, and order. Translate faithfully without changing meaning. "
            "Return JSON with title and questions, each containing prompt and choices."
        )},
        {"role": "user", "content": json.dumps({"title": title, "questions": source}, ensure_ascii=False)},
    ], temperature=0.1)
    translated = result.get("questions")
    if (not isinstance(result.get("title"), str) or not result["title"].strip()
            or not isinstance(translated, list) or len(translated) != len(source)):
        raise AIProviderError("AI service returned an incomplete assessment translation")
    for original, item in zip(source, translated):
        if (not isinstance(item, dict) or not isinstance(item.get("prompt"), str) or not item["prompt"].strip()
                or not isinstance(item.get("choices"), list) or len(item["choices"]) != len(original["choices"])
                or not all(isinstance(choice, str) and choice.strip() for choice in item["choices"])):
            raise AIProviderError("AI service changed the assessment structure")
    return {"title": result["title"], "questions": translated}


def generate_lesson_banner(course_title: str, lesson_title: str, content: str) -> bytes:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise AIConfigurationError("AI_API_KEY is not configured")
    base_url = os.getenv("AI_IMAGE_BASE_URL", os.getenv("AI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
    payload = {
        "model": os.getenv("AI_IMAGE_MODEL", "gpt-image-2.5-flare"),
        "prompt": (
            "Create a polished, inclusive online-learning lesson banner illustration. "
            "Wide 16:9 composition, no text, no logos, no watermark. Depict the lesson topic clearly, "
            "with clean educational editorial art, balanced contrast, and a calm modern palette. "
            f"Course: {course_title[:200]}. Lesson: {lesson_title[:200]}. Context: {content[:1800]}"
        ),
        "size": "1536x864",
        "quality": "low",
        "n": 1,
    }
    request = Request(
        f"{base_url}/images/generations",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read())
        image_bytes = base64.b64decode(result["data"][0]["b64_json"], validate=True)
        if not image_bytes.startswith(b"\x89PNG\r\n\x1a\n") or len(image_bytes) > 12 * 1024 * 1024:
            raise AIProviderError("AI service returned an invalid lesson image")
        return image_bytes
    except HTTPError as exc:
        raise AIProviderError(f"AI image service returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, AIProviderError):
            raise
        raise AIProviderError("AI service did not return a valid lesson image") from exc


def generate_quiz_json(course_title: str, lesson_title: str, material: str) -> dict:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise AIConfigurationError("AI_API_KEY is not configured")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Create a high-quality multiple-choice lesson quiz using only the supplied source material. "
                    "Return JSON with title and questions. Each question must have prompt, choices (4 strings), "
                    "correct_index (zero-based integer), and points (integer 1). Write in the same language as the source. "
                    "Do not invent facts absent from the source. Create 5 distinct questions."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"course": course_title, "lesson": lesson_title, "source_material": material[:24000]},
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.2,
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read())
        return json.loads(result["choices"][0]["message"]["content"])
    except HTTPError as exc:
        raise AIProviderError(f"AI service returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AIProviderError("AI service did not return a valid quiz") from exc


def generate_course_recommendations(interest: str, learner_level: str, language: str, courses: list[dict]) -> dict:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise AIConfigurationError("AI_API_KEY is not configured")
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    payload = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Recommend up to 5 courses from the provided catalog. Rank by the learner's requested topic and "
                    "their quiz-derived level. Only use the supplied course IDs. Return JSON as "
                    "{\"recommendations\":[{\"course_id\":\"...\",\"reason\":\"...\"}]}. "
                    "Write each short reason in the supplied UI language. Do not invent course details."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"interest": interest[:100], "learner_level": learner_level, "ui_language": language, "catalog": courses[:30]},
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.2,
    }
    request = Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read())
        return json.loads(result["choices"][0]["message"]["content"])
    except HTTPError as exc:
        raise AIProviderError(f"AI service returned HTTP {exc.code}") from None
    except (URLError, TimeoutError, KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AIProviderError("AI service did not return valid recommendations") from exc
