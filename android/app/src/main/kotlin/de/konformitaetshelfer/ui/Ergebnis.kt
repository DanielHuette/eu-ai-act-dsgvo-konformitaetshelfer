package de.konformitaetshelfer.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.konformitaetshelfer.daten.Fall
import de.konformitaetshelfer.daten.Pflicht

/**
 * Die Auskunft.
 *
 * Reihenfolge nach dem, was den Nutzer zuerst angeht: Einstufung, dann warum,
 * dann was zu tun ist, dann der Wortlaut zum Nachlesen, dann ein ähnlicher
 * Fall. Der ausformulierte Text steht NICHT oben - er ist eine Zugabe, nicht
 * die Auskunft.
 */
@Composable
fun ColumnScope.Ergebnisbildschirm(modell: Helfermodell) {
    val einstufung = modell.einstufung
    Kopfzeile(
        titel = "Auskunft",
        unterzeile = "Regelstand ${modell.regelstand}, Daten ${modell.datenstand}",
        zurueck = { modell.zu(Bildschirm.FRAGEBOGEN) },
        rechts = { Neuanfang(modell) },
    )

    if (einstufung == null) {
        Ladehinweis(Modifier.weight(1f), "Es liegt noch keine Auskunft vor")
        return
    }

    LazyColumn(modifier = Modifier.fillMaxWidth().weight(1f).padding(horizontal = 16.dp)) {
        item {
            Spacer(Modifier.height(18.dp))
            Klassenschild(einstufung.klasse)
            if (einstufung.weitereKlassen.isNotEmpty()) {
                Spacer(Modifier.height(8.dp))
                Text(
                    "Zusätzlich: " +
                        einstufung.weitereKlassen.joinToString(", ") { it.anzeige },
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Spacer(Modifier.height(10.dp))
            Text(
                "Ihre Rolle: " +
                    einstufung.rollen.joinToString(", ") { it.anzeige }
                        .ifBlank { "noch offen" },
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
            )
        }

        // Warum. Jede Begründung nennt ihre Fundstelle und wie sicher sie ist.
        item { Abschnittstitel("Warum") }
        items(einstufung.hinweise, key = { it.regel }) { hinweis ->
            Column(modifier = Modifier.padding(vertical = 6.dp)) {
                Text(
                    hinweis.fundstelle,
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(hinweis.begruendung.trim(), style = MaterialTheme.typography.bodyMedium)
                Text(
                    when (hinweis.sicherheit) {
                        "sicher" -> "Diese Einordnung ergibt sich unmittelbar aus dem Text."
                        "zu_pruefen" -> "Diese Einordnung hängt an der Beurteilung des " +
                            "Einzelfalls und ist zu prüfen."
                        else -> "Diese Einordnung ist wahrscheinlich, aber vom " +
                            "Einzelfall abhängig."
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        if (einstufung.rollenwechselHinweis.isNotBlank()) {
            item {
                Spacer(Modifier.height(8.dp))
                Vorbehaltstreifen(einstufung.rollenwechselHinweis)
            }
        }

        // Offene Punkte stehen VOR der Pflichtenliste: wer sie nicht klärt,
        // liest eine Liste, die sich noch ändern kann.
        if (einstufung.offeneFragen.isNotEmpty()) {
            item { Abschnittstitel("Noch offen") }
            items(einstufung.offeneFragen, key = { it.feld }) { offen ->
                Column(modifier = Modifier.padding(vertical = 6.dp)) {
                    Text(offen.frage.trim(), style = MaterialTheme.typography.bodyMedium)
                    Text(
                        offen.folgeBeiJa,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            item {
                TextButton(onClick = { modell.zu(Bildschirm.FRAGEBOGEN) }) {
                    Text("Offene Fragen beantworten")
                }
            }
        }

        item {
            Abschnittstitel("Was zu tun ist (${einstufung.pflichten.size})")
        }
        items(einstufung.pflichten, key = { it.kennung }) { pflicht ->
            Pflichtkarte(pflicht)
        }

        item { Abschnittstitel("Belegstellen im Wortlaut") }
        items(modell.belege, key = { it.einheit.kennung }) { treffer ->
            Wortlautfeld(
                fundstelle = treffer.einheit.fundstelle,
                titel = treffer.einheit.titel,
                text = treffer.einheit.text,
            )
        }

        modell.passenderFall?.let { fall ->
            item {
                Abschnittstitel("Ein ähnlicher Fall")
                Fallkarte(fall)
            }
        }

        // Die Zugabe zum Schluss. Ohne Schlüssel steht hier nur, was sie wäre.
        item {
            Abschnittstitel("Ausformuliert")
            if (modell.schluesselEingetragen()) {
                if (modell.ausformuliert.isBlank()) {
                    Button(
                        onClick = { modell.ausformulieren() },
                        enabled = !modell.rechnet,
                    ) {
                        Text(if (modell.rechnet) "wird geschrieben" else "Ausformulieren")
                    }
                } else {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer,
                        ),
                        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
                    ) {
                        Text(
                            modell.ausformuliert,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer,
                            modifier = Modifier.padding(14.dp),
                        )
                    }
                }
            } else {
                Text(
                    "Wer einen eigenen Schlüssel für Claude oder GPT einträgt, " +
                        "bekommt diese Auskunft zusätzlich als zusammenhängenden Text. " +
                        "Die Einstufung bleibt dieselbe - sie kommt aus dem " +
                        "Regelwerk, nicht aus dem Modell.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                TextButton(onClick = { modell.zu(Bildschirm.EINSTELLUNGEN) }) {
                    Text("Schlüssel eintragen")
                }
            }
            if (modell.meldung.isNotBlank()) {
                Text(
                    modell.meldung,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.error,
                )
            }
        }

        item {
            Spacer(Modifier.height(20.dp))
            Vorbehaltstreifen(
                "Keine Rechtsberatung. Die Einstufung folgt dem Verordnungstext mit " +
                    "Regelstand ${modell.regelstand}. Zu den Fristen: einzelne " +
                    "Geltungstermine wurden zum Datenstand politisch erörtert. Vor " +
                    "einer Entscheidung mit Geld- oder Rechtsfolgen ist der geltende " +
                    "Stand bei der zuständigen Behörde zu prüfen."
            )
            Spacer(Modifier.height(28.dp))
        }
    }
}

/** Eine Pflicht - zusammengeklappt der Satz, aufgeklappt Nachweis und Folgen. */
@Composable
private fun Pflichtkarte(pflicht: Pflicht) {
    var offen by remember { mutableStateOf(false) }
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                pflicht.titel,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    pflicht.fundstellenText,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                )
                if (pflicht.giltAb != null) {
                    Text(
                        "gilt ab ${pflicht.giltAb}",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Text(pflicht.wasZuTunIst.trim(), style = MaterialTheme.typography.bodyMedium)
            AnimatedVisibility(visible = offen) {
                Column {
                    if (pflicht.nachweis.isNotBlank()) {
                        Spacer(Modifier.height(10.dp))
                        Text(
                            "Womit Sie es belegen",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(pflicht.nachweis, style = MaterialTheme.typography.bodySmall)
                    }
                    if (pflicht.beiVerstoss.isNotBlank()) {
                        Spacer(Modifier.height(8.dp))
                        Text(
                            "Was bei einem Verstoß droht",
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                        Text(pflicht.beiVerstoss, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
            TextButton(onClick = { offen = !offen }) {
                Text(if (offen) "weniger" else "Nachweis und Folgen")
            }
        }
    }
}

/** Ein Anwendungsfall mit Lernhinweis und Stolperstein. */
@Composable
fun Fallkarte(fall: Fall, mitLage: Boolean = true) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(fall.titel, style = MaterialTheme.typography.titleMedium)
            Text(
                fall.gebiet,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (mitLage) {
                Spacer(Modifier.height(8.dp))
                Text(fall.lage.trim(), style = MaterialTheme.typography.bodyMedium)
            }
            Spacer(Modifier.height(10.dp))
            Text(
                "Daraus zu lernen",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.secondary,
            )
            Text(fall.lernhinweis.trim(), style = MaterialTheme.typography.bodyMedium)
            if (fall.stolperstein.isNotBlank()) {
                Spacer(Modifier.height(10.dp))
                Text(
                    "Häufiger Fehler",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.error,
                )
                Text(fall.stolperstein.trim(), style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
