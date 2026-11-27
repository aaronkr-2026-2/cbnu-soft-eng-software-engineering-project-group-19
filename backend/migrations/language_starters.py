"""Frozen content for the introductory language catalog migration."""

LESSONS = (
    {
        "uz": (
            "Salomlashish va tanishish",
            "Salomlashish, ism va ona tilingizni aytishni mashq qiling. Rasmiy vaziyatda muloyim iborani tanlang.",
        ),
        "en": (
            "Greetings and introductions",
            "Practise greetings, saying your name, and naming the language you speak. Choose a polite expression in formal settings.",
        ),
        "ru": (
            "Приветствие и знакомство",
            "Потренируйтесь здороваться, называть своё имя и родной язык. В официальной ситуации выбирайте вежливую форму.",
        ),
        "ko": (
            "인사와 자기소개",
            "인사하고 이름과 모국어를 말하는 연습을 하세요. 처음 만나는 사람에게는 정중한 표현을 쓰세요.",
        ),
    },
    {
        "uz": (
            "Kafeda buyurtma berish",
            "Buyurtma berishda miqdorni son bilan ayting. Narxni so‘rang va suhbat oxirida minnatdorchilik bildiring.",
        ),
        "en": (
            "Ordering at a café",
            "Say how many items you want, ask the price, and thank the server at the end.",
        ),
        "ru": (
            "Заказ в кафе",
            "Уточните количество, спросите цену и поблагодарите собеседника в конце разговора.",
        ),
        "ko": (
            "카페에서 주문하기",
            "원하는 수량을 말하고 가격을 물어보세요. 대화가 끝나면 감사 인사를 하세요.",
        ),
    },
    {
        "uz": (
            "Yo‘l so‘rash va tushunish",
            "Boradigan joyingizni ayting. Chap, o‘ng va to‘g‘ri kabi ko‘rsatmalarni farqlang. Tushunmasangiz takrorlashni so‘rang.",
        ),
        "en": (
            "Asking for and following directions",
            "Name your destination and practise telling left, right, and straight ahead apart. Ask for repetition if you miss an instruction.",
        ),
        "ru": (
            "Как спросить дорогу",
            "Назовите место назначения и различайте указания «налево», «направо» и «прямо». Если не поняли, попросите повторить.",
        ),
        "ko": (
            "길 묻고 찾아가기",
            "목적지를 말하고 왼쪽, 오른쪽, 직진을 구별하세요. 잘 못 들었으면 다시 말해 달라고 하세요.",
        ),
    },
)

# Each position has the same meaning in all four languages.
PHRASES = (
    {
        "uz": (
            "Salom!",
            "Mening ismim Mina.",
            "Ismingiz nima?",
            "Men o‘zbek tilida gaplashaman.",
            "Tanishganimdan xursandman.",
            "Xayr, ko‘rishguncha!",
        ),
        "en": (
            "Hello!",
            "My name is Mina.",
            "What’s your name?",
            "I speak Uzbek.",
            "Nice to meet you.",
            "Goodbye, see you later!",
        ),
        "ru": (
            "Здравствуйте!",
            "Меня зовут Мина.",
            "Как вас зовут?",
            "Я говорю по-узбекски.",
            "Приятно познакомиться.",
            "До свидания, до встречи!",
        ),
        "ko": (
            "안녕하세요!",
            "제 이름은 미나예요.",
            "이름이 뭐예요?",
            "저는 우즈베크어를 해요.",
            "만나서 반가워요.",
            "안녕히 가세요. 다음에 봐요!",
        ),
    },
    {
        "uz": (
            "Bitta qahva bering, iltimos.",
            "Ikkita choy bering, iltimos.",
            "Bu qancha turadi?",
            "Suv bormi?",
            "Shakarsiz bo‘lsin, iltimos.",
            "Rahmat!",
        ),
        "en": (
            "One coffee, please.",
            "Two teas, please.",
            "How much is this?",
            "Do you have any water?",
            "No sugar, please.",
            "Thank you!",
        ),
        "ru": (
            "Один кофе, пожалуйста.",
            "Два чая, пожалуйста.",
            "Сколько это стоит?",
            "У вас есть вода?",
            "Без сахара, пожалуйста.",
            "Спасибо!",
        ),
        "ko": (
            "커피 한 잔 주세요.",
            "차 두 잔 주세요.",
            "이거 얼마예요?",
            "물 있어요?",
            "설탕 빼 주세요.",
            "감사합니다!",
        ),
    },
    {
        "uz": (
            "Kechirasiz, bekat qayerda?",
            "Chapga buriling.",
            "O‘ngga buriling.",
            "To‘g‘ri boring.",
            "Bu yerdan uzoqmi?",
            "Yana bir marta ayting, iltimos.",
        ),
        "en": (
            "Excuse me, where is the stop?",
            "Turn left.",
            "Turn right.",
            "Go straight ahead.",
            "Is it far from here?",
            "Please say that again.",
        ),
        "ru": (
            "Извините, где остановка?",
            "Поверните налево.",
            "Поверните направо.",
            "Идите прямо.",
            "Это далеко отсюда?",
            "Повторите, пожалуйста.",
        ),
        "ko": (
            "실례합니다. 정류장이 어디예요?",
            "왼쪽으로 도세요.",
            "오른쪽으로 도세요.",
            "똑바로 가세요.",
            "여기서 멀어요?",
            "다시 한번 말해 주세요.",
        ),
    },
)

COPY = {
    "uz": {
        "titles": {
            "uz": "O‘zbek tili asoslari",
            "en": "Ingliz tili asoslari",
            "ru": "Rus tili asoslari",
            "ko": "Koreys tili asoslari",
        },
        "category": "Til kurslari",
        "description": "Salomlashish, kafeda buyurtma berish va yo‘l so‘rashni mashq qiling. Uchta dars, dars quizlari va sertifikat uchun yakuniy imtihon.",
        "practice": "Mashq. Tarjimani yopib, iboralarni ovoz chiqarib ayting. Keyin dars mavzusiga mos ikki qatorli suhbat tuzing.",
        "quiz": "Dars quizi",
        "exam": "Yakuniy imtihon",
        "meaning": "Bu iboraning ma’nosi nima? «{}»",
        "say": "Buni o‘rganayotgan tilingizda qanday aytasiz? «{}»",
        "explanation": "To‘g‘ri juftlik: {} — {}",
    },
    "en": {
        "titles": {
            "uz": "Uzbek for beginners",
            "en": "English for beginners",
            "ru": "Russian for beginners",
            "ko": "Korean for beginners",
        },
        "category": "Language courses",
        "description": "Practise greetings, ordering at a café, and asking for directions. Includes three lessons, lesson quizzes, and a final exam for a certificate.",
        "practice": "Practice. Cover the translation and say each phrase aloud. Then write a two-line dialogue for this lesson’s situation.",
        "quiz": "Lesson quiz",
        "exam": "Final exam",
        "meaning": "What does this phrase mean? “{}”",
        "say": "How would you say this in the language you’re learning? “{}”",
        "explanation": "Correct match: {} — {}",
    },
    "ru": {
        "titles": {
            "uz": "Узбекский для начинающих",
            "en": "Английский для начинающих",
            "ru": "Русский для начинающих",
            "ko": "Корейский для начинающих",
        },
        "category": "Языковые курсы",
        "description": "Научитесь здороваться, делать заказ в кафе и спрашивать дорогу. Три урока, тесты и итоговый экзамен для получения сертификата.",
        "practice": "Практика. Закройте перевод и произнесите фразы вслух. Затем составьте диалог из двух реплик по теме урока.",
        "quiz": "Тест по уроку",
        "exam": "Итоговый экзамен",
        "meaning": "Что означает эта фраза? «{}»",
        "say": "Как сказать это на языке, который вы изучаете? «{}»",
        "explanation": "Правильная пара: {} — {}",
    },
    "ko": {
        "titles": {
            "uz": "초급 우즈베크어",
            "en": "초급 영어",
            "ru": "초급 러시아어",
            "ko": "초급 한국어",
        },
        "category": "외국어 강좌",
        "description": "인사하기, 카페에서 주문하기, 길 묻기를 연습하세요. 세 개의 수업과 퀴즈를 마친 뒤 최종 시험에 합격하면 수료증을 받을 수 있습니다.",
        "practice": "연습. 번역을 가리고 표현을 소리 내어 말하세요. 그런 다음 수업 상황에 맞는 두 줄짜리 대화를 만들어 보세요.",
        "quiz": "수업 퀴즈",
        "exam": "최종 시험",
        "meaning": "이 표현은 무슨 뜻인가요? “{}”",
        "say": "배우는 언어로 어떻게 말할까요? “{}”",
        "explanation": "올바른 짝: {} — {}",
    },
}

USAGE = {
    "uz": {
        "en": (
            "Salomlashganda “Hello” neytral, “Hi” esa norasmiy. “My name is …” qolipini o‘z ismingiz bilan ishlating.",
            "Sanash uchun one va two dan foydalaning. “One coffee, please” iborasida please buyurtmani muloyim qiladi.",
            "“Turn” burilishni, “go straight” yo‘lda davom etishni bildiradi. left va right so‘zlarini joylarini almashtirib mashq qiling.",
        ),
        "ru": (
            "Yangi tanishga «Здравствуйте» va «вас» deb murojaat qiling. «Меня зовут …» iborasidan keyin ismingiz keladi.",
            "«Один кофе» va «два чая» qoliplarini juftlikda yodlang. «Пожалуйста» buyurtmani muloyim qiladi.",
            "«Налево» chapga, «направо» o‘ngga degani. «Поверните» va «идите» muloyim buyruq shakllari.",
        ),
        "ko": (
            "«안녕하세요» kundalik muloyim salom. «제 이름은 …예요» qolipida namunadagi ismni o‘zingizniki bilan almashtiring.",
            "«주세요» so‘rov oxirida ishlatiladi. Ichimlik sanaganda «한 잔» bir piyola, «두 잔» ikki piyola.",
            "«어디예요?» «qayerda?» degani. Yo‘nalishda «왼쪽으로» chap tomonga, «오른쪽으로» o‘ng tomonga.",
        ),
    },
    "en": {
        "uz": (
            "Salom is a common greeting. In your introduction, replace Mina in Mening ismim Mina with your own name.",
            "Bitta and ikkita mean one and two items. Iltimos adds the polite sense of “please.”",
            "Chapga and o‘ngga mean towards the left and right. The ending -ga can indicate direction.",
        ),
        "ru": (
            "Use Здравствуйте and вас when speaking politely to someone you’ve just met. Put your name after Меня зовут.",
            "Learn один кофе and два чая as complete phrases: the noun form depends on the quantity. Пожалуйста makes a request polite.",
            "Налево describes movement to the left and направо to the right. Поверните and идите are polite commands.",
        ),
        "ko": (
            "안녕하세요 is a polite everyday greeting. Practise 제 이름은 미나예요 first, then make the sentence about yourself.",
            "주세요 makes a polite request. 한 잔 and 두 잔 count one and two cups of a drink.",
            "어디예요 asks where something is. 왼쪽으로 means towards the left, and 오른쪽으로 towards the right.",
        ),
    },
    "ru": {
        "uz": (
            "Salom — обычное приветствие. В конструкции Mening ismim … назовите своё имя после ismim.",
            "Bitta и ikkita обозначают один и два предмета. Слово iltimos делает просьбу вежливой.",
            "Chapga означает «налево», o‘ngga — «направо». Окончание -ga может обозначать направление движения.",
        ),
        "en": (
            "Hello подходит в большинстве ситуаций, а Hi звучит неформально. В формуле My name is … назовите своё имя.",
            "Сравните one coffee и two teas. Добавьте please в конце заказа, чтобы попросить вежливо.",
            "Turn означает «повернуть», go straight — «идти прямо». Запомните противопоставление left и right.",
        ),
        "ko": (
            "안녕하세요 — вежливое повседневное приветствие. Потренируйтесь произносить 제 이름은 미나예요, а затем представьтесь сами.",
            "주세요 означает вежливую просьбу. 한 잔 и 두 잔 обозначают одну и две чашки напитка.",
            "어디예요? означает «где?». 왼쪽으로 указывает налево, 오른쪽으로 — направо.",
        ),
    },
    "ko": {
        "uz": (
            "Salom은 일상적인 인사예요. Mening ismim …에서 Mina 대신 자신의 이름을 넣어 말해 보세요.",
            "bitta는 한 개, ikkita는 두 개를 뜻해요. 부탁할 때 iltimos를 쓰면 정중해요.",
            "chapga는 왼쪽으로, o‘ngga는 오른쪽으로라는 뜻이에요. -ga는 이동 방향을 나타낼 수 있어요.",
        ),
        "en": (
            "Hello는 두루 쓸 수 있는 인사이고 Hi는 좀 더 가벼워요. My name is … 뒤에 자신의 이름을 넣어 보세요.",
            "one coffee와 two teas를 비교해 보세요. 주문 끝에 please를 붙이면 요청이 정중해져요.",
            "turn은 방향을 바꾸라는 뜻이고 go straight는 직진하라는 뜻이에요. left와 right를 짝으로 익히세요.",
        ),
        "ru": (
            "처음 만난 사람에게는 Здравствуйте를 쓰면 정중해요. Меня зовут … 뒤에 자신의 이름을 말하세요.",
            "один кофе와 два чая는 수량에 따라 명사 형태가 달라지는 예예요. 부탁할 때 пожалуйста를 붙이세요.",
            "налево는 왼쪽으로, направо는 오른쪽으로라는 뜻이에요. Поверните와 идите는 정중한 지시 표현이에요.",
        ),
    },
}


def build_question(unit, source, target, index, reverse):
    native = PHRASES[unit][source]
    foreign = PHRASES[unit][target]
    prompts, answers = (native, foreign) if reverse else (foreign, native)
    positions = [(index + shift) % len(answers) for shift in range(4)]
    offset = (index + unit) % len(positions)
    positions = positions[offset:] + positions[:offset]
    return {
        "prompt": COPY[source]["say" if reverse else "meaning"].format(prompts[index]),
        "choices": [answers[position] for position in positions],
        "correct_index": positions.index(index),
    }
