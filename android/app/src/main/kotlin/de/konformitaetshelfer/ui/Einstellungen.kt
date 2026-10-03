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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import de.konformitaetshelfer.modell.Anbieter

/**
 * Einstellungen und Herkunft.
 *
 * Hier wird der Anbieterschlüssel eingetragen. Er wird nach dem Eintragen
 * NICHT mehr angezeigt - weder im Klartext noch verkürzt. Was zu sehen ist,
 * ist nur, DASS einer hinterlegt ist. Ein Schlüssel, der auf dem Bildschirm
 * steht, steht auch auf einem Bildschirmfoto.
 */
@Composable
fun ColumnScope.Einstellungen(modell: Helfermodell) {
    Kopfzeile(
        titel = "Einstellungen",
        unterzeile = "Datenstand und Ausformulierung",
        zurueck = { modell.zu(Bildschirm.START) },
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
        Abschnittstitel("Was auf diesem Gerät liegt")
        Text(
            "${modell.einheiten} Rechtseinheiten aus KI-Verordnung, " +
                "Datenschutz-Grundverordnung und Bundesdatenschutzgesetz, dazu " +
                "${modell.faelle.size} ausgearbeitete Anwendungsfälle und " +
                "${modell.pruefabschnitte.size} Abschnitte des Datenschutz-Prüfpfads.",
            style = MaterialTheme.typography.bodyMedium,
        )
        Spacer(Modifier.height(8.dp))
        Text(
            "Datenstand ${modell.datenstand}, Regelstand ${modell.regelstand}.",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
        )

        Abschnittstitel("Ausformulieren mit einem Sprachmodell")
        Text(
            "Ohne Schlüssel läuft alles: Einstufung, Pflichtenliste, Suche und " +
                "Belegstellen rechnen auf diesem Gerät und ohne Netz. Wer einen " +
                "eigenen Schlüssel einträgt, bekommt die Auskunft zusätzlich als " +
                "zusammenhängenden Text.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(6.dp))
        Text(
            "Die Einstufung selbst kommt immer aus dem Regelwerk. Das Modell " +
                "formuliert nur und darf das Ergebnis nicht verändern.",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium,
            color = MaterialTheme.colorScheme.secondary,
        )
        Spacer(Modifier.height(6.dp))
        Text(
            "Beim Ausformulieren gehen Ihre Beschreibung und die gefundenen " +
                "Belegstellen an den gewählten Anbieter. Nur dann, nur dafür.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(Modifier.height(14.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            for (anbieter in Anbieter.entries) {
                Wahlknopf(
                    text = anbieter.anzeige,
                    gewaehlt = modell.anbieter() == anbieter,
                    modifier = Modifier.weight(1f),
                ) {
                    modell.anbieterSetzen(
                        if (modell.anbieter() == anbieter) null else anbieter
                    )
                }
            }
        }

        modell.anbieter()?.let { anbieter ->
            Spacer(Modifier.height(14.dp))
            Schluesselfeld(modell, anbieter)
        }

        Abschnittstitel("Woher die Daten kommen")
        Text(
            "Der Wortlaut der KI-Verordnung stammt aus dem Amtsblatt der " +
                "Europäischen Union, der des Bundesdatenschutzgesetzes von " +
                "gesetze-im-internet.de. Jede Belegstelle nennt ihre Herkunft. " +
                "Das Einstufungsregelwerk und die Pflichtenliste sind aus dem " +
                "Verordnungstext gebaut und als Textdateien nachlesbar.",
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(Modifier.height(20.dp))
        Vorbehaltstreifen(
            "Keine Rechtsberatung. Dieses Werkzeug ordnet ein KI-System anhand des " +
                "Verordnungstextes ein und nennt die Fundstellen. Es ersetzt keine " +
                "Prüfung durch einen Rechtsanwalt oder die zuständige Behörde. " +
                "Einzelne Geltungstermine wurden zum Datenstand politisch erörtert; " +
                "vor einer Entscheidung mit Geld- oder Rechtsfolgen ist der geltende " +
                "Stand bei der zuständigen Behörde zu prüfen."
        )
        Spacer(Modifier.height(28.dp))
    }
}

/** Das Eingabefeld für den Schlüssel. */
@Composable
private fun Schluesselfeld(modell: Helfermodell, anbieter: Anbieter) {
    var eingabe by remember(anbieter) { mutableStateOf("") }
    val hinterlegt = modell.hatSchluessel(anbieter)

    if (hinterlegt) {
        Text(
            "Für ${anbieter.anzeige} ist ein Schlüssel hinterlegt. Er liegt " +
                "verschlüsselt im Schlüsselspeicher dieses Geräts und wird nicht " +
                "angezeigt, nicht protokolliert und nicht gesichert.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.secondary,
        )
        Spacer(Modifier.height(8.dp))
        OutlinedButton(onClick = { modell.schluesselSetzen(anbieter, "") }) {
            Text("Schlüssel entfernen")
        }
    } else {
        OutlinedTextField(
            value = eingabe,
            onValueChange = { eingabe = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Schlüssel für ${anbieter.anzeige}") },
            singleLine = true,
            // Der Schlüssel wird schon bei der Eingabe verdeckt, und die
            // Tastatur merkt sich nichts davon.
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                autoCorrectEnabled = false,
                imeAction = ImeAction.Done,
            ),
        )
        Spacer(Modifier.height(8.dp))
        Button(
            onClick = {
                modell.schluesselSetzen(anbieter, eingabe)
                eingabe = ""
            },
            enabled = eingabe.isNotBlank(),
        ) {
            Text("Eintragen")
        }
    }
}
