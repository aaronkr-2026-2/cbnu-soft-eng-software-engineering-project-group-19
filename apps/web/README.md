# StudyFlow AI web starter

The web starter is a dependency-free, responsive interface with Uzbek, English, Russian, and Korean UI copy. It is served by the FastAPI backend at `/app` and uses the existing authentication, course catalog, enrollment, lesson, progress, quiz, recommendation, and learning-plan endpoints. Signed-in learners can preview published course descriptions and lesson outlines before enrolling, read enrolled lessons, mark them complete, take quizzes, review quiz attempts, view course progress and recommendations, and generate study plans. After finishing every lesson, learners can leave or update a 1–5-star course review that appears in the public course preview. Course authors can review enrollment, lesson completion, ratings, and final-exam pass statistics for their own courses. Signed-in course authors can create courses, add lessons and multi-question quizzes, and publish or unpublish their courses from the instructor studio. After completing every lesson, learners can take a final exam assembled from each lesson quiz. Passing the exam (70% or higher) unlocks a uniquely coded course certificate that can be printed or saved as a PDF. Every certificate carries a 128-bit random verification code and a public verification link. Anyone can check the code at `/app/verify.html`; only certificates recorded in the database are reported as valid.

Run the backend from `backend/`:

```sh
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open <http://127.0.0.1:8000/app>.
