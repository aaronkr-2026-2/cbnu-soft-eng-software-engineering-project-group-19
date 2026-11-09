# StudyFlow course content model

## Recommended hierarchy

```text
Course
└── Module (unit, week, or major topic)
    └── Lesson
        └── Learning Material (text, PDF, video, audio, or code)
        ├── Quiz
        └── Assignment
```

Keep course metadata such as title, owner, language, level, price, and publication status on `Course`. Modules and lessons should have their own IDs and ordering fields. Store each learning material, quiz, assignment, learner submission, and progress record separately and link it to its parent ID. A final exam stays course-level because it covers the whole course.

## Current implementation

StudyFlow stores `Course`, `CourseModule`, `Lesson`, quizzes and attempts, final exams, enrollments, and lesson progress separately. Authors can add, rename, reorder, and remove course modules and assign lessons to them. Existing lessons keep working without a module, and deleting a module leaves its lessons in the course as unassigned lessons. Module titles are translated and cached when the AI translation service is configured. A lesson still holds its text and one optional uploaded resource directly on its row; multiple ordered learning materials and assignments remain future schema work.

The module migration adds nullable lesson links, so existing lesson IDs, quizzes, and progress records remain intact.
