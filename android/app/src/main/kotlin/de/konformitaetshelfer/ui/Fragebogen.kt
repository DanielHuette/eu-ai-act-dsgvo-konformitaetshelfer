package de.konformitaetshelfer.ui

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
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.konformitaetshelfer.daten.Antwort
import de.konformitaetshelfer.daten.Rolle
import de.konformitaetshelfer.einstufung.Frage

/**
 * Der Fragebogen.
 *
 * Die Fragen kommen aus dem Regelwerk, nicht aus diesem Quelltext, und jede
 * nennt ihre Fundstelle. Wer wissen will, warum er das gefragt wird, liest
 * sie mit.
 *
 * Drei Antworten statt zwei: "noch offen" ist eine eigene Antwort und wird
 * NICHT als Nein gelesen. Eine übersprungene Frage darf keine Entlastung
 * vortäuschen - sie erscheint am Ende als offener Punkt.
 */
@Composable
fun ColumnScope.Fragebogen(modell: Helfermodell) {
    Kopfzeile(
        titel = "Fragen zum System",
        unterzeile = "Ihre Antworten entscheiden die Einstufung",
        zurueck = { modell.zu(Bildschirm.START) },
    )

    if (!modell.geladen) {
        Ladehinweis(Modifier.weight(1f))
        return
    }

    val fragen = modell.fragen
    val nachGruppe = fragen.groupBy { it.gruppe }

    LazyColumn(
        modifier = Modifier.fillMaxWidth().weight(1f).padding(horizontal = 16.dp),
    ) {
        item {
            Spacer(Modifier.height(16.dp))
            Abschnittstitel("Ihre Rolle")
            Text(
                "Anbieter ist, wer das System entwickelt oder unter eigenem Namen in " +
                    "Verkehr bringt. Betreiber ist, wer es in eigener Verantwortung " +
                    "einsetzt. Die Rolle entscheidet, welche Pflichten gelten.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                for (rolle in listOf(Rolle.ANBIETER, Rolle.BETREIBER)) {
                    Wahlknopf(
                        text = rolle.anzeige,
                        gewaehlt = modell.angaben.rolle == rolle,
                        modifier = Modifier.weight(1f),
                        onClick = {
                            modell.rolleSetzen(
                                if (modell.angaben.rolle == rolle) null else rolle
                            )
                        },
                    )
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Switch(
                    checked = modell.angaben.istProdukthersteller,
                    onCheckedChange = { modell.produkterstellerSetzen(it) },
                )
                Text(
                    "Wir bauen das System in ein eigenes Produkt ein",
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(start = 12.dp),
                )
            }
        }

        for ((gruppe, inGruppe) in nachGruppe) {
            item {
                Abschnittstitel(gruppe)
            }
            items(inGruppe, key = { it.feld }) { frage ->
                Fragekarte(
                    frage = frage,
                    antwort = modell.angaben.antwort(frage.feld),
                    onAntwort = { modell.antworten(frage.feld, it) },
                )
            }
        }

        if (!modell.alleVerbote) {
            item {
                Spacer(Modifier.height(8.dp))
                TextButton(onClick = { modell.verboteAufklappen() }) {
                    Text("Alle Fragen zu verbotenen Praktiken anzeigen")
                }
                Text(
                    "Gezeigt werden sonst nur die Verbotsfragen, auf die Ihre " +
                        "Beschreibung deutet. Ein Verbot wiegt schwer - wer unsicher " +
                        "ist, geht alle neun durch.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        item {
            Spacer(Modifier.height(20.dp))
            Vorbehaltstreifen(
                "Offen gelassene Fragen erscheinen im Ergebnis als offene Punkte. " +
                    "Sie gelten nicht als Nein."
            )
            Spacer(Modifier.height(24.dp))
        }
    }

    Row(
        modifier = Modifier.fillMaxWidth().padding(16.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        OutlinedButton(onClick = { modell.zu(Bildschirm.START) }) {
            Text("Zurück")
        }
        Button(
            onClick = { modell.auskunftRechnen() },
            enabled = !modell.rechnet,
            modifier = Modifier.weight(1f),
        ) {
            Text(if (modell.rechnet) "rechnet" else "Einordnen und belegen")
        }
    }
}

/** Eine Frage mit drei Antworten. */
@Composable
private fun Fragekarte(frage: Frage, antwort: Antwort, onAntwort: (Antwort) -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                frage.text.trim(),
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
            if (frage.fundstelle.isNotBlank()) {
                Text(
                    frage.fundstelle,
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Wahlknopf("Ja", antwort == Antwort.JA, Modifier.weight(1f)) {
                    onAntwort(Antwort.JA)
                }
                Wahlknopf("Nein", antwort == Antwort.NEIN, Modifier.weight(1f)) {
                    onAntwort(Antwort.NEIN)
                }
                Wahlknopf("noch offen", antwort == Antwort.OFFEN, Modifier.weight(1.2f)) {
                    onAntwort(Antwort.OFFEN)
                }
            }
        }
    }
}

/** Ein Knopf, der gewählt anders aussieht - ohne vorläufige Bausteine. */
@Composable
fun Wahlknopf(
    text: String,
    gewaehlt: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    if (gewaehlt) {
        FilledTonalButton(onClick = onClick, modifier = modifier) {
            Text(text, fontWeight = FontWeight.SemiBold, maxLines = 1)
        }
    } else {
        OutlinedButton(onClick = onClick, modifier = modifier) {
            Text(text, maxLines = 1)
        }
    }
}
