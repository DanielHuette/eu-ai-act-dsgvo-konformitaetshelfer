package de.konformitaetshelfer.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/**
 * Der Startbildschirm.
 *
 * Zwei Wege hinein: eigene Worte oder gleich der Fragebogen. Der Freitext
 * steht vorn, weil niemand mit 25 Fragen anfangen will - er entscheidet, WELCHE
 * Fragen überhaupt gestellt werden. Eingestuft wird er nie; dazu siehe
 * Pruefer.deutetDarauf.
 */
@Composable
fun ColumnScope.Startbildschirm(modell: Helfermodell) {
    Kopfzeile(
        titel = "EU-KI-Verordnung und Datenschutz",
        unterzeile = if (modell.geladen) {
            "${modell.einheiten} Rechtseinheiten auf dem Gerät, Stand ${modell.datenstand}"
        } else {
            "wird geöffnet"
        },
        rechts = {
            TextButton(onClick = { modell.zu(Bildschirm.EINSTELLUNGEN) }) {
                Text("Mehr", color = MaterialTheme.colorScheme.onPrimary)
            }
        },
    )

    if (!modell.geladen) {
        Ladehinweis(Modifier.weight(1f))
        return
    }

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .weight(1f)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 16.dp),
    ) {
        Spacer(Modifier.height(20.dp))
        Text(
            "Was macht Ihr KI-System?",
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onBackground,
        )
        Spacer(Modifier.height(6.dp))
        Text(
            "Beschreiben Sie es in eigenen Worten: wer es einsetzt, worüber es " +
                "entscheidet oder was es erzeugt. Daraus ergibt sich, welche Fragen " +
                "zu klären sind. Die Einstufung selbst entsteht erst aus Ihren " +
                "Antworten, nicht aus diesem Text.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(14.dp))
        OutlinedTextField(
            value = modell.beschreibung,
            onValueChange = { modell.beschreibungSetzen(it) },
            modifier = Modifier.fillMaxWidth().height(170.dp),
            placeholder = {
                Text(
                    "Zum Beispiel: Wir lassen ein Sprachmodell eingehende " +
                        "Bewerbungen lesen und auf einer Skala einordnen, wie gut " +
                        "sie zur Stelle passen.",
                    style = MaterialTheme.typography.bodySmall,
                )
            },
            label = { Text("Beschreibung") },
        )

        Spacer(Modifier.height(16.dp))
        Button(
            onClick = { modell.zu(Bildschirm.FRAGEBOGEN) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Fragen beantworten und einordnen")
        }

        Spacer(Modifier.height(24.dp))
        Abschnittstitel("Auch ohne eigenen Fall")
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedButton(
                onClick = { modell.zu(Bildschirm.FAELLE) },
                modifier = Modifier.weight(1f),
            ) {
                Text("44 Beispiele")
            }
            OutlinedButton(
                onClick = { modell.zu(Bildschirm.DATENSCHUTZ) },
                modifier = Modifier.weight(1f),
            ) {
                Text("Datenschutz")
            }
        }

        Spacer(Modifier.height(26.dp))
        Vorbehaltstreifen(
            "Keine Rechtsberatung. Dieses Werkzeug ordnet ein KI-System anhand des " +
                "Verordnungstextes ein und nennt die Fundstellen im Wortlaut. Es " +
                "ersetzt keine Prüfung durch einen Rechtsanwalt oder die zuständige " +
                "Behörde. Regelstand ${modell.regelstand}, Datenstand " +
                "${modell.datenstand}."
        )
        Spacer(Modifier.height(10.dp))
        Text(
            "Alles rechnet auf diesem Gerät. Ohne eingetragenen Schlüssel geht " +
                "nichts ins Netz.",
            style = MaterialTheme.typography.bodySmall,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.secondary,
            modifier = Modifier.padding(bottom = 24.dp),
        )
    }
}
