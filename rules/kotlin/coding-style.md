---
paths:
  - "**/*.kt"
  - "**/*.kts"
---
# Kotlin Coding Style

> 扩展 [common/coding-style.md](../common/coding-style.md)，适用于 Android (Kotlin + Jetpack Compose) 技术栈。

## 类型和数据模型

### data class（不可变优先）
- 值对象使用 `data class`
- 实体使用普通 `class`
- 密封层级使用 `sealed class` / `sealed interface`

```kotlin
data class User(
    val id: String,
    val email: String,
    val name: String
)

sealed interface UiState<out T> {
    data object Loading : UiState<Nothing>
    data class Success<T>(val data: T) : UiState<T>
    data class Error(val message: String) : UiState<Nothing>
}
```

### 类型安全
- 使用 `value class` 包装原始类型 ID
- 使用 `sealed interface` 替代枚举（可携带数据）
- 避免 `Any`，不可信输入显式类型收窄

```kotlin
@JvmInline
value class UserId(val value: String)

fun loadUser(id: UserId): User = TODO()
```

## 不可变性

```kotlin
// 错误：原地修改
fun updateUser(user: MutableMap<String, Any>, name: String): Map<String, Any> {
    user["name"] = name
    return user
}

// 正确：copy 创建新实例
fun updateUser(user: User, name: String): User =
    user.copy(name = name)
```

- `val` 优于 `var`
- `List` 优于 `MutableList`（需要修改时使用 `buildList`）
- `Map` 优于 `MutableMap`

## 错误处理

```kotlin
import timber.log.Timber

suspend fun loadUser(userId: String): Result<User> =
    runCatching {
        riskyOperation(userId)
    }.onFailure { e ->
        Timber.e(e, "Failed to load user %s", userId)
    }

// 调用方
when (val result = loadUser(id)) {
    is Result.Success -> showUser(result.value)
    is Result.Failure -> showError(result.exception.message)
}
```

## Jetpack Compose

### Composable 规范
- Composable 函数使用 PascalCase
- 状态提升（State Hoisting）：UI 不持有状态
- 使用 `remember` / `rememberSaveable` 管理本地状态

```kotlin
@Composable
fun UserCard(
    user: User,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.clickable { onSelect(user.id) }) {
        Text(text = user.name)
        Text(text = user.email)
    }
}
```

### ViewModel
```kotlin
class UserViewModel(
    private val repository: UserRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<UiState<User>>(UiState.Loading)
    val uiState: StateFlow<UiState<User>> = _uiState.asStateFlow()

    fun loadUser(id: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            repository.getUser(id)
                .onSuccess { _uiState.value = UiState.Success(it) }
                .onFailure { _uiState.value = UiState.Error(it.message ?: "Unknown error") }
        }
    }
}
```

### 副作用
- `LaunchedEffect` 用于协程副作用
- `DisposableEffect` 用于需要清理的副作用
- `SideEffect` 用于每次重组时执行

```kotlin
@Composable
fun UserScreen(userId: String, viewModel: UserViewModel = viewModel()) {
    LaunchedEffect(userId) {
        viewModel.loadUser(userId)
    }

    val state by viewModel.uiState.collectAsStateWithLifecycle()

    when (state) {
        is UiState.Loading -> CircularProgressIndicator()
        is UiState.Success -> UserCard(user = (state as UiState.Success).data)
        is UiState.Error -> ErrorMessage(message = (state as UiState.Error).message)
    }
}
```

## 格式化

- 使用 `ktlint` 统一格式
- 遵循 [Kotlin 官方编码规范](https://kotlinlang.org/docs/coding-conventions.html)
- 行宽 120
- 尾随逗号启用

## 日志
- 生产代码中**禁止** `println()`
- 使用 `Timber`（Android）或 `SLF4J`（后端）
