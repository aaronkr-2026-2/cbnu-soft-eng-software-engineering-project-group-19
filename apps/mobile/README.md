# SCHOLWARD Academy Mobile

Android va iOS uchun SCHOLWARD Academy o‘quvchi ilovasi. Mavjud SCHOLWARD Academy hisobingiz bilan kiring. Kurslar va dars progressi web bilan bitta serverda saqlanadi.

## Telefonda ochish

```sh
cd apps/mobile
npm ci
npm start
```

Telefon va kompyuterni bir Wi-Fi tarmog‘iga ulang. Android’da Expo Go ichidan, iOS’da kamera orqali terminaldagi QR kodni skanerlang. iOS’da Expo Go hamda Expo CLI bir Expo hisobiga kirgan bo‘lishi kerak. Ilova Expo SDK 58’dan foydalanadi.

## Birinchi versiya

- O‘quvchi hisobi bilan kirish va qurilmada sessiyani xavfsiz saqlash.
- O‘zbek, ingliz, rus va koreys tilidagi interfeys va kurslar katalogi. Tanlangan til qurilmada saqlanadi.
- Tanlangan kursning darslari, dars materiallari va progressi.
- Videoni dars ichida ijro etish. Ko‘rish progressi SCHOLWARD Academy’da saqlanadi. Dars qayta ochilganda pleyer saqlangan joydan davom etishga tayyor turadi. Videoni brauzerda ham ochish mumkin. Ilovaga qaytganda progress avtomatik yangilanadi.
- Dars quizlarini mobil ilovada ishlash, natijasi va avvalgi urinishlarini ko‘rish.
- Darslar tugagach yakuniy imtihon holatini ko‘rish. Imtihonni topshirish va sertifikatni rasmiylashtirish SCHOLWARD Academy brauzer oynasida passkey bilan tasdiqlanadi. So‘ralsa, brauzerda o‘sha o‘quvchi hisobi bilan kiring.
- «Sertifikatlarim» bo‘limida berilgan sertifikatlarni ko‘rish va tekshirish havolasini ochish.

Pulli kursga yozilish [SCHOLWARD Academy veb-saytida](https://studyflow-web-1hab.vercel.app/app/) amalga oshiriladi.

## Tekshirish

```sh
npm run check
npx expo export --platform ios --platform android
```

Standart server manzili `https://studyflow-web-1hab.vercel.app`. Sinov serverini ishlatish uchun Expo ishga tushishidan oldin `EXPO_PUBLIC_STUDYFLOW_API_URL` qiymatini belgilang.
