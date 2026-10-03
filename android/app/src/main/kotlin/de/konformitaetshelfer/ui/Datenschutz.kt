package de.konformitaetshelfer.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import de.konformitaetshelfer.daten.Pruefabschnitt

/**
 * Der Prüfpfad der Datenschutz-Grundverordnung.
 *
 * 26 Abschnitte in der Reihenfolge, in der sie zu prüfen sind. Sie bauen
 * aufeinander auf: wer den Personenbezug verneint, ist nach dem ersten
 * Abschnitt fertig - muss das aber begründen können.
 *
 * Kein zweiter Fragebogen: Datenschutz ist kein Ja-Nein-Baum mit einem
 * Ergebnis am Ende, sondern eine Prüfliste, die man abarbeitet und belegt.
 * Ein Ergebnis zu behaupten, wo die Verordnung eine Abwägung verlangt, wäre
 * falsche Sicherheit.
 */
@Composable
fun ColumnScope.Pruefpfad(modell: Helfermodell) {
    Kopfzeile(
        titel = "Datenschutz prüfen",
        unterzeile = "${modell.pruefabschnitte.size} Abschnitte, in dieser Reihenfolge",
        zurueck = { modell.zu(Bildschirm.START) },
    )

    if (!modell.geladen) {
        Ladehinweis(Modifier.weight(1f))
        return
    }

    LazyColumn(modifier = Modifier.fillMaxWidth().weight(1f).padding(horizontal = 16.dp)) {
        item {
            Spacer(Modifier.height(16.dp))
            Vorbehaltstreifen(
                "Diese Liste führt durch die Prüfung und nennt zu jedem Schritt die " +
                    "Fundstelle und den Nachweis, den Sie führen müssen. Sie trifft " +
                    "keine Entscheidung für Sie - mehrere Schritte verlangen eine " +
                    "Abwägung, die nur Sie für Ihren Fall treffen können."
            )
        }
        items(modell.pruefabschnitte, key = { it.kennung }) { abschnitt ->
            Abschnittskarte(abschnitt)
        }
        item { Spacer(Modifier.height(28.dp)) }
    }
}

@Composable
private fun Abschnittskarte(abschnitt: Pruefabschnitt) {
    var offen by remember { mutableStateOf(false) }
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                "${abschnitt.rang}. ${abschnitt.titel}",
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                abschnitt.fundstellenText,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
            )
            Spacer(Modifier.height(8.dp))
            Text(abschnitt.frage.trim(), style = MaterialTheme.typography.bodyLarge)
            AnimatedVisibility(visible = offen) {
                Column {
                    Spacer(Modifier.height(10.dp))
                    Text(
                        abschnitt.wasZuTunIst.trim(),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                    if (abschnitt.nachweis.isNotBlank()) {
                        Spacer(Modifier.height(10.dp))
                        Text(
                            "Womit Sie es belegen",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(abschnitt.nachweis, style = MaterialTheme.typography.bodySmall)
                    }
                    if (abschnitt.beiVerstoss.isNotBlank()) {
                        Spacer(Modifier.height(8.dp))
                        Text(
                            "Was bei einem Verstoß droht",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(
                            abschnitt.beiVerstoss,
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }
            TextButton(onClick = { offen = !offen }) {
                Text(if (offen) "weniger" else "Was zu tun ist")
            }
        }
    }
}
