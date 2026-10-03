package de.konformitaetshelfer.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.konformitaetshelfer.daten.Risikoklasse

/** Die Kopfzeile. Eigenhändig gebaut, damit kein vorläufiger Baustein nötig ist. */
@Composable
fun Kopfzeile(
    titel: String,
    unterzeile: String = "",
    zurueck: (() -> Unit)? = null,
    rechts: @Composable () -> Unit = {},
) {
    Surface(color = MaterialTheme.colorScheme.primary, tonalElevation = 0.dp) {
        Row(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            if (zurueck != null) {
                TextButton(onClick = zurueck) {
                    Text("Zurück", color = MaterialTheme.colorScheme.onPrimary)
                }
            } else {
                Spacer(Modifier.width(12.dp))
            }
            Column(modifier = Modifier.weight(1f).padding(horizontal = 4.dp)) {
                Text(
                    titel,
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onPrimary,
                )
                if (unterzeile.isNotBlank()) {
                    Text(
                        unterzeile,
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.78f),
                    )
                }
            }
            rechts()
        }
    }
}

/** Eine Überschrift über einem Abschnitt. */
@Composable
fun Abschnittstitel(text: String, modifier: Modifier = Modifier) {
    Text(
        text.uppercase(),
        style = MaterialTheme.typography.labelSmall,
        fontWeight = FontWeight.SemiBold,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = modifier.padding(top = 20.dp, bottom = 6.dp),
    )
}

/**
 * Das Schild mit der Risikoklasse.
 *
 * Die Farbe ist hier die Aussage: Rot heißt verboten, nicht "Achtung". Eine
 * Einstufung, die man übersehen kann, ist keine Auskunft.
 */
@Composable
fun Klassenschild(klasse: Risikoklasse, modifier: Modifier = Modifier) {
    val (grund, schrift) = when (klasse) {
        Risikoklasse.VERBOTEN ->
            MaterialTheme.colorScheme.error to MaterialTheme.colorScheme.onError
        Risikoklasse.HOCHRISIKO_ANHANG_I,
        Risikoklasse.HOCHRISIKO_ANHANG_III,
        Risikoklasse.GPAI_SYSTEMISCH ->
            Color(0xFFB45309) to Color.White
        Risikoklasse.HOCHRISIKO_AUSNAHME, Risikoklasse.TRANSPARENZ, Risikoklasse.GPAI ->
            MaterialTheme.colorScheme.primaryContainer to
                MaterialTheme.colorScheme.onPrimaryContainer
        Risikoklasse.MINIMAL ->
            MaterialTheme.colorScheme.surfaceVariant to
                MaterialTheme.colorScheme.onSurfaceVariant
    }
    Surface(
        color = grund,
        shape = RoundedCornerShape(6.dp),
        modifier = modifier,
    ) {
        Text(
            klasse.anzeige,
            color = schrift,
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
        )
    }
}

/**
 * Der Wortlaut einer Belegstelle.
 *
 * Ungekürzt, in Serifenschrift, am linken Rand gekennzeichnet. Wer eine
 * Auskunft prüfen will, muss den Satz lesen können, auf den sie sich stützt -
 * eine Zusammenfassung wäre hier das Gegenteil von Hilfe.
 */
@Composable
fun Wortlautfeld(fundstelle: String, titel: String, text: String) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        // IntrinsicSize.Min lässt die Zeile so hoch werden wie ihr Inhalt;
        // erst dadurch kann der Randstreifen daneben auf volle Höhe gehen.
        Row(modifier = Modifier.fillMaxWidth().height(IntrinsicSize.Min)) {
            Surface(
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.width(4.dp).fillMaxHeight(),
            ) {}
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    fundstelle,
                    style = MaterialTheme.typography.labelLarge,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.primary,
                )
                if (titel.isNotBlank()) {
                    Text(
                        titel,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                Spacer(Modifier.height(8.dp))
                Text(text, style = WORTLAUT, color = MaterialTheme.colorScheme.onSurface)
            }
        }
    }
}

/** Streifen für den Vorbehalt - immer sichtbar, nie bunt. */
@Composable
fun Vorbehaltstreifen(text: String, modifier: Modifier = Modifier) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
            .border(
                1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(8.dp),
            )
            .padding(12.dp),
        horizontalArrangement = Arrangement.Start,
    ) {
        Text(
            text,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
