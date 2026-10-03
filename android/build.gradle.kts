// Wurzelbau. Hier stehen nur die Fassungen der Zusatzprogramme; gebaut wird
// im Modul app. Die Fassungen sind festgenagelt und nicht mit "+" offen
// gelassen: ein Bau, der sich morgen von allein ändert, ist kein Nachweis.
//
// Die Zusammenstellung ist nachgemessen, nicht geschätzt. Jede Abhängigkeit
// trägt in ihrer Beschreibung, welche Bauwerkzeug-Fassung und welche
// Bau-Schnittstellenstufe sie mindestens braucht. Geprüft am 2026-10-03:
//   Bauwerkzeug 8.13.2 mit Gradle 8.14.3, Bau gegen Schnittstellenstufe 36.
// Neuere androidx-Fassungen (core-ktx 1.19, lifecycle 2.11) verlangen
// Bauwerkzeug 9.1 und Stufe 37 - die bleiben deshalb bewusst draußen.

plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.kotlin.serialization) apply false
}
