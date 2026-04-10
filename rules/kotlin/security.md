---
paths:
  - "**/*.kt"
---
# Kotlin Security

> 扩展 [common/security.md](../common/security.md)，适用于 Android (Kotlin + Jetpack Compose)。

## 网络安全

### Network Security Config
```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
</network-security-config>
```

### OkHttp + Certificate Pinning
```kotlin
val client = OkHttpClient.Builder()
    .certificatePinner(
        CertificatePinner.Builder()
            .add("api.yourdomain.com", "sha256/AAAA...")
            .build()
    )
    .build()
```

## 密钥管理

### Android Keystore
```kotlin
// 使用 EncryptedSharedPreferences（Jetpack Security）
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build()

val securePrefs = EncryptedSharedPreferences.create(
    context,
    "secure_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)
```

### 禁止
- **永不**硬编码 API Key、Token、密码
- **永不**使用 `SharedPreferences` 存储敏感数据
- **永不**在日志中输出敏感信息

```kotlin
// 错误
val apiKey = "sk_live_12345..."

// 正确 — 从 BuildConfig 或安全存储获取
val apiKey = BuildConfig.API_KEY
// 或
val apiKey = securePrefs.getString("api_key", null)
    ?: throw IllegalStateException("API key not configured")
```

## 输入验证

```kotlin
// 验证用户输入
fun validateEmail(email: String): Result<String> {
    if (email.isBlank()) return Result.failure(IllegalArgumentException("Email required"))
    if (!Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
        return Result.failure(IllegalArgumentException("Invalid email"))
    }
    return Result.success(email.trim().lowercase())
}

// WebView 安全
webView.settings.apply {
    javaScriptEnabled = false  // 除非必需
    allowFileAccess = false
    allowContentAccess = false
}
```

## 数据安全

### Room 数据库加密
```kotlin
// 使用 SQLCipher
val passphrase = SQLiteDatabase.getBytes("your-passphrase".toCharArray())
val factory = SupportFactory(passphrase)

Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
    .openHelperFactory(factory)
    .build()
```

### ProGuard / R8
```proguard
# 混淆敏感类
-keep class com.yourapp.data.model.** { *; }
-dontwarn okhttp3.**
```

## 权限最小化

```kotlin
// 只请求必需权限
// AndroidManifest.xml
// <uses-permission android:name="android.permission.INTERNET" />
// 不要请求不需要的权限

// 运行时权限
val requestPermission = rememberLauncherForActivityResult(
    ActivityResultContracts.RequestPermission()
) { granted ->
    if (granted) { /* proceed */ }
    else { /* explain why needed */ }
}
```

## 依赖安全

```kotlin
// build.gradle.kts
plugins {
    id("com.google.android.gms.oss-licenses-plugin")
}

// 定期运行
// ./gradlew dependencyUpdates    # 检查过期依赖
// ./gradlew lint                 # 安全 lint 检查
```

## 一人公司 Android 安全清单

- [ ] Network Security Config 禁止明文流量
- [ ] EncryptedSharedPreferences 存储敏感数据
- [ ] BuildConfig 管理 API Key（不硬编码）
- [ ] ProGuard/R8 启用代码混淆
- [ ] 权限最小化
- [ ] WebView JavaScript 默认关闭
- [ ] 依赖定期审计
