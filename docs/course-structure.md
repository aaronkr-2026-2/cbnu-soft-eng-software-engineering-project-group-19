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

StudyFlow already stores `Course`, `Lesson`, `Quiz`, quiz questions and attempts, final exams, enrollments, and lesson progress separately. A lesson currently holds its text and one optional uploaded resource directly on the `Lesson` row. This is adequate for the current prototype, but it does not yet support multiple ordered materials, modules, or assignments. The next schema expansion should introduce `CourseModule`, `LessonMaterial`, `LessonAssignment`, and `AssignmentSubmission`, while keeping nullable module links during migration so existing courses continue to work.

The current update adds lesson banner metadata and a `LessonTranslation` cache without changing existing lesson IDs or quiz/progress relationships.
