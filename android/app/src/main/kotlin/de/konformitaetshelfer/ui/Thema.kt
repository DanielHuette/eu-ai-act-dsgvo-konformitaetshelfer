package de.konformitaetshelfer.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * Das Aussehen.
 *
 * Die Haltung dahinter: das Werkzeug gibt Rechtsauskunft, also soll es wie ein
 * Schriftstück aussehen und nicht wie eine Werbefläche. Warmes Papierweiß statt
 * reinem Weiß, ein dunkles Blau für Überschriften, und Farbe nur dort, wo sie
 * etwas BEDEUTET - bei der Risikoklasse. Wenn Farbe überall ist, sagt sie nichts.
 *
 * Der Wortlaut der Gesetze steht in einer Schrift mit Serifen und mit mehr
 * Zeilenabstand als der übrige Text. Das trennt Zitat von Erklärung auf den
 * ersten Blick - wichtiger als jede Einrahmung, weil man es auch beim
 * Überfliegen sieht.
 */

private val Tiefblau = Color(0xFF1F3A5F)
private val Tiefblau_hell = Color(0xFF9FC0E8)
private val Papier = Color(0xFFFBF8F4)
private val Papier_dunkel = Color(0xFF14181D)
private val Tinte = Color(0xFF1A1C1E)
private val Tinte_hell = Color(0xFFE6E2DC)
private val Siegelrot = Color(0xFF8E2A2A)
private val Siegelrot_hell = Color(0xFFFFB4AA)
private val Pruefgruen = Color(0xFF2E7D5B)
private val Karte = Color(0xFFFFFFFF)
private val Karte_dunkel = Color(0xFF1D2227)

private val Hell = lightColorScheme(
    primary = Tiefblau,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFDCE7F5),
    onPrimaryContainer = Tiefblau,
    secondary = Pruefgruen,
    onSecondary = Color.White,
    error = Siegelrot,
    onError = Color.White,
    errorContainer = Color(0xFFF7DDDA),
    onErrorContainer = Color(0xFF5C1212),
    background = Papier,
    onBackground = Tinte,
    surface = Karte,
    onSurface = Tinte,
    surfaceVariant = Color(0xFFEFEAE2),
    onSurfaceVariant = Color(0xFF45474A),
    outline = Color(0xFF8E9094),
    outlineVariant = Color(0xFFD9D4CC),
)

private val Dunkel = darkColorScheme(
    primary = Tiefblau_hell,
    onPrimary = Color(0xFF0A2440),
    primaryContainer = Color(0xFF24405F),
    onPrimaryContainer = Color(0xFFD6E3F7),
    secondary = Color(0xFF8CD6B4),
    onSecondary = Color(0xFF003824),
    error = Siegelrot_hell,
    onError = Color(0xFF5C1212),
    errorContainer = Color(0xFF6E2320),
    onErrorContainer = Color(0xFFFFDAD5),
    background = Papier_dunkel,
    onBackground = Tinte_hell,
    surface = Karte_dunkel,
    onSurface = Tinte_hell,
    surfaceVariant = Color(0xFF2A3036),
    onSurfaceVariant = Color(0xFFC4C7CA),
    outline = Color(0xFF8E9094),
    outlineVariant = Color(0xFF3A4046),
)

/** Die Schrift für den Wortlaut der Rechtstexte. */
val WORTLAUT = TextStyle(
    fontFamily = FontFamily.Serif,
    fontSize = 15.sp,
    lineHeight = 25.sp,
)

private val Schriftbild = Typography().let { grund ->
    grund.copy(
        headlineSmall = grund.headlineSmall.copy(
            fontWeight = FontWeight.SemiBold,
            letterSpacing = (-0.2).sp,
        ),
        titleMedium = grund.titleMedium.copy(fontWeight = FontWeight.SemiBold),
        bodyLarge = grund.bodyLarge.copy(lineHeight = 24.sp),
        bodyMedium = grund.bodyMedium.copy(lineHeight = 21.sp),
        labelSmall = grund.labelSmall.copy(letterSpacing = 0.6.sp),
    )
}

@Composable
fun Thema(inhalt: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) Dunkel else Hell,
        typography = Schriftbild,
        content = inhalt,
    )
}
