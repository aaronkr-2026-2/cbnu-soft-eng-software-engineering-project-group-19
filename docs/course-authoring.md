# Course authoring

The author workflow follows a familiar online-course structure: a course contains an open subject area, ordered lessons, assessments, and a separate final exam. Coursera course pages commonly combine video, readings, and graded assignments within modules; StudyFlow uses ordered lessons, lesson quizzes, and an author-managed final exam. See [Coursera's course example](https://www.coursera.org/learn/teaching) for that content mix.

## Build a course

1. Sign in through the author portal and create a course with a title, description, and subject area. The subject area can be IT, programming, English, or another topic and is searchable in the single public course search.
2. Add lessons in the intended order. Choose **Text**, **PDF reading**, **Video lesson**, or **Audio lesson**.
3. Add lesson text or upload one PDF, video, or audio file. AI quiz generation uses lesson text and extracted PDF text; video and audio need a text transcript in the lesson before AI generation.
4. Create lesson quizzes manually or choose **Generate quiz with AI**. Learner quiz answers are graded automatically.
5. Add a separate final exam with its own questions, correct answers, and passing score. Learners can take it after completing every lesson.
6. Publish the course when the lessons, quizzes, and final exam are ready.

Certificates are issued after all lessons are complete and the learner passes the final exam. The recorded exam score sets the certificate grade: Foundation/Bronze below 80, Intermediate/Silver from 80, and Advanced/Gold from 90. A final exam cannot be edited after learners have attempted it, so it is best to review it before publishing.

AI features require `AI_API_KEY` in `backend/.env` and may incur provider charges. When an author requests quiz generation, up to 24,000 characters of lesson text, including extracted PDF text, are sent to the configured AI API. When a learner submits a search for personalized recommendations, the search topic, quiz-derived learning level, interface language, and course IDs/titles/subjects/levels are sent; no account identifier is sent. Audio and video files are not sent.

When `AI_API_KEY` is configured, saving a new lesson automatically requests a banner using its course title, lesson title, and up to 1,800 characters of lesson text. Authors can also use **Generate AI banner** to retry or replace it. The image model defaults to `gpt-image-2.5-flare`; each generation requests one image and can incur image-generation charges. Learners see the banner with the lesson.

Every new lesson receives a topic-specific local illustration if AI image generation is unavailable. Authors can replace course or lesson banners in the author studio by uploading a PNG, JPEG, or WebP image (up to 8 MB). Existing generated SVG course art is refreshed when the topic-specific banner design changes; manually uploaded artwork is preserved.

The catalog filters by the selected course language: Uzbek shows Uzbek courses, English shows English courses, and so on. Authors can select the course language while creating it; the author form follows the current interface language by default. After the first lesson is added, the course language is fixed so the existing lesson text is not mislabeled. Current Python, FastAPI, and Git/Linux courses are available in Uzbek, English, Russian, and Korean, each with its own course banner. Lesson titles, text, quizzes, and exams have cached translations across those languages.

The free Python course in each language has a public YouTube video on every lesson, with lesson quizzes and a final exam already attached. Passing the final exam after completing all lessons unlocks the verified certificate. These videos are embedded from their creators' public YouTube pages; playback controls are managed by YouTube.

Authors can upload their own MP4/WebM videos or add a YouTube link. Uploaded videos must be watched to the end before the learner can complete that lesson; seeking ahead is blocked and playback speed is fixed at normal speed. Embedded YouTube videos retain YouTube's standard player controls and seek bar. The backend records watched time intervals for each video and playlist item, so jumping ahead does not count the skipped portion; learners can seek, then return to watch any missing sections. Every item in a playlist must be watched to the end. Video progress is checked by the backend as well as the browser.

Course cover banners are generated automatically as local SVG illustrations and appear in catalog cards and course previews. This does not require an AI API key. The current Python course video links point to public creator playlists/videos; the FastAPI and Git links use freeCodeCamp's public videos. External videos play through YouTube's embedded player and remain hosted by their creators. New or edited course, lesson, quiz, and exam text needs `AI_API_KEY` to generate missing translations; without the key, the app shows the source language. Authors can manage only courses they own, including their lessons, quizzes, and final exams.

Accepted materials are PDF, MP4 or WebM video, and MP3, M4A, WAV, OGG, or WebM audio. Each file is limited to 150 MB and the prototype allows up to 1 GB of stored course materials total. The backend checks the declared type and file signature, stores files under generated names, and returns a short-lived signed link only after an authorized course or enrollment read. Learner pages embed video/audio playback and offer PDFs in a new tab.

Files currently live on the local backend disk. This keeps the course builder usable for the prototype; a public deployment should use private object storage, quotas, and a media delivery service.
