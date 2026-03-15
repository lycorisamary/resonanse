import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import 'admin_panel_screen.dart';

/// Экран профиля пользователя
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  User? _user;
  bool _isLoading = true;
  bool _isEditing = false;
  String? _error;

  // Контроллеры для формы редактирования
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _bioController = TextEditingController();
  DateTime? _selectedBirthdate;
  String? _selectedCity;
  List<String> _cities = [];
  
  // Контроллеры для смены пароля
  final _oldPasswordController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscureOldPassword = true;
  bool _obscureNewPassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void initState() {
    super.initState();
    _loadUserProfile();
    _loadCities();
  }

  /// Загрузка списка городов
  Future<void> _loadCities() async {
    try {
      // Пытаемся загрузить города с сервера
      final cities = await ApiService.getCities();
      if (mounted) {
        setState(() {
          _cities = cities;
        });
      }
    } catch (e) {
      // Если не удалось загрузить с сервера, используем хардкод список
      print('Ошибка загрузки городов: $e. Используется список по умолчанию.');
      if (mounted) {
        setState(() {
          _cities = [
            'Москва',
            'Санкт-Петербург',
            'Новосибирск',
            'Екатеринбург',
            'Казань',
            'Нижний Новгород',
            'Челябинск',
            'Самара',
            'Омск',
            'Ростов-на-Дону',
          ];
        });
      }
    }
  }

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _bioController.dispose();
    _oldPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  /// Загрузка профиля пользователя
  Future<void> _loadUserProfile() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final user = await ApiService.getCurrentUser();
      setState(() {
        _user = user;
        _firstNameController.text = user.firstName ?? '';
        _lastNameController.text = user.lastName ?? '';
        _bioController.text = user.bio ?? '';
        _selectedBirthdate = user.birthdate;
        _selectedCity = user.city;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Ошибка загрузки профиля: $e';
        _isLoading = false;
      });
    }
  }

  /// Загрузка аватара из галереи
  Future<void> _pickImageFromGallery() async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? image = await picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (image != null) {
        await _uploadAvatar(File(image.path));
      }
    } catch (e) {
      _showError('Ошибка выбора изображения: $e');
    }
  }

  /// Загрузка аватара с камеры
  Future<void> _pickImageFromCamera() async {
    try {
      final ImagePicker picker = ImagePicker();
      final XFile? image = await picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
      );

      if (image != null) {
        await _uploadAvatar(File(image.path));
      }
    } catch (e) {
      _showError('Ошибка съемки: $e');
    }
  }

  /// Загрузка аватара на сервер
  Future<void> _uploadAvatar(File imageFile) async {
    setState(() {
      _isLoading = true;
    });

    try {
      final user = await ApiService.uploadAvatar(imageFile);
      setState(() {
        _user = user;
        _isLoading = false;
      });
      _showSuccess('Аватар успешно загружен');
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _showError('Ошибка загрузки аватара: $e');
    }
  }

  /// Сохранение изменений профиля
  Future<void> _saveProfile() async {
    if (_user == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final userUpdate = UserUpdate(
        firstName: _firstNameController.text.isEmpty
            ? null
            : _firstNameController.text,
        lastName: _lastNameController.text.isEmpty
            ? null
            : _lastNameController.text,
        bio: _bioController.text.isEmpty ? null : _bioController.text,
        birthdate: _selectedBirthdate,
        city: _selectedCity,
      );

      final updatedUser = await ApiService.updateProfile(userUpdate);
      setState(() {
        _user = updatedUser;
        _isEditing = false;
        _isLoading = false;
      });
      _showSuccess('Профиль успешно обновлен');
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      _showError('Ошибка обновления профиля: $e');
    }
  }

  /// Показать диалог выбора источника изображения
  void _showImageSourceDialog() {
    showModalBottomSheet(
      context: context,
      builder: (BuildContext context) {
        return SafeArea(
          child: Wrap(
            children: [
              ListTile(
                leading: const Icon(Icons.photo_library),
                title: const Text('Галерея'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImageFromGallery();
                },
              ),
              ListTile(
                leading: const Icon(Icons.photo_camera),
                title: const Text('Камера'),
                onTap: () {
                  Navigator.pop(context);
                  _pickImageFromCamera();
                },
              ),
            ],
          ),
        );
      },
    );
  }

  /// Показать диалог выбора даты рождения
  Future<void> _selectBirthdate() async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: _selectedBirthdate ?? DateTime.now().subtract(
        const Duration(days: 365 * 18),
      ),
      firstDate: DateTime(1900),
      lastDate: DateTime.now(),
      locale: const Locale('ru', 'RU'),
    );

    if (picked != null) {
      setState(() {
        _selectedBirthdate = picked;
      });
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.green,
      ),
    );
  }

  /// Показать диалог смены пароля
  void _showChangePasswordDialog() {
    _oldPasswordController.clear();
    _newPasswordController.clear();
    _confirmPasswordController.clear();
    
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            return AlertDialog(
              title: const Text('Смена пароля'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: _oldPasswordController,
                      obscureText: _obscureOldPassword,
                      decoration: InputDecoration(
                        labelText: 'Текущий пароль',
                        prefixIcon: const Icon(Icons.lock),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscureOldPassword ? Icons.visibility : Icons.visibility_off,
                          ),
                          onPressed: () {
                            setDialogState(() {
                              _obscureOldPassword = !_obscureOldPassword;
                            });
                          },
                        ),
                        border: const OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _newPasswordController,
                      obscureText: _obscureNewPassword,
                      decoration: InputDecoration(
                        labelText: 'Новый пароль',
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscureNewPassword ? Icons.visibility : Icons.visibility_off,
                          ),
                          onPressed: () {
                            setDialogState(() {
                              _obscureNewPassword = !_obscureNewPassword;
                            });
                          },
                        ),
                        border: const OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _confirmPasswordController,
                      obscureText: _obscureConfirmPassword,
                      decoration: InputDecoration(
                        labelText: 'Подтвердите новый пароль',
                        prefixIcon: const Icon(Icons.lock_outline),
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscureConfirmPassword ? Icons.visibility : Icons.visibility_off,
                          ),
                          onPressed: () {
                            setDialogState(() {
                              _obscureConfirmPassword = !_obscureConfirmPassword;
                            });
                          },
                        ),
                        border: const OutlineInputBorder(),
                      ),
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Отмена'),
                ),
                ElevatedButton(
                  onPressed: () async {
                    if (_newPasswordController.text.length < 8) {
                      _showError('Пароль должен быть не менее 8 символов');
                      return;
                    }
                    if (_newPasswordController.text != _confirmPasswordController.text) {
                      _showError('Пароли не совпадают');
                      return;
                    }
                    
                    try {
                      await ApiService.changePassword(
                        oldPassword: _oldPasswordController.text,
                        newPassword: _newPasswordController.text,
                      );
                      Navigator.of(context).pop();
                      _showSuccess('Пароль успешно изменен');
                    } catch (e) {
                      _showError('Ошибка смены пароля: $e');
                    }
                  },
                  child: const Text('Изменить'),
                ),
              ],
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading && _user == null) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null && _user == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Профиль')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(_error!),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: _loadUserProfile,
                child: const Text('Повторить'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Мой профиль'),
        actions: [
          if (_isEditing)
            IconButton(
              icon: const Icon(Icons.check),
              onPressed: _saveProfile,
              tooltip: 'Сохранить',
            )
          else ...[
            if (_user?.isAdmin == true)
              IconButton(
                icon: const Icon(Icons.admin_panel_settings),
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (context) => const AdminPanelScreen(),
                    ),
                  );
                },
                tooltip: 'Админ-панель',
              ),
            IconButton(
              icon: const Icon(Icons.lock),
              onPressed: _showChangePasswordDialog,
              tooltip: 'Сменить пароль',
            ),
            IconButton(
              icon: const Icon(Icons.edit),
              onPressed: () {
                setState(() {
                  _isEditing = true;
                });
              },
              tooltip: 'Редактировать',
            ),
          ],
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Аватар
            Stack(
              children: [
                CircleAvatar(
                  radius: 60,
                  child: _user?.avatarUrl != null && _user!.avatarUrl!.isNotEmpty
                      ? ClipOval(
                          child: CachedNetworkImage(
                            imageUrl: _user!.avatarUrl!,
                            width: 120,
                            height: 120,
                            fit: BoxFit.cover,
                            placeholder: (context, url) => const CircularProgressIndicator(),
                            errorWidget: (context, url, error) => const Icon(Icons.person, size: 60),
                          ),
                        )
                      : const Icon(Icons.person, size: 60),
                ),
                Positioned(
                  bottom: 0,
                  right: 0,
                  child: CircleAvatar(
                    radius: 20,
                    backgroundColor: Theme.of(context).primaryColor,
                    child: IconButton(
                      icon: const Icon(Icons.camera_alt, size: 20),
                      color: Colors.white,
                      onPressed: _showImageSourceDialog,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Информация о пользователе
            if (_isEditing) _buildEditForm() else _buildViewForm(),
          ],
        ),
      ),
    );
  }

  Widget _buildViewForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Основная информация',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                _buildInfoRow('Имя', _user?.firstName ?? 'Не указано'),
                _buildInfoRow('Фамилия', _user?.lastName ?? 'Не указано'),
                _buildInfoRow('Email', _user?.email ?? ''),
                _buildInfoRow('Город', _user?.city ?? 'Не указано'),
                _buildInfoRow(
                  'Дата рождения',
                  _user?.birthdate != null
                      ? '${_user!.birthdate!.day}.${_user!.birthdate!.month}.${_user!.birthdate!.year}'
                      : 'Не указано',
                ),
              ],
            ),
          ),
        ),
        if (_user?.bio != null && _user!.bio!.isNotEmpty) ...[
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'О себе',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(_user!.bio!),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildEditForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _firstNameController,
          decoration: const InputDecoration(
            labelText: 'Имя',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _lastNameController,
          decoration: const InputDecoration(
            labelText: 'Фамилия',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),
        InkWell(
          onTap: _selectBirthdate,
          child: InputDecorator(
            decoration: const InputDecoration(
              labelText: 'Дата рождения',
              border: OutlineInputBorder(),
            ),
            child: Text(
              _selectedBirthdate != null
                  ? '${_selectedBirthdate!.day}.${_selectedBirthdate!.month}.${_selectedBirthdate!.year}'
                  : 'Выберите дату',
            ),
          ),
        ),
        const SizedBox(height: 16),
        DropdownButtonFormField<String>(
          initialValue: _selectedCity,
          decoration: const InputDecoration(
            labelText: 'Город',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.location_city),
          ),
          items: [
            const DropdownMenuItem<String>(
              value: null,
              child: Text('Не выбран'),
            ),
            ..._cities.map((city) => DropdownMenuItem<String>(
              value: city,
              child: Text(city),
            )),
          ],
          onChanged: (value) {
            setState(() {
              _selectedCity = value;
            });
          },
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _bioController,
          decoration: const InputDecoration(
            labelText: 'О себе',
            border: OutlineInputBorder(),
            hintText: 'Расскажите о себе...',
          ),
          maxLines: 5,
        ),
        const SizedBox(height: 24),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _isEditing = false;
                });
              },
              child: const Text('Отмена'),
            ),
            ElevatedButton(
              onPressed: _saveProfile,
              child: const Text('Сохранить'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}

