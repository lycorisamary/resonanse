/// Модель пользователя
class User {
  final int id;
  final String email;
  final String? firstName;
  final String? lastName;
  final String? bio;
  final String? avatarUrl;
  final DateTime? birthdate;
  final String? city;
  final double? latitude;
  final double? longitude;
  final bool isActive;
  final bool isVerified;
  final bool isAdmin;
  final DateTime createdAt;
  final DateTime updatedAt;

  User({
    required this.id,
    required this.email,
    this.firstName,
    this.lastName,
    this.bio,
    this.avatarUrl,
    this.birthdate,
    this.city,
    this.latitude,
    this.longitude,
    required this.isActive,
    required this.isVerified,
    this.isAdmin = false,
    required this.createdAt,
    required this.updatedAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      email: json['email'] as String,
      firstName: json['first_name'] as String?,
      lastName: json['last_name'] as String?,
      bio: json['bio'] as String?,
      avatarUrl: json['avatar_url'] as String?,
      birthdate: json['birthdate'] != null
          ? DateTime.parse(json['birthdate'] as String)
          : null,
      city: json['city'] as String?,
      latitude: json['latitude'] != null
          ? (json['latitude'] as num).toDouble()
          : null,
      longitude: json['longitude'] != null
          ? (json['longitude'] as num).toDouble()
          : null,
      isActive: json['is_active'] as bool,
      isVerified: json['is_verified'] as bool,
      isAdmin: json['is_admin'] as bool? ?? false,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'first_name': firstName,
      'last_name': lastName,
      'bio': bio,
      'avatar_url': avatarUrl,
      'birthdate': birthdate?.toIso8601String(),
      'city': city,
      'latitude': latitude,
      'longitude': longitude,
      'is_active': isActive,
      'is_verified': isVerified,
      'is_admin': isAdmin,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

/// Модель для обновления профиля
class UserUpdate {
  final String? firstName;
  final String? lastName;
  final String? bio;
  final DateTime? birthdate;
  final String? city;
  final double? latitude;
  final double? longitude;

  UserUpdate({
    this.firstName,
    this.lastName,
    this.bio,
    this.birthdate,
    this.city,
    this.latitude,
    this.longitude,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> json = {};
    if (firstName != null) json['first_name'] = firstName;
    if (lastName != null) json['last_name'] = lastName;
    if (bio != null) json['bio'] = bio;
    if (birthdate != null) json['birthdate'] = birthdate!.toIso8601String().split('T')[0];
    if (city != null) json['city'] = city;
    if (latitude != null) json['latitude'] = latitude;
    if (longitude != null) json['longitude'] = longitude;
    return json;
  }
}

