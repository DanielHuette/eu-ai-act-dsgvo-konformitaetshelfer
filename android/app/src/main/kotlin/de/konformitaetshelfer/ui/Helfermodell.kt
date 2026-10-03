package de.konformitaetshelfer.ui

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import de.konformitaetshelfer.Anwendung
import de.konformitaetshelfer.Werkzeug
import de.konformitaetshelfer.daten.Antwort
import de.konformitaetshelfer.daten.Einstufung
import de.konformitaetshelfer.daten.Fall
import de.konformitaetshelfer.daten.Risikoklasse
import de.konformitaetshelfer.daten.Rolle
import de.konformitaetshelfer.daten.Systembeschreibung
import de.konformitaetshelfer.daten.Treffer
import de.konformitaetshelfer.einstufung.Frage
import de.konformitaetshelfer.modell.Anbieter
import de.konformitaetshelfer.modell.Antwortgeber
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** Welcher Bildschirm zu sehen ist. */
enum class Bildschirm { START, FRAGEBOGEN, ERGEBNIS, FAELLE, DATENSCHUTZ, EINSTELLUNGEN }

/**
 * Der Zustand der App.
 *
 * Alles Rechnen läuft über [viewModelScope] auf einem Nebenläufer. Suche und
 * Einbettung brauchen auf einem Telefon einige hundert Millisekunden; auf dem
 * Hauptfaden wäre das eine stehende Oberfläche.
 */
class Helfermodell(anwendung: Application) : AndroidViewModel(anwendung) {

    private val werkzeug: Werkzeug = (anwendung as Anwendung).werkzeug

    var geladen by mutableStateOf(false)
        private set
    var bildschirm by mutableStateOf(Bildschirm.START)
        private set
    var beschreibung by mutableStateOf("")
        private set
    var angaben by mutableStateOf(Systembeschreibung())
        private set
    var alleVerbote by mutableStateOf(false)
        private set
    var einstufung by mutableStateOf<Einstufung?>(null)
        private set
    var belege by mutableStateOf<List<Treffer>>(emptyList())
        private set
    var passenderFall by mutableStateOf<Fall?>(null)
        private set
    var ausformuliert by mutableStateOf("")
        private set
    var meldung by mutableStateOf("")
        private set
    var rechnet by mutableStateOf(false)
        private set
    var gewaehlterFall by mutableStateOf<Fall?>(null)
        private set

    init {
        viewModelScope.launch {
            withContext(Dispatchers.IO) { werkzeug.oeffnen() }
            geladen = true
        }
    }

    // ------------------------------------------------------------- Steuerung

    fun zu(ziel: Bildschirm) {
        bildschirm = ziel
    }

    fun beschreibungSetzen(text: String) {
        beschreibung = text
        angaben = angaben.copy(beschreibung = text)
    }

    fun antworten(feld: String, antwort: Antwort) {
        angaben = angaben.mit(feld, antwort)
    }

    fun rolleSetzen(rolle: Rolle?) {
        angaben = angaben.copy(rolle = rolle)
    }

    fun produkterstellerSetzen(ist: Boolean) {
        angaben = angaben.copy(istProdukthersteller = ist)
    }

    fun verboteAufklappen() {
        alleVerbote = true
    }

    fun fallWaehlen(fall: Fall?) {
        gewaehlterFall = fall
    }

    val fragen: List<Frage>
        get() = if (geladen) werkzeug.pruefer.fragen(angaben, alleVerbote) else emptyList()

    val faelle: List<Fall>
        get() = if (geladen) werkzeug.faelle else emptyList()

    val pruefabschnitte get() = if (geladen) werkzeug.pruefabschnitte else emptyList()

    val datenstand: String get() = if (geladen) werkzeug.datenstand() else ""
    val regelstand: String get() = if (geladen) werkzeug.regelstand() else ""
    val einheiten: Int get() = if (geladen) werkzeug.meta["einheiten"]?.toIntOrNull() ?: 0 else 0

    fun schluesselEingetragen(): Boolean = geladen && werkzeug.schluessel.bereit()

    fun anbieter(): Anbieter? = if (geladen) werkzeug.schluessel.gewaehlt() else null

    fun anbieterSetzen(anbieter: Anbieter?) {
        if (geladen) werkzeug.schluessel.waehlen(anbieter)
    }

    fun schluesselSetzen(anbieter: Anbieter, wert: String) {
        if (!geladen) return
        if (wert.isBlank()) werkzeug.schluessel.loeschen(anbieter)
        else werkzeug.schluessel.eintragen(anbieter, wert)
    }

    fun hatSchluessel(anbieter: Anbieter): Boolean =
        geladen && !werkzeug.schluessel.schluessel(anbieter).isNullOrBlank()

    // -------------------------------------------------------------- Auskunft

    /**
     * Rechnet die Auskunft.
     *
     * Reihenfolge mit Absicht: zuerst die Einstufung aus dem
     * Entscheidungsbaum, dann die Belege zu DIESEM Ergebnis. Umgekehrt würde
     * die Suche die Einstufung färben.
     */
    fun auskunftRechnen() {
        if (!geladen || rechnet) return
        rechnet = true
        meldung = ""
        ausformuliert = ""
        viewModelScope.launch {
            val ergebnis = withContext(Dispatchers.Default) {
                val eingeordnet = werkzeug.pruefer.pruefen(angaben)
                val suchtext = buildString {
                    append(beschreibung)
                    for (hinweis in eingeordnet.hinweise) {
                        append(' ')
                        append(hinweis.fundstelle)
                    }
                }
                val gefunden = werkzeug.suche.suchen(suchtext, anzahl = 8)
                val fall = passendenFall(eingeordnet.klasse, eingeordnet.rollen, gefunden)
                Triple(eingeordnet, gefunden, fall)
            }
            einstufung = ergebnis.first
            belege = ergebnis.second
            passenderFall = ergebnis.third
            rechnet = false
            bildschirm = Bildschirm.ERGEBNIS
        }
    }

    /**
     * Sucht den Anwendungsfall, der am besten passt.
     *
     * Erste Wahl ist ein Fall, den die Suche selbst gefunden hat - dann
     * stimmt nicht nur die Klasse, sondern auch der Gegenstand. Erst wenn
     * keiner dabei ist, wird nach Klasse und Rolle genommen.
     */
    private fun passendenFall(
        klasse: Risikoklasse,
        rollen: Set<Rolle>,
        gefunden: List<Treffer>,
    ): Fall? {
        val ausDerSuche = gefunden.asSequence()
            .filter { it.einheit.istAnwendungsfall }
            .mapNotNull { treffer ->
                werkzeug.faelle.firstOrNull { "fall/${it.kennung}" == treffer.einheit.kennung }
            }
            .firstOrNull()
        if (ausDerSuche != null) return ausDerSuche

        val rollenwerte = rollen.map { it.wert }.toSet()
        return werkzeug.faelle.firstOrNull {
            it.einstufung == klasse.wert && it.rolle in rollenwerte
        } ?: werkzeug.faelle.firstOrNull { it.einstufung == klasse.wert }
    }

    /** Lässt die Auskunft ausformulieren, wenn ein Schlüssel eingetragen ist. */
    fun ausformulieren() {
        val fertig = einstufung ?: return
        if (!geladen || rechnet) return
        rechnet = true
        meldung = ""
        viewModelScope.launch {
            val ergebnis = withContext(Dispatchers.IO) {
                werkzeug.antwortgeber.ausformulieren(beschreibung, fertig, belege)
            }
            when (ergebnis) {
                is Antwortgeber.Ergebnis.Text -> ausformuliert = ergebnis.inhalt
                is Antwortgeber.Ergebnis.Fehler -> meldung = ergebnis.meldung
                Antwortgeber.Ergebnis.KeinSchluessel ->
                    meldung = "Dafür ist in den Einstellungen ein Schlüssel einzutragen."
            }
            rechnet = false
        }
    }

    fun neuAnfangen() {
        beschreibung = ""
        angaben = Systembeschreibung()
        alleVerbote = false
        einstufung = null
        belege = emptyList()
        passenderFall = null
        ausformuliert = ""
        meldung = ""
        bildschirm = Bildschirm.START
    }
}
