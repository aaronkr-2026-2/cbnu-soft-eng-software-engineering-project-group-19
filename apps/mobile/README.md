# SCHOLWARD Academy Mobile

The SCHOLWARD Academy learner app is available for Android and iOS. Sign in with your existing SCHOLWARD Academy account. The mobile and web apps use the same server for courses and lesson progress.

## Run on your phone

```sh
cd apps/mobile
npm ci
npm start
```

Connect your phone and computer to the same Wi-Fi network. On Android, scan the terminal QR code from Expo Go. On iOS, scan it with the Camera app and use the same Expo account in Expo Go and the Expo CLI. The app uses Expo SDK 58.

## Features

- Sign in with a learner account and store the session securely on your device.
- Browse the interface and course catalog in Uzbek, English, Russian, or Korean. The app remembers your language preference.
- Open lessons and materials for your selected course and track your progress.
- Watch videos in the app and resume from your saved position. You can also open the video in your browser. Progress refreshes automatically when you return to the app.
- Take lesson quizzes and review your scores and previous attempts.
- Check your final exam status after completing the lessons. To take the final exam or request a certificate, open SCHOLWARD Academy in your browser and verify with a passkey. If prompted, sign in with the same learner account.
- Remove a course from **My courses** and add it back from the catalog at any time. Course progress and certificates are retained.
- Open the web author portal from the sign-in screen.
- View issued certificates under **My Certificates** and open their verification links.

Enroll in paid courses on the [SCHOLWARD Academy website](https://scholward-academy.vercel.app/app/).

## Run checks

```sh
npm run check
npx expo export --platform ios --platform android
```

The app connects to `https://scholward-academy.vercel.app` by default. To use a test server, set `EXPO_PUBLIC_STUDYFLOW_API_URL` before starting Expo.
