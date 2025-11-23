from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO
from model import tour
from model import attrazione


class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione


        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0

        # TODO: Aggiungere eventuali altri attributi

        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        relazioni = TourDAO.get_tour_attrazioni() # elenco di id

        for relazione in relazioni:
            id_tour = relazione["id_tour"] # isolo id_tour
            id_attr = relazione["id_attrazione"] # isolo id_attrazione

            tour = self.tour_map.get(id_tour) # estraggo gli effettivi tour associati agli id
            attrazione = self.attrazioni_map.get(id_attr) # estraggo le effettive attrazioni associate agli id

            # Controlli di sicurezza
            if tour is None or attrazione is None:
                continue  # salto relazioni invalide

            tour.attrazioni.add(attrazione)
            attrazione.tour.add(tour)

        # TODO

    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        # Reset dei risultati ottimali
        self._pacchetto_ottimo = []
        self._valore_ottimo = -1
        self._costo = 0

        # 1️⃣ Filtrare i tour della regione
        lista_tour = []
        for tour in self.tour_map.values():
            if tour.id_regione == id_regione:
                lista_tour.append(tour)

        # 2️⃣ Variabili iniziali per la ricorsione
        pacchetto_parziale = []
        durata_corrente = 0
        costo_corrente = 0
        valore_corrente = 0
        attrazioni_usate = set()

        # 3️⃣ Avvio della ricorsione
        self._ricorsione(
            start_index=0,
            lista_tour=lista_tour,
            pacchetto_parziale=pacchetto_parziale,
            durata_corrente=durata_corrente,
            costo_corrente=costo_corrente,
            valore_corrente=valore_corrente,
            attrazioni_usate=attrazioni_usate,
            max_giorni=max_giorni,
            max_budget=max_budget
        )

        # 4️⃣ Risultato
        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

        # TODO

        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, lista_tour: list,
                    pacchetto_parziale: list, durata_corrente: int,
                    costo_corrente: float, valore_corrente: int,
                    attrazioni_usate: set, max_giorni: int, max_budget: float):
        """ Algoritmo di ricorsione che deve trovare il pacchetto che massimizza il valore culturale"""

        # 🟤 A) Aggiorna migliore soluzione trovata
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()
            self._costo = costo_corrente

        # 🟢 B) Caso terminale implicito: se superiamo la lista dei tour → stop
        if start_index >= len(lista_tour):
            return

        # 🔁 C) Loop sui tour rimanenti
        for i in range(start_index, len(lista_tour)):
            tour = lista_tour[i]

            # 1️⃣ Controllo attrazioni duplicate
            if not tour.attrazioni.isdisjoint(attrazioni_usate):
                continue  # se c’è almeno una attrazione già usata → salta

            # 2️⃣ Controllo durata
            nuova_durata = durata_corrente + tour.durata_giorni
            if max_giorni is not None and nuova_durata > max_giorni:
                continue

            # 3️⃣ Controllo budget
            nuovo_costo = costo_corrente + tour.costo
            if max_budget is not None and nuovo_costo > max_budget:
                continue

            # 4️⃣ Calcolo nuovo valore culturale
            valore_tour = sum(attr.valore_culturale for attr in tour.attrazioni)
            nuovo_valore = valore_corrente + valore_tour

            # 🟡 D) Aggiornamento stato parziale
            pacchetto_parziale.append(tour)
            attrazioni_da_aggiungere = set(tour.attrazioni)
            attrazioni_usate.update(attrazioni_da_aggiungere)

            # 🔴 E) Ricorsione
            self._ricorsione(
                start_index=i + 1,
                lista_tour=lista_tour,
                pacchetto_parziale=pacchetto_parziale,
                durata_corrente=nuova_durata,
                costo_corrente=nuovo_costo,
                valore_corrente=nuovo_valore,
                attrazioni_usate=attrazioni_usate,
                max_giorni=max_giorni,
                max_budget=max_budget
            )

            # 🟣 F) Backtracking
            pacchetto_parziale.pop()
            attrazioni_usate.difference_update(attrazioni_da_aggiungere)

        # TODO: è possibile cambiare i parametri formali della funzione se ritenuto opportuno
