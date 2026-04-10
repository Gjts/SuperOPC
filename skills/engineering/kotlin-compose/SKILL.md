---
name: kotlin-compose
description: Use when building Android apps with Kotlin and Jetpack Compose. Covers Compose UI patterns, navigation, ViewModel/state management, Material 3, and production-ready Android patterns.
---

## Kotlin + Jetpack Compose 模式

**宣布：** "我正在使用 kotlin-compose 技能。"

## 何时激活

- 构建 Compose UI 组件
- 设置 Navigation
- 管理 ViewModel 状态
- 实现 Material 3 主题
- 处理 Android 生命周期
- 优化 Compose 性能

## 组件设计

### 状态提升（State Hoisting）

```kotlin
// ✓ 无状态 Composable — 接收状态和回调
@Composable
fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    modifier: Modifier = Modifier,
) {
    TextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = modifier,
        trailingIcon = {
            IconButton(onClick = onSearch) {
                Icon(Icons.Default.Search, contentDescription = "搜索")
            }
        }
    )
}

// ✓ 有状态容器 — 持有状态，传递给无状态组件
@Composable
fun SearchScreen(viewModel: SearchViewModel = viewModel()) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    SearchBar(
        query = state.query,
        onQueryChange = viewModel::updateQuery,
        onSearch = viewModel::search,
    )
}
```

### 预览

```kotlin
@Preview(showBackground = true, widthDp = 360)
@Composable
private fun SearchBarPreview() {
    MyTheme {
        SearchBar(
            query = "Kotlin",
            onQueryChange = {},
            onSearch = {},
        )
    }
}
```

## ViewModel + UiState

```kotlin
data class UserListState(
    val users: List<User> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val query: String = "",
)

class UserListViewModel(
    private val repository: UserRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(UserListState())
    val uiState: StateFlow<UserListState> = _uiState.asStateFlow()

    init { loadUsers() }

    fun loadUsers() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            repository.getUsers()
                .onSuccess { users ->
                    _uiState.update { it.copy(users = users, isLoading = false) }
                }
                .onFailure { e ->
                    _uiState.update { it.copy(error = e.message, isLoading = false) }
                }
        }
    }

    fun updateQuery(query: String) {
        _uiState.update { it.copy(query = query) }
    }
}
```

## Navigation

```kotlin
// 类型安全路由（Navigation Compose 2.8+）
@Serializable data object Home
@Serializable data class UserDetail(val userId: String)
@Serializable data object Settings

@Composable
fun AppNavHost(navController: NavHostController = rememberNavController()) {
    NavHost(navController = navController, startDestination = Home) {
        composable<Home> {
            HomeScreen(
                onUserClick = { id -> navController.navigate(UserDetail(id)) },
                onSettingsClick = { navController.navigate(Settings) },
            )
        }
        composable<UserDetail> { backStackEntry ->
            val route = backStackEntry.toRoute<UserDetail>()
            UserDetailScreen(userId = route.userId)
        }
        composable<Settings> {
            SettingsScreen()
        }
    }
}
```

## Material 3 主题

```kotlin
@Composable
fun MyTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) {
        dynamicDarkColorScheme(LocalContext.current)
    } else {
        dynamicLightColorScheme(LocalContext.current)
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        content = content,
    )
}

val AppTypography = Typography(
    headlineLarge = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 28.sp,
    ),
    bodyLarge = TextStyle(
        fontSize = 16.sp,
        lineHeight = 24.sp,
    ),
)
```

## 列表性能

```kotlin
// ✓ LazyColumn + key
LazyColumn {
    items(users, key = { it.id }) { user ->
        UserCard(user = user, onClick = { onUserClick(user.id) })
    }
}

// ✓ 大列表分页
val pager = Pager(PagingConfig(pageSize = 20)) { UserPagingSource(api) }
val users = pager.flow.cachedIn(viewModelScope)

// Composable 中
val lazyPagingItems = users.collectAsLazyPagingItems()
LazyColumn {
    items(lazyPagingItems.itemCount) { index ->
        lazyPagingItems[index]?.let { UserCard(it) }
    }
}
```

## 项目结构

```
app/src/main/java/com/myapp/
  di/                    # 依赖注入（Hilt）
  data/
    local/               # Room DAO
    remote/              # Retrofit API
    repository/          # Repository 实现
  domain/
    model/               # 领域模型
    repository/          # Repository 接口
    usecase/             # 用例
  ui/
    components/          # 共享 Composable
    theme/               # Material 3 主题
    screens/
      home/              # HomeScreen + ViewModel
      user/              # UserScreen + ViewModel
  navigation/            # NavHost + 路由定义
  MainActivity.kt
```

## 一人公司 Android 清单

- [ ] MVVM + UiState（单向数据流）
- [ ] Hilt 依赖注入
- [ ] 类型安全 Navigation
- [ ] Material 3 + Dynamic Color
- [ ] collectAsStateWithLifecycle（生命周期感知）
- [ ] LazyColumn + key 列表优化
- [ ] 错误/加载/空状态处理
- [ ] ProGuard/R8 代码混淆
