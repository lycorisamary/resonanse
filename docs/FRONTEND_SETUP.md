# Инструкция по настройке и запуску фронтенда

## Требования

- Flutter SDK 3.0.0 или выше
- Android Studio или VS Code с расширением Flutter
- Android SDK (для запуска на Android)
- Эмулятор Android или физическое устройство

## Проверка установки Flutter

Убедитесь, что Flutter установлен и настроен:

```bash
flutter doctor
```

Исправьте все проблемы, которые покажет команда.

## Пошаговая настройка

### 1. Переход в папку фронтенда

```bash
cd frontend
```

### 2. Установка зависимостей

```bash
flutter pub get
```

Эта команда установит все зависимости, указанные в `pubspec.yaml`.

### 3. Проверка доступных устройств

```bash
flutter devices
```

Должны быть доступны эмуляторы или подключенные устройства.

### 4. Запуск приложения

#### 4.1. Запуск на эмуляторе/устройстве

```bash
flutter run
```

Flutter автоматически выберет доступное устройство. Если доступно несколько устройств, можно указать конкретное:

```bash
flutter run -d <device_id>
```

#### 4.2. Запуск в режиме отладки

По умолчанию приложение запускается в режиме отладки с hot reload.

**Hot Reload**: Нажмите `r` в консоли для быстрой перезагрузки изменений.

**Hot Restart**: Нажмите `R` для полной перезагрузки приложения.

**Quit**: Нажмите `q` для выхода.

### 5. Сборка APK для Android

Для создания APK файла:

```bash
flutter build apk
```

APK будет находиться в `build/app/outputs/flutter-apk/app-release.apk`.

Для создания debug версии:

```bash
flutter build apk --debug
```

## Структура фронтенда

```
frontend/
├── lib/
│   └── main.dart          # Точка входа приложения
├── android/               # Настройки Android
├── ios/                   # Настройки iOS (для будущего использования)
├── pubspec.yaml           # Зависимости и настройки проекта
└── .gitignore            # Игнорируемые файлы
```

## Основные зависимости

- `http` - HTTP клиент для работы с API бэкенда
- `json_annotation` - Аннотации для сериализации JSON
- `shared_preferences` - Локальное хранилище для токенов и настроек
- `cupertino_icons` - Иконки для iOS стиля

## Настройка подключения к API

В будущем необходимо будет настроить базовый URL API бэкенда. Это можно сделать через:

1. Константы в коде
2. Файл конфигурации
3. Переменные окружения (через пакет `flutter_dotenv`)

Пример структуры для работы с API:

```dart
// lib/config/api_config.dart
class ApiConfig {
  static const String baseUrl = 'http://localhost:8000';
  static const String apiVersion = '/api/v1';
}
```

## Разработка

### Структура кода

Рекомендуемая структура для будущей разработки:

```
lib/
├── main.dart
├── config/              # Конфигурация
│   └── api_config.dart
├── models/              # Модели данных
│   └── user.dart
├── services/            # Сервисы для работы с API
│   ├── auth_service.dart
│   └── user_service.dart
├── screens/             # Экраны приложения
│   ├── login_screen.dart
│   ├── register_screen.dart
│   └── home_screen.dart
├── widgets/             # Переиспользуемые виджеты
└── utils/               # Утилиты
    └── storage.dart
```

### Типизация

Все данные должны быть типизированы. Используйте классы и модели для работы с данными API.

Пример модели пользователя:

```dart
class User {
  final int id;
  final String email;
  final String? firstName;
  final String? lastName;
  
  User({
    required this.id,
    required this.email,
    this.firstName,
    this.lastName,
  });
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      email: json['email'],
      firstName: json['first_name'],
      lastName: json['last_name'],
    );
  }
}
```

## Тестирование

### Запуск тестов

```bash
flutter test
```

### Запуск с покрытием

```bash
flutter test --coverage
```

## Устранение неполадок

### Ошибка "No devices found"

1. Убедитесь, что эмулятор запущен или устройство подключено
2. Проверьте: `flutter devices`
3. Запустите эмулятор через Android Studio

### Ошибка подключения к API

1. Убедитесь, что бэкенд запущен на `http://localhost:8000`
2. Для Android эмулятора используйте `10.0.2.2` вместо `localhost`
3. Проверьте настройки CORS в бэкенде

### Ошибки компиляции

1. Очистите кэш: `flutter clean`
2. Переустановите зависимости: `flutter pub get`
3. Перезапустите приложение

### Проблемы с зависимостями

```bash
# Очистка кэша
flutter clean

# Обновление зависимостей
flutter pub upgrade

# Переустановка зависимостей
flutter pub get
```

## Следующие шаги

- [ ] Создать экраны регистрации и входа
- [ ] Реализовать работу с API (HTTP клиент)
- [ ] Добавить хранение JWT токена
- [ ] Создать навигацию между экранами
- [ ] Добавить обработку ошибок
- [ ] Реализовать загрузку и отображение фотографий

## Полезные команды

```bash
# Проверка установки
flutter doctor

# Список устройств
flutter devices

# Запуск приложения
flutter run

# Сборка APK
flutter build apk

# Очистка проекта
flutter clean

# Анализ кода
flutter analyze

# Форматирование кода
flutter format .
```


