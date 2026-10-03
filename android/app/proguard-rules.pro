# Was beim Verkleinern stehen bleiben muss.

# Die ONNX-Laufzeit ruft ihre Java-Klassen von der nativen Seite über ihre
# Namen auf. Wer sie umbenennt, bekommt beim ersten Einbetten einen Absturz,
# den kein Test vorher zeigt.
-keep class ai.onnxruntime.** { *; }
-dontwarn ai.onnxruntime.**

# Gleiches gilt für das mitgelieferte SQLite.
-keep class androidx.sqlite.driver.bundled.** { *; }

# Tink, die Verschlüsselung hinter dem Schlüsselspeicher, sucht ihre
# Bausteine zur Laufzeit.
-keep class com.google.crypto.tink.** { *; }
-dontwarn com.google.crypto.tink.**
-dontwarn javax.annotation.**
-dontwarn com.google.errorprone.annotations.**

# kotlinx.serialization erzeugt Hilfsklassen, die über Namen gefunden werden.
-keepclassmembers class kotlinx.serialization.json.** { *** Companion; }
-keepclasseswithmembers class kotlinx.serialization.json.** { kotlinx.serialization.KSerializer serializer(...); }
-keep,includedescriptorclasses class de.konformitaetshelfer.**$$serializer { *; }
-keepclassmembers class de.konformitaetshelfer.** { *** Companion; }

# OkHttp spricht über optionale Teile von Conscrypt und Co., die hier fehlen.
-dontwarn okhttp3.internal.platform.**
-dontwarn org.conscrypt.**
-dontwarn org.bouncycastle.**
-dontwarn org.openjsse.**

# Kein Protokoll in der ernsten Fassung. android.util.Log wird zusätzlich
# weggelassen - eine Rechtsauskunft samt Systembeschreibung des Nutzers hat
# im Systemprotokoll nichts zu suchen.
-assumenosideeffects class android.util.Log {
    public static *** v(...);
    public static *** d(...);
    public static *** i(...);
    public static *** w(...);
    public static *** e(...);
}
