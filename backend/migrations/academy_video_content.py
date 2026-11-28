"""Course references and teaching scripts for the academy's bundled videos."""

IT_COURSES = {
    "uz": {
        "html": "98650845-0f20-4931-87b1-0862c4194840",
        "python": "46d0d692-0cab-40aa-a3d6-ce234a932985",
    },
    "en": {
        "html": "3b6755aa-4e2b-4761-a153-ec859697eea0",
        "python": "9759360e-f9a1-4a5d-9dd8-63f152a0e621",
    },
    "ru": {
        "html": "29eeb0a9-57cb-498e-b0af-d9ef323a2e9e",
        "python": "a3ec9c26-b067-4dda-95d6-f434dc1f00f5",
    },
    "ko": {
        "html": "357914bd-438f-4418-bbeb-0370f82f3dfe",
        "python": "c2598ec0-dabe-4967-b5c0-d2001e41665e",
    },
}

IT_HEADINGS = {
    "html": {
        "uz": ("Semantik HTML", "CSS va Flexbox", "Moslashuvchan portfolio"),
        "en": ("Semantic HTML", "CSS and Flexbox", "Responsive portfolio"),
        "ru": ("Семантический HTML", "CSS и Flexbox", "Адаптивное портфолио"),
        "ko": ("시맨틱 HTML", "CSS와 플렉스박스", "반응형 포트폴리오"),
    },
    "python": {
        "uz": ("Qiymatlar va kiritish", "Shart va takrorlash", "Funksiyalar va ballar"),
        "en": ("Values and input", "Conditions and loops", "Functions and scores"),
        "ru": ("Значения и ввод", "Условия и циклы", "Функции и баллы"),
        "ko": ("값과 입력", "조건과 반복", "함수와 점수"),
    },
}

IT_DEMOS = {
    "html": (
        (
            "<header><h1>Portfolio</h1></header>\n<main>\n  <article><h2>Project</h2><p>Details</p></article>\n</main>\n<footer>Contact</footer>",
            {
                "uz": (
                    "Sarlavhani header ichiga, asosiy ma’lumotni main ichiga qo‘ying. Mustaqil loyiha uchun article ishlating.",
                    "Bitta asosiy sarlavha tanlang. Loyihaga ikkinchi darajali sarlavha bering va sahifani brauzerda tekshiring.",
                ),
                "en": (
                    "Put the page heading in the header and the main content inside main. Use an article for a project that makes sense on its own.",
                    "Give the page one main heading and the project a second-level heading. Open the file in a browser to inspect the result.",
                ),
                "ru": (
                    "Разместите заголовок в шапке, а основной материал в главной области. Самостоятельный проект оформите как статью.",
                    "Оставьте один главный заголовок и добавьте заголовок второго уровня для проекта. Откройте файл в браузере.",
                ),
                "ko": (
                    "상단 영역에는 페이지 제목을 배치하고 본문은 메인 영역 안에 넣습니다. 독립적인 프로젝트는 아티클로 묶습니다.",
                    "페이지의 첫 번째 제목은 하나만 두고 프로젝트에는 두 번째 단계 제목을 넣습니다. 브라우저에서 파일을 열어 확인하세요.",
                ),
            },
        ),
        (
            ".projects {\n  display: flex;\n  flex-wrap: wrap;\n  gap: 1rem;\n}\n.projects > article { flex: 1 1 15rem; }",
            {
                "uz": (
                    "Nuqta bilan yozilgan selektor klassni tanlaydi. Flexbox kartalarni bir qatorda joylaydi va oralariga bo‘shliq qo‘yadi.",
                    "Oynani toraytirib ko‘ring. Qatorga sig‘maydigan karta keyingi qatorga o‘tishi kerak.",
                ),
                "en": (
                    "The dot selects a class. Flexbox lays the cards out in a row and the gap property sets the space between them.",
                    "Shrink the browser window. A card that no longer fits should wrap to the next row.",
                ),
                "ru": (
                    "Точка в начале селектора выбирает класс. Флексбокс раскладывает карточки в ряд, а свойство промежутка задаёт расстояние.",
                    "Сузьте окно браузера. Карточка, которой не хватило места, должна перейти на следующую строку.",
                ),
                "ko": (
                    "점으로 시작하는 선택자는 클래스를 찾습니다. 플렉스박스는 카드를 가로로 정렬하고 간격 속성은 카드 사이의 여백을 정합니다.",
                    "브라우저 너비를 줄여 보세요. 한 줄에 들어가지 않는 카드는 다음 줄로 넘어갑니다.",
                ),
            },
        ),
        (
            "img { max-width: 100%; height: auto; }\n@media (max-width: 600px) {\n  nav { display: grid; gap: 0.5rem; }\n}",
            {
                "uz": (
                    "Rasm konteyneridan chiqib ketmasligi uchun maksimal enini belgilang. Eni kichrayganda navigatsiya vertikal tartibga o‘tadi.",
                    "Portfolioni telefon va kompyuter o‘lchamida oching. Havolalar hamda rasmlarni sinab, gorizontal siljish yo‘qligini tekshiring.",
                ),
                "en": (
                    "Limit an image to the width of its container. At narrow widths, switch the navigation to a vertical layout.",
                    "Try the portfolio at phone and desktop widths. Check the links and images, and confirm you don’t have to scroll sideways.",
                ),
                "ru": (
                    "Ограничьте ширину изображения шириной контейнера. На узком экране расположите ссылки навигации вертикально.",
                    "Проверьте портфолио на ширине телефона и компьютера. Проверьте ссылки, картинки и отсутствие горизонтальной прокрутки.",
                ),
                "ko": (
                    "이미지의 최대 너비를 부모 요소의 너비로 제한하세요. 화면이 좁을 때는 메뉴 링크를 세로로 배치합니다.",
                    "휴대폰과 데스크톱 너비에서 포트폴리오를 열어 보세요. 링크와 이미지가 제대로 보이는지, 가로 스크롤이 생기지 않는지 확인하세요.",
                ),
            },
        ),
    ),
    "python": (
        (
            'name = input("Name: ")\nscore = int(input("Score: "))\nprint(f"{name}: {score + 5}")',
            {
                "uz": (
                    "Kiritish funksiyasi matn qaytaradi. Ball bilan hisoblash uchun matnni butun songa aylantiring.",
                    "Masalan, ballga sakkiz kiritsangiz, dastur o‘n uch chiqaradi. Matn va son bilan ishlashdagi farqni kuzating.",
                ),
                "en": (
                    "Input returns text. Convert the score to an integer before using it in arithmetic.",
                    "Try entering eight as the score. The output should include thirteen. Notice how a string and a number behave differently.",
                ),
                "ru": (
                    "Функция ввода возвращает текст. Перед вычислением преобразуйте введённый балл в целое число.",
                    "Введите восемь. Программа должна вывести тринадцать. Сравните, как ведут себя строка и число.",
                ),
                "ko": (
                    "입력 함수는 문자열을 반환합니다. 점수를 계산하기 전에 문자열을 정수로 바꾸세요.",
                    "점수에 팔을 입력하면 십삼이 나옵니다. 문자열과 숫자의 동작이 어떻게 다른지 확인하세요.",
                ),
            },
        ),
        (
            'scores = [81, 52, 73]\nfor score in scores:\n    if score >= 75:\n        print(score, "Pass")',
            {
                "uz": (
                    "Sikl ro‘yxatdagi ballarni navbat bilan oladi. Shart yetmish besh yoki undan baland ballarni tanlaydi.",
                    "Qaysi ball chiqishini oldindan ayting. Keyin ro‘yxatga aynan yetmish beshni qo‘shib natijani tekshiring.",
                ),
                "en": (
                    "The loop visits each score in the list. The condition selects scores of seventy-five and above.",
                    "Predict which score is printed. Then add exactly seventy-five to the list and check the result.",
                ),
                "ru": (
                    "Цикл перебирает баллы из списка. Условие выбирает значения от семидесяти пяти включительно.",
                    "Предскажите, какой балл будет выведен. Затем добавьте в список ровно семьдесят пять и проверьте результат.",
                ),
                "ko": (
                    "반복문은 리스트에 있는 점수를 차례대로 확인합니다. 조건문은 칠십오 점 이상만 골라냅니다.",
                    "어떤 점수가 출력될지 먼저 예상하세요. 리스트에 정확히 칠십오 점을 추가해 결과를 확인하세요.",
                ),
            },
        ),
        (
            "def average(scores):\n    if not scores:\n        return None\n    return sum(scores) / len(scores)\n\nprint(average([80, 90]))",
            {
                "uz": (
                    "Funksiya ballar yig‘indisini ularning soniga bo‘ladi. Bo‘sh ro‘yxatni alohida tekshirish nolga bo‘lishning oldini oladi.",
                    "Sakson va to‘qsonning o‘rtachasi sakson besh. Bo‘sh ro‘yxat yuborib, funksiya qanday javob qaytarishini ko‘ring.",
                ),
                "en": (
                    "The function divides the sum by the number of scores. Checking for an empty list avoids dividing by zero.",
                    "The average of eighty and ninety is eighty-five. Try passing an empty list and inspect the return value.",
                ),
                "ru": (
                    "Функция делит сумму на количество баллов. Проверка пустого списка помогает избежать деления на ноль.",
                    "Среднее между восемьюдесятью и девяноста равно восьмидесяти пяти. Передайте пустой список и проверьте результат.",
                ),
                "ko": (
                    "함수는 점수의 합을 점수 개수로 나눕니다. 빈 리스트를 먼저 확인하면 영으로 나누는 문제를 피할 수 있습니다.",
                    "팔십과 구십의 평균은 팔십오입니다. 빈 리스트를 전달해서 반환값을 살펴보세요.",
                ),
            },
        ),
    ),
}


def video_key(subject, source, position):
    return f"academy-v1-{subject}-{source}-{position}.mp4"
