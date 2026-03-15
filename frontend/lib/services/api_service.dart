import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';
import '../models/user.dart';

/// Сервис для работы с API
class ApiService {
  static const String _tokenKey = 'auth_token';

  /// Получение сохраненного токена
  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  /// Сохранение токена
  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  /// Удаление токена
  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }

  /// Создание заголовков с авторизацией
  static Future<Map<String, String>> _getHeaders({
    bool includeAuth = true,
    bool isMultipart = false,
  }) async {
    final headers = <String, String>{};
    
    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
    }
    
    if (includeAuth) {
      final token = await _getToken();
      if (token != null) {
        headers['Authorization'] = 'Bearer $token';
      }
    }
    
    return headers;
  }

  /// Регистрация нового пользователя
  static Future<User> register({
    required String email,
    required String password,
    String? firstName,
    String? lastName,
  }) async {
    final headers = await _getHeaders(includeAuth: false);
    final response = await http.post(
      Uri.parse('${ApiConfig.apiBaseUrl}/auth/register'),
      headers: headers,
      body: _toJsonString({
        'email': email,
        'password': password,
        if (firstName != null) 'first_name': firstName,
        if (lastName != null) 'last_name': lastName,
      }),
    );

    if (response.statusCode == 201) {
      return User.fromJson(
        _parseJson(response.body) as Map<String, dynamic>,
      );
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка регистрации: ${response.statusCode}');
    }
  }

  /// Вход в систему
  static Future<String> login({
    required String email,
    required String password,
  }) async {
    final headers = await _getHeaders(includeAuth: false);
    final response = await http.post(
      Uri.parse('${ApiConfig.apiBaseUrl}/auth/login'),
      headers: headers,
      body: _toJsonString({
        'email': email,
        'password': password,
      }),
    );

    if (response.statusCode == 200) {
      final data = _parseJson(response.body) as Map<String, dynamic>;
      final token = data['access_token'] as String;
      await saveToken(token);
      return token;
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка входа: ${response.statusCode}');
    }
  }

  /// Выход из системы
  static Future<void> logout() async {
    await clearToken();
  }

  /// Проверка авторизации
  static Future<bool> isAuthenticated() async {
    final token = await _getToken();
    return token != null && token.isNotEmpty;
  }

  /// Получение информации о текущем пользователе
  static Future<User> getCurrentUser() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('${ApiConfig.apiBaseUrl}/users/me'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return User.fromJson(
        _parseJson(response.body) as Map<String, dynamic>,
      );
    } else {
      throw Exception('Ошибка получения пользователя: ${response.statusCode}');
    }
  }

  /// Обновление профиля пользователя
  static Future<User> updateProfile(UserUpdate userUpdate) async {
    final headers = await _getHeaders();
    final response = await http.patch(
      Uri.parse('${ApiConfig.apiBaseUrl}/users/me'),
      headers: headers,
      body: _toJsonString(userUpdate.toJson()),
    );

    if (response.statusCode == 200) {
      return User.fromJson(
        _parseJson(response.body) as Map<String, dynamic>,
      );
    } else {
      throw Exception('Ошибка обновления профиля: ${response.statusCode}');
    }
  }

  /// Загрузка аватара
  static Future<User> uploadAvatar(File imageFile) async {
    final token = await _getToken();
    if (token == null) {
      throw Exception('Токен авторизации не найден');
    }

    final request = http.MultipartRequest(
      'POST',
      Uri.parse('${ApiConfig.apiBaseUrl}/users/upload-avatar'),
    );

    request.headers['Authorization'] = 'Bearer $token';
    request.files.add(
      await http.MultipartFile.fromPath('file', imageFile.path),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return User.fromJson(
        _parseJson(response.body) as Map<String, dynamic>,
      );
    } else {
      throw Exception('Ошибка загрузки аватара: ${response.statusCode}');
    }
  }

  /// Парсинг JSON
  static dynamic _parseJson(String jsonString) {
    return jsonDecode(jsonString);
  }

  /// Смена пароля
  static Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('${ApiConfig.apiBaseUrl}/users/change-password'),
      headers: headers,
      body: _toJsonString({
        'old_password': oldPassword,
        'new_password': newPassword,
      }),
    );

    if (response.statusCode == 200) {
      return;
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка смены пароля: ${response.statusCode}');
    }
  }

  /// Получение списка городов
  static Future<List<String>> getCities() async {
    final response = await http.get(
      Uri.parse('${ApiConfig.apiBaseUrl}/cities/cities'),
    );

    if (response.statusCode == 200) {
      final data = _parseJson(response.body) as List<dynamic>;
      return data.map((city) => city as String).toList();
    } else {
      throw Exception('Ошибка получения списка городов: ${response.statusCode}');
    }
  }

  /// Обновление геолокации пользователя (для гео-поиска и свайпов)
  static Future<void> updateLocation({
    required double latitude,
    required double longitude,
  }) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('${ApiConfig.apiBaseUrl}/users/location'),
      headers: headers,
      body: _toJsonString({
        'latitude': latitude,
        'longitude': longitude,
      }),
    );

    if (response.statusCode != 200) {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка обновления геолокации: ${response.statusCode}');
    }
  }

  /// Получение ленты кандидатов для свайпов
  static Future<List<User>> getFeed({double radiusKm = 10}) async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('${ApiConfig.apiBaseUrl}/feed?radius_km=$radiusKm'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final data = _parseJson(response.body) as List<dynamic>;
      return data
          .map((userJson) => User.fromJson(userJson as Map<String, dynamic>))
          .toList();
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка получения фида: ${response.statusCode}');
    }
  }

  /// Отправка свайпа (лайк/дизлайк) по пользователю
  /// Возвращает true, если получился взаимный матч.
  static Future<bool> sendSwipe({
    required int targetUserId,
    required bool decision,
  }) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('${ApiConfig.apiBaseUrl}/swipes'),
      headers: headers,
      body: _toJsonString({
        'target_user_id': targetUserId,
        'decision': decision,
      }),
    );

    if (response.statusCode == 200) {
      final data = _parseJson(response.body) as Map<String, dynamic>;
      return (data['is_match'] as bool?) ?? false;
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка свайпа: ${response.statusCode}');
    }
  }

  /// Получение списка всех пользователей (только для админа)
  static Future<List<User>> getAllUsers() async {
    final headers = await _getHeaders();
    final response = await http.get(
      Uri.parse('${ApiConfig.apiBaseUrl}/admin/users'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      final data = _parseJson(response.body) as List<dynamic>;
      return data.map((userJson) => User.fromJson(userJson as Map<String, dynamic>)).toList();
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка получения пользователей: ${response.statusCode}');
    }
  }

  /// Обновление пользователя администратором
  static Future<User> updateUserAdmin(int userId, UserUpdate userUpdate) async {
    final headers = await _getHeaders();
    final response = await http.patch(
      Uri.parse('${ApiConfig.apiBaseUrl}/admin/users/$userId'),
      headers: headers,
      body: _toJsonString(userUpdate.toJson()),
    );

    if (response.statusCode == 200) {
      return User.fromJson(
        _parseJson(response.body) as Map<String, dynamic>,
      );
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка обновления пользователя: ${response.statusCode}');
    }
  }

  /// Активация пользователя
  static Future<User> activateUser(int userId) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('${ApiConfig.apiBaseUrl}/admin/users/$userId/activate'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return User.fromJson(
        _parseJson(response.body) as Map<String, dynamic>,
      );
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка активации пользователя: ${response.statusCode}');
    }
  }

  /// Деактивация пользователя
  static Future<User> deactivateUser(int userId) async {
    final headers = await _getHeaders();
    final response = await http.post(
      Uri.parse('${ApiConfig.apiBaseUrl}/admin/users/$userId/deactivate'),
      headers: headers,
    );

    if (response.statusCode == 200) {
      return User.fromJson(
        _parseJson(response.body) as Map<String, dynamic>,
      );
    } else {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка деактивации пользователя: ${response.statusCode}');
    }
  }

  /// Удаление пользователя
  static Future<void> deleteUser(int userId) async {
    final headers = await _getHeaders();
    final response = await http.delete(
      Uri.parse('${ApiConfig.apiBaseUrl}/admin/users/$userId'),
      headers: headers,
    );

    if (response.statusCode != 200) {
      final errorBody = _parseJson(response.body);
      throw Exception(errorBody['detail'] ?? 'Ошибка удаления пользователя: ${response.statusCode}');
    }
  }

  /// Конвертация в JSON строку
  static String _toJsonString(Map<String, dynamic> json) {
    return jsonEncode(json);
  }
}

