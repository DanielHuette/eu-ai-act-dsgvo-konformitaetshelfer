package de.konformitaetshelfer.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
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
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import de.konformitaetshelfer.daten.Risikoklasse

/**
 * Die Sammlung der 44 Anwendungsfälle.
 *
 * Wer kein eigenes System einordnen will, lernt hier an fremden Fällen - und
 * findet oft den eigenen wieder. Die Fälle sind nach Gebieten geordnet, wie
 * sie in den Regeldateien stehen.
 */
@Composable
fun ColumnScope.Fallsammlung(modell: Helfermodell) {
    val gewaehlt = modell.gewaehlterFall
    Kopfzeile(
        titel = if (gewaehlt == null) "Anwendungsfälle" else "Anwendungsfall",
        unterzeile = if (gewaehlt == null) "${modell.faelle.size} ausgearbeitete Fälle" else "",
        zurueck = {
            if (gewaehlt == null) modell.zu(Bildschirm.START) else modell.fallWaehlen(null)
        },
    )

    if (!modell.geladen) {
        Ladehinweis(Modifier.weight(1f))
        return
    }

    LazyColumn(modifier = Modifier.fillMaxWidth().weight(1f).padding(horizontal = 16.dp)) {
        if (gewaehlt != null) {
            item {
                Spacer(Modifier.height(16.dp))
                Risikoklasse.ausWert(gewaehlt.einstufung)?.let { Klassenschild(it) }
                Spacer(Modifier.height(10.dp))
                Fallkarte(gewaehlt)

                Abschnittstitel("Begründung")
                Text(gewaehlt.begruendung.trim(), style = MaterialTheme.typography.bodyMedium)

                Abschnittstitel("Pflichten in diesem Fall")
            }
            items(gewaehlt.pflichten) { satz ->
                Row(modifier = Modifier.padding(vertical = 4.dp)) {
                    Text("—  ", style = MaterialTheme.typography.bodyMedium)
                    Text(satz, style = MaterialTheme.typography.bodyMedium)
                }
            }
            item {
                Abschnittstitel("Fundstellen")
                Text(
                    gewaehlt.rechtsgrundlage.joinToString("  ·  "),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary,
                )
                Spacer(Modifier.height(28.dp))
            }
        } else {
            for ((gebiet, inGebiet) in modell.faelle.groupBy { it.gebiet }) {
                item { Abschnittstitel(gebiet.ifBlank { "Weitere" }) }
                items(inGebiet, key = { it.kennung }) { fall ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .clickable { modell.fallWaehlen(fall) },
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.surface,
                        ),
                        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Text(fall.titel, style = MaterialTheme.typography.titleMedium)
                            Spacer(Modifier.height(4.dp))
                            Text(
                                (Risikoklasse.ausWert(fall.einstufung)?.anzeige
                                    ?: fall.einstufung) + "  ·  " + fall.rolle,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
            item { Spacer(Modifier.height(28.dp)) }
        }
    }
}
