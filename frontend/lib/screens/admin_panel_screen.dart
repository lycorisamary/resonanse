import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/api_service.dart';

/// Экран админ-панели
class AdminPanelScreen extends StatefulWidget {
  const AdminPanelScreen({super.key});

  @override
  State<AdminPanelScreen> createState() => _AdminPanelScreenState();
}

class _AdminPanelScreenState extends State<AdminPanelScreen> {
  List<User> _users = [];
  bool _isLoading = true;
  String? _error;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  Future<void> _loadUsers() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final users = await ApiService.getAllUsers();
      setState(() {
        _users = users;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Ошибка загрузки пользователей: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _toggleUserActive(User user) async {
    try {
      if (user.isActive) {
        await ApiService.deactivateUser(user.id);
      } else {
        await ApiService.activateUser(user.id);
      }
      await _loadUsers();
      _showSuccess('Пользователь ${user.isActive ? "деактивирован" : "активирован"}');
    } catch (e) {
      _showError('Ошибка: $e');
    }
  }

  Future<void> _deleteUser(User user) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Удаление пользователя'),
        content: Text('Вы уверены, что хотите удалить пользователя ${user.email}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Отмена'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Удалить'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ApiService.deleteUser(user.id);
        await _loadUsers();
        _showSuccess('Пользователь удален');
      } catch (e) {
        _showError('Ошибка удаления: $e');
      }
    }
  }

  void _showUserDetails(User user) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('${user.firstName ?? ''} ${user.lastName ?? ''}'.trim().isEmpty
            ? user.email
            : '${user.firstName ?? ''} ${user.lastName ?? ''}'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildDetailRow('ID', user.id.toString()),
              _buildDetailRow('Email', user.email),
              _buildDetailRow('Имя', user.firstName ?? 'Не указано'),
              _buildDetailRow('Фамилия', user.lastName ?? 'Не указано'),
              _buildDetailRow('Город', user.city ?? 'Не указано'),
              _buildDetailRow('Активен', user.isActive ? 'Да' : 'Нет'),
              _buildDetailRow('Верифицирован', user.isVerified ? 'Да' : 'Нет'),
              _buildDetailRow('Администратор', user.isAdmin ? 'Да' : 'Нет'),
              if (user.bio != null && user.bio!.isNotEmpty)
                _buildDetailRow('О себе', user.bio!),
              _buildDetailRow('Создан', user.createdAt.toString().split('.')[0]),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Закрыть'),
          ),
        ],
      ),
    );
  }

  Future<void> _showEditUserDialog(User user) async {
    final firstNameController = TextEditingController(text: user.firstName ?? '');
    final lastNameController = TextEditingController(text: user.lastName ?? '');
    final cityController = TextEditingController(text: user.city ?? '');
    final bioController = TextEditingController(text: user.bio ?? '');

    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Редактирование пользователя'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: firstNameController,
                decoration: const InputDecoration(
                  labelText: 'Имя',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: lastNameController,
                decoration: const InputDecoration(
                  labelText: 'Фамилия',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: cityController,
                decoration: const InputDecoration(
                  labelText: 'Город',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: bioController,
                decoration: const InputDecoration(
                  labelText: 'О себе',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
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
              try {
                final update = UserUpdate(
                  firstName: firstNameController.text.trim().isEmpty
                      ? null
                      : firstNameController.text.trim(),
                  lastName: lastNameController.text.trim().isEmpty
                      ? null
                      : lastNameController.text.trim(),
                  city: cityController.text.trim().isEmpty
                      ? null
                      : cityController.text.trim(),
                  bio: bioController.text.trim().isEmpty
                      ? null
                      : bioController.text.trim(),
                );
                await ApiService.updateUserAdmin(user.id, update);
                if (mounted) {
                  Navigator.of(context).pop();
                  await _loadUsers();
                  _showSuccess('Пользователь обновлён');
                }
              } catch (e) {
                _showError('Ошибка обновления: $e');
              }
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
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

  List<User> get _filteredUsers {
    if (_searchQuery.isEmpty) {
      return _users;
    }
    final query = _searchQuery.toLowerCase();
    return _users.where((user) {
      return user.email.toLowerCase().contains(query) ||
          (user.firstName?.toLowerCase().contains(query) ?? false) ||
          (user.lastName?.toLowerCase().contains(query) ?? false) ||
          (user.city?.toLowerCase().contains(query) ?? false);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Админ-панель'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadUsers,
            tooltip: 'Обновить',
          ),
        ],
      ),
      body: Column(
        children: [
          // Поиск
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              decoration: InputDecoration(
                labelText: 'Поиск пользователей',
                prefixIcon: const Icon(Icons.search),
                border: const OutlineInputBorder(),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          setState(() {
                            _searchQuery = '';
                          });
                        },
                      )
                    : null,
              ),
              onChanged: (value) {
                setState(() {
                  _searchQuery = value;
                });
              },
            ),
          ),
          // Список пользователей
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(_error!),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              onPressed: _loadUsers,
                              child: const Text('Повторить'),
                            ),
                          ],
                        ),
                      )
                    : _filteredUsers.isEmpty
                        ? const Center(child: Text('Пользователи не найдены'))
                        : ListView.builder(
                            itemCount: _filteredUsers.length,
                            itemBuilder: (context, index) {
                              final user = _filteredUsers[index];
                              return Card(
                                margin: const EdgeInsets.symmetric(
                                  horizontal: 16,
                                  vertical: 8,
                                ),
                                child: ListTile(
                                  leading: CircleAvatar(
                                    child: Text(
                                      user.firstName?.isNotEmpty == true
                                          ? user.firstName![0].toUpperCase()
                                          : user.email[0].toUpperCase(),
                                    ),
                                  ),
                                  title: Text(
                                    '${user.firstName ?? ''} ${user.lastName ?? ''}'.trim().isEmpty
                                        ? user.email
                                        : '${user.firstName ?? ''} ${user.lastName ?? ''}',
                                  ),
                                  subtitle: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(user.email),
                                      if (user.city != null) Text(user.city!),
                                    ],
                                  ),
                                  trailing: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(
                                        user.isActive ? Icons.check_circle : Icons.cancel,
                                        color: user.isActive ? Colors.green : Colors.red,
                                      ),
                                      if (user.isAdmin)
                                        const Padding(
                                          padding: EdgeInsets.only(left: 8),
                                          child: Icon(Icons.admin_panel_settings, color: Colors.orange),
                                        ),
                                    ],
                                  ),
                                  onTap: () => _showUserDetails(user),
                                  onLongPress: () {
                                    showModalBottomSheet(
                                      context: context,
                                      builder: (context) => SafeArea(
                                        child: Column(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            ListTile(
                                              leading: const Icon(Icons.edit),
                                              title: const Text('Редактировать'),
                                              onTap: () {
                                                Navigator.pop(context);
                                                _showEditUserDialog(user);
                                              },
                                            ),
                                            ListTile(
                                              leading: Icon(
                                                user.isActive ? Icons.block : Icons.check_circle,
                                              ),
                                              title: Text(user.isActive ? 'Деактивировать' : 'Активировать'),
                                              onTap: () {
                                                Navigator.pop(context);
                                                _toggleUserActive(user);
                                              },
                                            ),
                                            ListTile(
                                              leading: const Icon(Icons.delete, color: Colors.red),
                                              title: const Text('Удалить', style: TextStyle(color: Colors.red)),
                                              onTap: () {
                                                Navigator.pop(context);
                                                _deleteUser(user);
                                              },
                                            ),
                                          ],
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}

