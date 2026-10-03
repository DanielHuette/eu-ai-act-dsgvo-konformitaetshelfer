// Bau der App.
//
// ROOM ODER SQLITE - die Entscheidung und warum
// =============================================
// Gewählt ist androidx.sqlite mit mitgeliefertem SQLite und handgeschriebenem
// SQL. KEIN Room. Die Gründe, in der Reihenfolge ihres Gewichts:
//
// 1. Die Datenbank ist fertig und wird nur gelesen. Sie entsteht beim Bauen
//    aus scripts/export_android.py. Room ist dafür gemacht, ein Schema zu
//    führen, zu wandern und mitzuwachsen - Arbeit, die hier niemand braucht,
//    weil eine neue Rechtslage eine neue Datei bringt und keine Wanderung.
// 2. Die beiden Abfragen, auf die es ankommt, kann Room nicht abbilden:
//    die Stichwortsuche braucht FTS5 mit MATCH und bm25(), die Vektorsuche
//    liest 1972 Zahlenblöcke in einem Zug. Für FTS5 hat Room keine
//    Entsprechung - es kennt nur FTS3 und FTS4. Beides müsste als rohe
//    Abfrage an Room vorbei laufen; dann trägt Room nichts mehr bei.
// 3. Das mitgelieferte SQLite ist nachgemessen das einzige, auf das man sich
//    verlassen kann: in sqlite-bundled-android 2.7.1 sind FTS5, unicode61
//    und remove_diacritics=2 eingebaut (geprüft am 2026-10-03 an der
//    Bibliothek selbst). Das SQLite des Telefons hat FTS5 je nach
//    Android-Fassung nicht - die Stichwortsuche fiele dann still aus.
// 4. Weniger Teile: kein Symbolverarbeiter (KSP), kein erzeugter Quelltext,
//    kürzere Bauzeit, und was die App tut, steht lesbar im SQL.

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "de.konformitaetshelfer"
    compileSdk = 36

    defaultConfig {
        applicationId = "de.konformitaetshelfer"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"

        // Nur die beiden Bauarten, die in echten Telefonen stecken. x86 und
        // x86_64 brauchen nur Emulatoren und würden das Paket um die Größe
        // der ONNX-Laufzeit zweimal aufblähen.
        ndk {
            abiFilters += listOf("arm64-v8a", "armeabi-v7a")
        }
    }

    buildTypes {
        release {
            // Der Quelltext wird verkleinert, die Beigaben nicht - an einer
            // Modelldatei und einer Datenbank gibt es nichts zu kürzen.
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
            // Der Ausgabestand wird nicht unterschrieben. Wer das Paket aus
            // dem Netz lädt, erlaubt die Installation aus unbekannter Quelle;
            // siehe die Anleitung in .github/workflows/android.yml.
            signingConfig = null
        }
        debug {
            // Die Fehlersuchfassung trägt einen eigenen Namen, damit sie
            // nicht versehentlich die ernste Fassung überschreibt.
            applicationIdSuffix = ".pruefung"
        }
    }

    androidResources {
        // Beigaben unkomprimiert ablegen. Zwei Gründe: die 118 MB große
        // Modelldatei wird so beim Bauen nicht sinnlos durch die Kompression
        // geschoben, und die App kann sie zur Laufzeit direkt aus dem Paket
        // in den Speicher einblenden, statt sie erst zu entpacken.
        noCompress.addAll(listOf("onnx", "db", "json"))
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_21
        targetCompatibility = JavaVersion.VERSION_21
    }

    kotlin {
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21)
        }
    }

    buildFeatures {
        compose = true
        // Kein BuildConfig-Feld nötig; was die App über ihren Datenstand
        // wissen muss, steht in der Tabelle meta der Datenbank. Ein zweiter
        // Ort für dieselbe Angabe wäre ein zweiter Ort, der veraltet.
        buildConfig = true
    }

    sourceSets {
        getByName("main") {
            kotlin.srcDirs("src/main/kotlin")
        }
        getByName("test") {
            kotlin.srcDirs("src/test/kotlin")
        }
    }

    packaging {
        resources {
            excludes += setOf(
                "/META-INF/{AL2.0,LGPL2.1}",
                "/META-INF/DEPENDENCIES",
                "/META-INF/INDEX.LIST",
            )
        }
    }

    testOptions {
        unitTests {
            isIncludeAndroidResources = false
        }
    }
}

dependencies {
    implementation(libs.kern.ktx)
    implementation(libs.tatigkeit.compose)
    implementation(libs.lebenslauf.ansichtsmodell)

    implementation(platform(libs.compose.sammlung))
    implementation(libs.compose.ui)
    implementation(libs.compose.grafik)
    implementation(libs.compose.werkzeug)
    implementation(libs.compose.material3)
    debugImplementation(libs.compose.werkzeug.fehlersuche)

    implementation(libs.sqlite)
    implementation(libs.sqlite.mitgeliefert)

    implementation(libs.onnx.laufzeit)
    implementation(libs.schluesselspeicher)
    implementation(libs.serialisierung.json)
    implementation(libs.okhttp)
    implementation(libs.nebenlaeufig)

    testImplementation(libs.junit)
    testImplementation(libs.nebenlaeufig.pruefung)
}
