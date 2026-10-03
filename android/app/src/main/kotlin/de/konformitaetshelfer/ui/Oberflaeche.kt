package de.konformitaetshelfer.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

/**
 * Die Oberfläche.
 *
 * Gewechselt wird über einen einfachen Zustand und nicht über eine
 * Wegeverwaltung: es gibt sechs Bildschirme und keine tiefen Verzweigungen.
 * Eine zusätzliche Bibliothek dafür wäre mehr Gewicht als Nutzen.
 */
@Composable
fun Oberflaeche() {
    val modell: Helfermodell = viewModel()

    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background,
    ) {
        Column(modifier = Modifier.fillMaxSize().windowInsetsPadding(WindowInsets.safeDrawing)) {
            when (modell.bildschirm) {
                Bildschirm.START -> Startbildschirm(modell)
                Bildschirm.FRAGEBOGEN -> Fragebogen(modell)
                Bildschirm.ERGEBNIS -> Ergebnisbildschirm(modell)
                Bildschirm.FAELLE -> Fallsammlung(modell)
                Bildschirm.DATENSCHUTZ -> Pruefpfad(modell)
                Bildschirm.EINSTELLUNGEN -> Einstellungen(modell)
            }
        }
    }
}

/** Der Hinweis, solange Datenbank und Modell geöffnet werden. */
@Composable
fun Ladehinweis(
    modifier: Modifier = Modifier,
    text: String = "Rechtsbestand wird geöffnet",
) {
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator()
            Text(
                text,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 16.dp),
            )
        }
    }
}

/** Fußzeile mit dem Weg zurück zum Anfang. */
@Composable
fun Neuanfang(modell: Helfermodell) {
    TextButton(onClick = { modell.neuAnfangen() }) {
        Text("Neue Anfrage")
    }
}
