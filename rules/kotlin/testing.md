---
paths:
  - "**/*.kt"
---
# Kotlin Testing

> 扩展 [common/testing.md](../common/testing.md)，适用于 Android + Jetpack Compose。

## 框架选择

| 场景 | 框架 | 依赖 |
|------|------|------|
| 单元测试 | JUnit 5 | `junit-jupiter` |
| Mock | MockK | `io.mockk:mockk` |
| 断言 | Kotest | `io.kotest:kotest-assertions-core` |
| Compose UI | Compose Test | `androidx.compose.ui:ui-test-junit4` |
| 集成测试 | Robolectric | `org.robolectric:robolectric` |
| E2E | UI Automator | `androidx.test.uiautomator` |

## 单元测试结构

```kotlin
class UserServiceTest {

    private val repo = mockk<UserRepository>()
    private val sut = UserService(repo)

    @Test
    fun `createUser with valid input returns user`() = runTest {
        // Arrange
        val request = CreateUserRequest(email = "test@example.com", name = "Test")
        coEvery { repo.save(any()) } returns User(id = "1", email = "test@example.com", name = "Test")

        // Act
        val result = sut.create(request)

        // Assert
        result.email shouldBe "test@example.com"
        coVerify(exactly = 1) { repo.save(any()) }
    }

    @Test
    fun `createUser with invalid email throws ValidationException`() = runTest {
        val request = CreateUserRequest(email = "bad", name = "Test")

        shouldThrow<ValidationException> {
            sut.create(request)
        }
    }
}
```

## ViewModel 测试

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class UserViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private val repository = mockk<UserRepository>()
    private lateinit var viewModel: UserViewModel

    @BeforeEach
    fun setup() {
        viewModel = UserViewModel(repository)
    }

    @Test
    fun `loadUser updates state to Success`() = runTest {
        val user = User(id = "1", email = "test@example.com", name = "Test")
        coEvery { repository.getUser("1") } returns Result.success(user)

        viewModel.loadUser("1")

        viewModel.uiState.value shouldBe UiState.Success(user)
    }

    @Test
    fun `loadUser on failure updates state to Error`() = runTest {
        coEvery { repository.getUser("1") } returns Result.failure(Exception("Not found"))

        viewModel.loadUser("1")

        viewModel.uiState.value.shouldBeInstanceOf<UiState.Error>()
    }
}
```

## Compose UI 测试

```kotlin
class UserCardTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `UserCard displays user name and email`() {
        val user = User(id = "1", email = "test@example.com", name = "Test User")

        composeTestRule.setContent {
            UserCard(user = user, onSelect = {})
        }

        composeTestRule.onNodeWithText("Test User").assertIsDisplayed()
        composeTestRule.onNodeWithText("test@example.com").assertIsDisplayed()
    }

    @Test
    fun `UserCard calls onSelect when clicked`() {
        val onSelect = mockk<(String) -> Unit>(relaxed = true)
        val user = User(id = "1", email = "test@example.com", name = "Test")

        composeTestRule.setContent {
            UserCard(user = user, onSelect = onSelect)
        }

        composeTestRule.onNodeWithText("Test").performClick()
        verify { onSelect("1") }
    }
}
```

## 测试命名约定

使用反引号包裹的描述性名称：

```kotlin
@Test
fun `createUser with valid input returns user`() { ... }

@Test
fun `createUser with duplicate email throws Conflict`() { ... }

@Test
fun `getUser with invalid id returns NotFound`() { ... }
```

## MainDispatcherRule

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class MainDispatcherRule(
    private val dispatcher: TestDispatcher = UnconfinedTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```
