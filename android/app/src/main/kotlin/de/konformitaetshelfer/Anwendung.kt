package de.konformitaetshelfer

import android.app.Application
import de.konformitaetshelfer.daten.Fall
import de.konformitaetshelfer.daten.Pflicht
import de.konformitaetshelfer.daten.Pruefabschnitt
import de.konformitaetshelfer.daten.Rechtsbestand
import de.konformitaetshelfer.einstufung.Pruefer
import de.konformitaetshelfer.modell.Antwortgeber
import de.konformitaetshelfer.modell.Schluesselspeicher
import de.konformitaetshelfer.suche.Einbetter
import de.konformitaetshelfer.suche.Suche

/**
 * Alles, was die App einmal öffnen muss - Datenbank, Einbetter, Regelwerk.
 *
 * Das Öffnen dauert: die Datenbank wird beim ersten Start aus dem Paket
 * herausgelegt, der Wortschatz des Einbetters hat 250 002 Einträge. Deshalb
 * geschieht es nicht im Erstellungsaufruf, sondern in [oeffnen], das aus
 * einem Nebenläufer gerufen wird.
 */
class Werkzeug(private val anwendung: Application) {

    lateinit var bestand: Rechtsbestand
        private set
    lateinit var suche: Suche
        private set
    lateinit var pruefer: Pruefer
        private set
    lateinit var pflichten: List<Pflicht>
        private set
    lateinit var faelle: List<Fall>
        private set
    lateinit var pruefabschnitte: List<Pruefabschnitt>
        private set
    lateinit var meta: Map<String, String>
        private set
    lateinit var schluessel: Schluesselspeicher
        private set
    lateinit var antwortgeber: Antwortgeber
        private set

    @Volatile
    var offen: Boolean = false
        private set

    /** Ob das Einbettungsmodell geladen werden konnte. Steuert nur die Suchwege. */
    @Volatile
    var mitVektorsuche: Boolean = false
        private set

    @Synchronized
    fun oeffnen() {
        if (offen) return

        bestand = Rechtsbestand.oeffnen(anwendung)
        meta = bestand.meta()
        pflichten = bestand.pflichten()
        faelle = bestand.faelle()
        pruefabschnitte = bestand.pruefabschnitte()
        pruefer = Pruefer(bestand.risikoregeln(), pflichten)
        schluessel = Schluesselspeicher(anwendung)
        antwortgeber = Antwortgeber(schluessel)

        val dimensionen = meta["dimensionen"]?.toIntOrNull() ?: 384
        val hoechstens = meta["max_wortmarken"]?.toIntOrNull() ?: 512
        // Fehlt das Modell im Paket oder lässt es sich nicht laden, läuft die
        // Suche über Fundstelle und Stichwort weiter. Besser eine Suche mit
        // zwei Wegen als keine App.
        val einbetter = runCatching { Einbetter.oeffnen(anwendung, hoechstens) }.getOrNull()
        mitVektorsuche = einbetter != null
        suche = Suche(
            bestand = bestand,
            einbetter = einbetter,
            vorsilbeFrage = meta["vorsilbe_frage"] ?: "query: ",
            dimensionen = dimensionen,
        )
        offen = true
    }

    /** Der Datenstand, wie er in jeder Auskunft genannt wird. */
    fun datenstand(): String = meta["datenstand"].orEmpty()

    fun regelstand(): String = meta["regelstand"].orEmpty()
}

class Anwendung : Application() {
    val werkzeug: Werkzeug by lazy { Werkzeug(this) }
}
