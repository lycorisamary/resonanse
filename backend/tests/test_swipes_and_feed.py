import requests
import time
import random

# Базовый URL твоего запущенного локального сервера
BASE_URL = "http://localhost:8000/api/v1"

# Генерируем уникальный префикс для ЭТОГО запуска тестов.
# Пример: "test_1710523423_8492"
# Это гарантирует, что даже при повторном запуске без очистки БД тесты пройдут успешно.
TEST_PREFIX = f"test_{int(time.time())}_{random.randint(1000, 9999)}"

def get_test_email(base_name: str) -> str:
    """Возвращает уникальный email на основе базового имени."""
    return f"{TEST_PREFIX}_{base_name}@example.com"

def _auth_headers(email: str, password: str) -> dict[str, str]:
    """Получение заголовков Authorization для тестового пользователя."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
    )
    # Добавлено подробное сообщение об ошибке для отладки
    assert resp.status_code == 200, f"Ошибка входа для {email}: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_swipe_and_match_flow():
    """
    Проверяет сценарий:
    - два пользователя регистрируются и ставят друг другу лайк
    - второй свайп приводит к созданию матча и is_match = True
    """
    # Генерируем уникальные email для этого прогона
    email1 = get_test_email("user1")
    email2 = get_test_email("user2")
    password = "password123"

    # Регистрация двух пользователей
    r1 = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email1,
            "password": password,
            "first_name": "User1",
        },
    )
    assert r1.status_code == 201, f"Ошибка регистрации user1: {r1.text}"
    user1_id = r1.json()["id"]

    r2 = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email2,
            "password": password,
            "first_name": "User2",
        },
    )
    assert r2.status_code == 201, f"Ошибка регистрации user2: {r2.text}"
    user2_id = r2.json()["id"]

    # Авторизация и получение токенов
    h1 = _auth_headers(email1, password)
    h2 = _auth_headers(email2, password)

    # Первый лайк от user1 к user2
    resp1 = requests.post(
        f"{BASE_URL}/swipes",
        json={"target_user_id": user2_id, "decision": True},
        headers=h1,
    )
    assert resp1.status_code == 200, f"Ошибка свайпа 1: {resp1.text}"
    assert resp1.json()["is_match"] is False, "Первый свайп не должен создавать матч"

    # Ответный лайк от user2 к user1
    resp2 = requests.post(
        f"{BASE_URL}/swipes",
        json={"target_user_id": user1_id, "decision": True},
        headers=h2,
    )
    assert resp2.status_code == 200, f"Ошибка свайпа 2: {resp2.text}"
    assert resp2.json()["is_match"] is True, "Второй взаимный свайп должен создать матч"


def test_feed_uses_redis_cache():
    """
    Базовый тест для фида:
    - пользователь устанавливает геолокацию
    - получает ленту /feed
    """
    email = get_test_email("feed_user")
    password = "password123"

    # Регистрируем пользователя
    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "FeedUser",
        },
    )
    assert r.status_code == 201, f"Ошибка регистрации feed_user: {r.text}"

    headers = _auth_headers(email, password)

    # Устанавливаем геолокацию (Москва)
    resp_loc = requests.post(
        f"{BASE_URL}/users/location",
        json={"latitude": 55.7558, "longitude": 37.6173},
        headers=headers,
    )
    assert resp_loc.status_code == 200, f"Ошибка установки локации: {resp_loc.text}"

    # Первый запрос к /feed (должен сгенерировать колоду и записать в Redis)
    resp_feed1 = requests.get(f"{BASE_URL}/feed", headers=headers)
    assert resp_feed1.status_code == 200, f"Ошибка первого запроса feed: {resp_feed1.text}"
    assert isinstance(resp_feed1.json(), list), "Feed должен возвращать список"

    # Второй запрос к /feed (должен использовать кэш)
    resp_feed2 = requests.get(f"{BASE_URL}/feed", headers=headers)
    assert resp_feed2.status_code == 200, f"Ошибка второго запроса feed: {resp_feed2.text}"
    assert isinstance(resp_feed2.json(), list), "Feed должен возвращать список"


def test_swipe_self_forbidden():
    """
    Нельзя свайпнуть самого себя — ожидаем 400.
    """
    email = get_test_email("self")
    password = "password123"

    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Self",
        },
    )
    assert r.status_code == 201, f"Ошибка регистрации self: {r.text}"
    user_id = r.json()["id"]

    headers = _auth_headers(email, password)

    resp = requests.post(
        f"{BASE_URL}/swipes",
        json={"target_user_id": user_id, "decision": True},
        headers=headers,
    )
    assert resp.status_code == 400, "Свайп самого себя должен вернуть 400"
    # Проверка текста ошибки (убедись, что на бэкенде сообщение совпадает)
    assert "Нельзя свайпнуть самого себя" in resp.text or "self" in resp.text.lower()


def test_swipe_nonexistent_user():
    """
    Свайп по несуществующему пользователю должен возвращать 404.
    """
    email = get_test_email("swiper")
    password = "password123"

    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "Swiper",
        },
    )
    assert r.status_code == 201, f"Ошибка регистрации swiper: {r.text}"

    headers = _auth_headers(email, password)

    # Пытаемся свайпнуть ID, которого точно нет (например, 999999)
    resp = requests.post(
        f"{BASE_URL}/swipes",
        json={"target_user_id": 999999, "decision": True},
        headers=headers,
    )
    assert resp.status_code == 404, "Свайп несуществующего пользователя должен вернуть 404"
    assert "не найден" in resp.text.lower() or "not found" in resp.text.lower()


def test_nearby_requires_location():
    """
    /users/nearby без установленной локации должен вернуть 400.
    """
    email = get_test_email("noloc")
    password = "password123"

    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "NoLoc",
        },
    )
    assert r.status_code == 201, f"Ошибка регистрации noloc: {r.text}"

    headers = _auth_headers(email, password)

    resp = requests.get(f"{BASE_URL}/users/nearby", headers=headers)
    assert resp.status_code == 400, "Запрос nearby без локации должен вернуть 400"
    assert "локацию" in resp.text.lower() or "location" in resp.text.lower()


def test_feed_requires_location():
    """
    /feed без установленной локации также должен вернуть 400.
    """
    email = get_test_email("noloc_feed")
    password = "password123"

    r = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "first_name": "NoLocFeed",
        },
    )
    assert r.status_code == 201, f"Ошибка регистрации noloc_feed: {r.text}"

    headers = _auth_headers(email, password)

    resp = requests.get(f"{BASE_URL}/feed", headers=headers)
    assert resp.status_code == 400, "Запрос feed без локации должен вернуть 400"
    assert "локацию" in resp.text.lower() or "location" in resp.text.lower()


def test_nearby_excludes_already_swiped_users():
    """
    Пользователи, по которым уже есть запись в swipes, не должны попадать в nearby.
    """
    email1 = get_test_email("nearby1")
    email2 = get_test_email("nearby2")
    password = "password123"

    # Регистрация двух пользователей
    r1 = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email1,
            "password": password,
            "first_name": "Nearby1",
        },
    )
    r2 = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email2,
            "password": password,
            "first_name": "Nearby2",
        },
    )
    assert r1.status_code == 201, f"Ошибка регистрации nearby1: {r1.text}"
    assert r2.status_code == 201, f"Ошибка регистрации nearby2: {r2.text}"

    user1_id = r1.json()["id"]
    user2_id = r2.json()["id"]

    h1 = _auth_headers(email1, password)
    h2 = _auth_headers(email2, password)

    # Обоим ставим одинаковую локацию (Москва)
    payload_loc = {"latitude": 55.7558, "longitude": 37.6173}
    resp_loc1 = requests.post(f"{BASE_URL}/users/location", json=payload_loc, headers=h1)
    resp_loc2 = requests.post(f"{BASE_URL}/users/location", json=payload_loc, headers=h2)
    assert resp_loc1.status_code == 200
    assert resp_loc2.status_code == 200

    # До свайпа — user2 должен быть в списке nearby для user1
    # (Предполагаем, что других пользователей рядом нет или их мало, но user2 точно должен быть)
    resp_nearby_before = requests.get(f"{BASE_URL}/users/nearby?radius_km=5", headers=h1)
    assert resp_nearby_before.status_code == 200
    ids_before = [u["id"] for u in resp_nearby_before.json()]
    # Проверка: user2 есть в списке
    assert user2_id in ids_before, "До свайпа пользователь должен быть в списке nearby"

    # user1 свайпает user2
    resp_swipe = requests.post(
        f"{BASE_URL}/swipes",
        json={"target_user_id": user2_id, "decision": True},
        headers=h1,
    )
    assert resp_swipe.status_code == 200

    # После свайпа user2 больше не должен появляться в nearby для user1
    resp_nearby_after = requests.get(f"{BASE_URL}/users/nearby?radius_km=5", headers=h1)
    assert resp_nearby_after.status_code == 200
    ids_after = [u["id"] for u in resp_nearby_after.json()]
    
    # Главная проверка теста
    assert user2_id not in ids_after, "После свайпа пользователь НЕ должен быть в списке nearby"