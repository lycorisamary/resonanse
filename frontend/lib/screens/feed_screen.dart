import 'package:flutter/material.dart';
import '../models/user.dart';
import '../services/api_service.dart';

/// Экран ленты кандидатов для свайпов.
class FeedScreen extends StatefulWidget {
  const FeedScreen({super.key});

  @override
  State<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  final List<User> _candidates = [];
  bool _isLoading = true;
  bool _isError = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadFeed();
  }

  Future<void> _loadFeed() async {
    setState(() {
      _isLoading = true;
      _isError = false;
      _errorMessage = null;
    });
    try {
      // Радиус 50 км для теста
      final users = await ApiService.getFeed(radiusKm: 50);
      setState(() {
        _candidates
          ..clear()
          ..addAll(users);
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _isError = true;
        _errorMessage = e.toString();
      });
    }
  }

  Future<void> _handleSwipe(User user, bool like) async {
    try {
      final isMatch = await ApiService.sendSwipe(
        targetUserId: user.id,
        decision: like,
      );

      if (!mounted) return;

      if (isMatch) {
        showDialog(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('У вас взаимный матч!'),
            content: Text(
              'Вы и ${user.firstName ?? user.email} лайкнули друг друга.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Ок'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка свайпа: $e')),
      );
    } finally {
      // Удаляем текущего кандидата из стека
      if (mounted) {
        setState(() {
          _candidates.remove(user);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_isError) {
      return Scaffold(
        appBar: AppBar(title: const Text('Лента')),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.error_outline, color: Colors.red, size: 48),
                const SizedBox(height: 16),
                Text(
                  _errorMessage ?? 'Ошибка загрузки ленты',
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: _loadFeed,
                  icon: const Icon(Icons.refresh),
                  label: const Text('Попробовать снова'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Лента'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadFeed,
            tooltip: 'Обновить ленту',
          ),
        ],
      ),
      body: _candidates.isEmpty
          ? const Center(
              child: Padding(
                padding: EdgeInsets.all(24.0),
                child: Text(
                  'На данный момент нет подходящих анкет поблизости.\nЗайди позже!',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 18, color: Colors.grey),
                ),
              ),
            )
          : Stack(
              children: [
                Positioned.fill(
                  child: Padding(
                    padding: const EdgeInsets.all(12.0),
                    child: _buildCardStack(),
                  ),
                ),
              ],
            ),
    );
  }

  // Строим стек карточек (берем последние 2 для эффекта колоды)
  Widget _buildCardStack() {
    // Берем последние 2 элемента, чтобы рисовать их стопкой
    final visibleCandidates = _candidates.length > 2 
        ? _candidates.sublist(_candidates.length - 2) 
        : _candidates;

    return Stack(
      children: visibleCandidates.map((user) {
        final index = visibleCandidates.indexOf(user);
        final isTop = index == visibleCandidates.length - 1;
        
        return Positioned.fill(
          child: AnimatedOpacity(
            opacity: isTop ? 1.0 : 0.8,
            duration: const Duration(milliseconds: 300),
            child: Transform.scale(
              scale: isTop ? 1.0 : 0.95,
              child: Transform.translate(
                offset: Offset(0, isTop ? 0 : 10),
                child: _buildSingleCard(user, isTop: isTop),
              ),
            ),
          ),
        );
      }).toList().reversed.toList(), // Рисуем снизу вверх
    );
  }

  Widget _buildSingleCard(User user, {required bool isTop}) {
    final fullName = user.firstName ?? user.email.split('@').first;
    final city = user.city ?? 'Город не указан';
    final bio = user.bio ?? 'О себе пока ничего не написано';
    final hasAvatar = user.avatarUrl != null && user.avatarUrl!.isNotEmpty;

    return Card(
      elevation: isTop ? 8 : 4,
      shadowColor: Colors.black45,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      clipBehavior: Clip.antiAlias,
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.grey.shade200, Colors.white],
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Верхняя часть с фото или заглушкой
            Expanded(
              flex: 3,
              child: Container(
                width: double.infinity,
                color: Colors.grey.shade300,
                child: hasAvatar
                    ? Image.network(
                        user.avatarUrl!,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const Center(
                          child: Icon(Icons.person, size: 64, color: Colors.grey),
                        ),
                      )
                    : const Center(
                        child: Icon(Icons.person, size: 64, color: Colors.grey),
                      ),
              ),
            ),
            // Нижняя часть с информацией
            Expanded(
              flex: 2,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      fullName,
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.location_on, size: 16, color: Colors.grey),
                        const SizedBox(width: 4),
                        Text(
                          city,
                          style: const TextStyle(color: Colors.grey, fontSize: 14),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Expanded(
                      child: Text(
                        bio,
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 14, color: Colors.black54),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            // Кнопки действий (только для верхней карты)
            if (isTop)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    _buildActionButton(
                      icon: Icons.close,
                      color: Colors.red.shade400,
                      onTap: () => _handleSwipe(user, false),
                    ),
                    _buildActionButton(
                      icon: Icons.favorite,
                      color: Colors.green.shade400,
                      onTap: () => _handleSwipe(user, true),
                    ),
                  ],
                ),
              )
            else
              const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 60,
        height: 60,
        decoration: BoxDecoration(
          color: Colors.white,
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: color.withOpacity(0.3),
              blurRadius: 8,
              spreadRadius: 2,
            ),
          ],
        ),
        child: Icon(icon, color: color, size: 32),
      ),
    );
  }
}