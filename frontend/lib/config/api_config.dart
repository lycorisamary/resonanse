/// Конфигурация API
class ApiConfig {
  // Базовый URL API бэкенда
  // Для Android эмулятора используйте: http://10.0.2.2:8000
  // Для физического устройства используйте IP вашего компьютера: http://192.168.x.x:8000
  static const String baseUrl = 'http://localhost:8000';
  static const String apiVersion = '/api/v1';
  
  static String get apiBaseUrl => '$baseUrl$apiVersion';
}

