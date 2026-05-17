<template>
  <div v-if="!accessChecked" class="min-h-screen gradient-bg text-slate-100 flex items-center justify-center px-6">
    <div class="w-full max-w-lg text-center glass-panel p-6 md:p-8">
      <p class="step-pill">Diag1 · Ładowanie</p>
      <h1 class="mt-3 text-2xl md:text-3xl font-display font-semibold text-white">Sprawdzanie dostępu...</h1>
    </div>
  </div>

  <div v-else-if="!isAccessGranted" class="min-h-screen gradient-bg text-slate-100 flex items-center justify-center px-6">
    <div class="w-full max-w-lg">
      <section class="glass-panel p-6 md:p-8">
        <p class="step-pill mb-2">Diag1 · Bezpieczny dostęp</p>
        <h1 class="text-2xl md:text-3xl font-display font-semibold text-white">
          Dostęp do aplikacji Diag1
        </h1>
        <p class="mt-3 text-slate-300">
          Ta wersja Cloud Run jest przeznaczona do użytku wyłącznie dla osób
          uprawnionych do oceny projektu. Wpisz hasło, aby przejść dalej.
          Aplikacja ma charakter narzędzia wspierającego personel medyczny i służy do przygotowania
          danych do dalszej rozmowy z lekarzem.
        </p>
        <p class="mt-2 text-sm text-slate-300">
          <strong>Uwaga:</strong> To hasło zabezpiecza warstwę prezentacji.
          Po wejściu pojawia się pełna wersja aplikacji.
        </p>
        <div class="mt-6 space-y-3">
          <label class="block">
            <span class="text-sm text-slate-200">Hasło dostępu:</span>
            <input
              v-model="accessPasswordInput"
              type="password"
              class="mt-2 w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-white"
              placeholder="Wprowadź hasło"
              @keyup.enter="authenticateAccess"
            />
          </label>
          <button
            class="px-5 py-3 rounded-xl bg-glow-700 hover:bg-glow-500 text-white font-semibold"
            :disabled="!accessPasswordInput || accessLoading"
            @click="authenticateAccess"
          >
            Wejdź do aplikacji
          </button>
          <p v-if="accessError" class="text-sm text-rose-300">{{ accessError }}</p>
        </div>
      </section>
    </div>
  </div>

  <div v-else class="min-h-screen gradient-bg text-slate-100">
    <header class="px-6 py-8">
      <div class="max-w-5xl mx-auto">
        <p class="step-pill">Diag1 · LLM Trend Analysis</p>
        <h1 class="mt-3 text-3xl md:text-4xl font-display font-semibold text-white">
          Analiza Trendów Wyników Badań Laboratoryjnych
        </h1>
        <p class="mt-3 text-slate-300 max-w-3xl">
          Prototyp demonstracyjny z mechanizmami zgodności, anonimizacją i analizą trendów przez Google AI.
        </p>
      </div>
    </header>

    <main class="px-6 pb-12">
      <div class="max-w-5xl mx-auto grid gap-6">
        <section class="glass-panel p-6 md:p-8">
          <div class="flex flex-wrap gap-3 text-sm text-slate-300">
            <span :class="stepClass(1)">1. Zgody</span>
            <span :class="stepClass(2)">2. Upload</span>
            <span :class="stepClass(3)">3. Przetwarzanie</span>
            <span :class="stepClass(4)">4. Raport</span>
            <span :class="stepClass(5)">5. Zamknięcie</span>
            <span @click="goToAdminPanel" class="px-3 py-1 rounded-full bg-slate-800 text-slate-400 cursor-pointer hover:bg-slate-700">6. 🔒 Zgody (Admin)</span>
          </div>

          <div v-if="step === 1" class="mt-6 space-y-6">
            <div class="bg-amber-500/10 border border-amber-400/40 rounded-xl p-4">
              <p class="font-semibold text-amber-200">
                UWAGA: TO NIE JEST PORADA LEKARSKA
              </p>
              <p class="text-sm text-amber-100/80 mt-2">
                Niniejsza aplikacja ma charakter wyłącznie edukacyjny i poglądowy. Wygenerowany raport
                służy jedynie do wizualizacji trendów matematycznych w wynikach badań i nie stanowi diagnozy
                medycznej, zalecenia terapeutycznego ani interpretacji wyników w rozumieniu ustawy o działalności leczniczej.
              </p>
              <p class="text-sm text-amber-100/80 mt-2">
                System oparty o sztuczną inteligencję może generować błędne informacje. Nie podejmuj żadnych decyzji
                zdrowotnych (w tym zmiany dawkowania leków) na podstawie tego raportu. Każdy wynik skonsultuj z
                wykwalifikowanym personelem medycznym.
              </p>
              <p class="text-sm text-amber-100/80 mt-2">
                Zakresy referencyjne są zależne od metody oznaczenia, laboratorium oraz danych pacjenta
                (wiek, płeć, stan fizjologiczny i choroby towarzyszące). Brak źródła normy obniża wiarygodność
                interpretacji — taka informacja wymaga dodatkowej weryfikacji medycznej.
              </p>
            </div>

            <div>
              <h2 class="text-xl font-display font-semibold text-white">Legal Gate</h2>
              <p class="text-slate-300 text-sm mt-2">
                Zaznacz wszystkie zgody, aby kontynuować. Zgody nie są domyślnie zaznaczone.
              </p>
              <p class="text-xs text-slate-400 mt-2">
                Pełna treść: <a class="text-glow-500" href="#regulamin">Regulamin</a> ·
                <a class="text-glow-500" href="#privacy">Polityka Prywatności</a>
              </p>
              <p class="text-xs text-slate-400 mt-1">
                Pobierz: <a class="text-glow-500" href="/regulamin.txt" download>Regulamin (.txt)</a> ·
                <a class="text-glow-500" href="/polityka-prywatnosci.txt" download>Polityka Prywatności (.txt)</a>
              </p>

              <div class="mt-5 space-y-4">
                <label class="flex gap-3 items-start">
                  <input v-model="consentTerms" type="checkbox" class="mt-1" />
                  <span class="text-sm text-slate-200">
                    Oświadczam, że zapoznałem/am się z Regulaminem serwisu oraz Polityką Prywatności i
                    akceptuję ich postanowienia.
                  </span>
                </label>
                <label class="flex gap-3 items-start">
                  <input v-model="consentHealth" type="checkbox" class="mt-1" />
                  <span class="text-sm text-slate-200">
                    Wyrażam wyraźną zgodę na przetwarzanie moich danych osobowych o stanie zdrowia zawartych
                    w załączonych plikach PDF w celu wykonania analizy trendów wyników badań. Rozumiem, że
                    podanie danych jest dobrowolne, ale niezbędne do działania usługi. Mam prawo cofnąć zgodę
                    w dowolnym momencie.
                  </span>
                </label>
                <label class="flex gap-3 items-start">
                  <input v-model="consentAi" type="checkbox" class="mt-1" />
                  <span class="text-sm text-slate-200">
                    Jestem świadomy/a, że analiza wykonywana jest w sposób zautomatyzowany przy użyciu modelu
                    sztucznej inteligencji Google (Vertex AI lub Gemini API), a wynik może zawierać błędy
                    i wymaga weryfikacji przez człowieka.
                  </span>
                </label>
              </div>
            </div>

            <div>
              <h2 class="text-xl font-display font-semibold text-white">Poziom anonimizacji danych</h2>
              <p class="text-slate-300 text-sm mt-2">
                Wybierz, jak bardzo chcesz zanonimizować swoje dane medyczne przed analizą.
              </p>
              <div class="mt-4 space-y-3">
                <label class="flex gap-3 items-start p-4 border border-slate-600 rounded-xl cursor-pointer hover:bg-slate-800/30 transition-colors" :class="{ 'border-glow-500 bg-glow-500/10': anonymizationLevel === 'full' }">
                  <input v-model="anonymizationLevel" type="radio" value="full" class="mt-1" />
                  <div>
                    <span class="text-sm text-slate-200 font-semibold">Pełna anonimizacja (Zalecane)</span>
                    <p class="text-xs text-slate-400 mt-1">
                      Usuń wszystkie dane osobowe (imię, nazwisko, PESEL, adres, nr telefonu).
                      System zachowa tylko wartości liczbowe z badań.
                    </p>
                  </div>
                </label>
                <label class="flex gap-3 items-start p-4 border border-slate-600 rounded-xl cursor-pointer hover:bg-slate-800/30 transition-colors" :class="{ 'border-glow-500 bg-glow-500/10': anonymizationLevel === 'medical' }">
                  <input v-model="anonymizationLevel" type="radio" value="medical" class="mt-1" />
                  <div>
                    <span class="text-sm text-slate-200 font-semibold">Tylko dane medyczne</span>
                    <p class="text-xs text-slate-400 mt-1">
                      Zachowaj: wyniki badań, wiek, płeć, wagę (jeśli dostępne).
                      Usuń dane identyfikujące (imię, nazwisko, PESEL, adres).
                    </p>
                  </div>
                </label>
              </div>
            </div>

            <div class="grid md:grid-cols-2 gap-4 text-sm text-slate-300">
              <div id="privacy" class="bg-slate-800/60 border border-slate-700 rounded-xl p-4">
                <h3 class="font-semibold text-white">Klauzula informacyjna RODO</h3>
                <p class="mt-2">
                  <strong>Kto jest administratorem danych?</strong><br>
                  Administratorem Twoich danych osobowych jest <strong>Maciej Białostocki</strong>, realizujący projekt
                  w ramach studiów podyplomowych na Warszawskim Uniwersytecie Medycznym w Warszawie.
                  Kontakt: <a href="mailto:auto@vabank.pl" class="text-glow-500">auto@vabank.pl</a>
                </p>
                <details class="mt-3 text-xs text-slate-400">
                  <summary class="cursor-pointer text-slate-200">Pełna treść klauzuli informacyjnej</summary>
                  <div class="mt-3 space-y-3">
                    <p>
                      <strong class="text-slate-200">1. Administrator danych:</strong><br>
                      Maciej Białostocki, e-mail kontaktowy: auto@vabank.pl
                    </p>
                    <p>
                      <strong class="text-slate-200">2. Inspektor ochrony danych:</strong><br>
                      Administrator nie wyznaczył IOD. W sprawach ochrony danych skontaktuj się na: auto@vabank.pl
                    </p>
                    <p>
                      <strong class="text-slate-200">3. Cele i podstawy prawne przetwarzania:</strong><br>
                      Celem jest wykonanie jednorazowej analizy porównawczej wyników badań z plików PDF.<br>
                      Podstawą prawną jest zgoda użytkownika (Art. 6 ust. 1 lit. a RODO), a dla danych o zdrowiu:
                      wyraźna zgoda (Art. 9 ust. 2 lit. a RODO).
                    </p>
                    <p>
                      <strong class="text-slate-200">4. Odbiorcy danych:</strong><br>
                      Odbiorcami danych są dostawcy infrastruktury i modeli Google AI (Vertex AI / Gemini API).
                      Dane są przesyłane szyfrowanym kanałem TLS.
                    </p>
                    <p>
                      <strong class="text-slate-200">5. Przekazywanie danych poza EOG:</strong><br>
                      Przy konfiguracji Vertex AI w wybranym regionie UE przetwarzanie zapytania i odpowiedzi
                      odbywa się w tym regionie (mechanizm Data Residency).
                      W przypadku użycia Gemini API (Developer API) routing jest globalny i nie gwarantuje
                      wskazania konkretnego kraju przetwarzania, dlatego może dojść do przekazania danych poza EOG.
                      W takim przypadku stosowane są zabezpieczenia z Art. 46 RODO (w tym standardowe klauzule umowne).
                      Informację o zastosowanych zabezpieczeniach możesz uzyskać, pisząc na auto@vabank.pl.
                    </p>
                    <p>
                      <strong class="text-slate-200">6. Okres przechowywania danych:</strong><br>
                      Pliki PDF są przetwarzane w RAM i nie są zapisywane jako pliki trwałe.
                      Treść raportu i tekst wyodrębniony z dokumentów jest usuwana po kliknięciu
                      „Zakończ sesję i usuń dane”, a najpóźniej automatycznie po 24 godzinach od utworzenia sesji.
                      Metadane zgód (UUID sesji, czas, status, zgody, poziom anonimizacji) są przechowywane dla
                      rozliczalności (Art. 5 ust. 2 RODO).
                    </p>
                    <p>
                      <strong class="text-slate-200">7. Twoje prawa:</strong><br>
                      Masz prawo do:<br>
                      • dostępu do swoich danych osobowych (Art. 15 RODO)<br>
                      • sprostowania danych (Art. 16 RODO)<br>
                      • usunięcia danych (Art. 17 RODO)<br>
                      • ograniczenia przetwarzania (Art. 18 RODO)<br>
                      • przenoszenia danych (Art. 20 RODO)<br>
                      • wniesienia sprzeciwu wobec przetwarzania (Art. 21 RODO)<br>
                      • cofnięcia zgody w dowolnym momencie (cofnięcie zgody nie wpływa na zgodność z prawem
                      przetwarzania dokonanego przed jej cofnięciem). Cofnięcia możesz dokonać przyciskiem
                      „Zakończ sesję i usuń dane” lub kontaktując się mailowo.
                    </p>
                    <p>
                      <strong class="text-slate-200">8. Prawo do skargi:</strong><br>
                      Masz prawo wniesienia skargi do Prezesa Urzędu Ochrony Danych Osobowych (PUODO),
                      ul. Moniuszki 1A, 00-014 Warszawa.
                    </p>
                    <p>
                      <strong class="text-slate-200">9. Zautomatyzowane podejmowanie decyzji:</strong><br>
                      Nie podejmujemy zautomatyzowanych decyzji na podstawie Twoich danych, w tym profilowania
                      w rozumieniu Art. 22 RODO. Wygenerowany raport ma charakter wyłącznie informacyjny.
                    </p>
                    <p>
                      <strong class="text-slate-200">10. Dobrowolność podania danych:</strong><br>
                      Podanie danych jest dobrowolne, ale niezbędne do świadczenia usługi analizy trendów.
                      Niepodanie danych uniemożliwi wykonanie usługi.
                    </p>
                  </div>
                </details>
              </div>
              <div id="regulamin" class="bg-slate-800/60 border border-slate-700 rounded-xl p-4">
                <h3 class="font-semibold text-white">Regulamin świadczenia usług</h3>
                <p class="mt-2">
                  Aplikacja nie jest wyrobem medycznym w rozumieniu Rozporządzenia (UE) 2017/745 (MDR).
                  Usługodawca nie ponosi odpowiedzialności za skutki decyzji podjętych na podstawie raportu.
                  Aplikacja nie zastępuje konsultacji lekarskiej ani badań laboratoryjnych.
                </p>
                <details class="mt-3 text-xs text-slate-400">
                  <summary class="cursor-pointer text-slate-200">Pełna treść Regulaminu</summary>
                  <div class="mt-3 space-y-3">
                    <p>
                      <strong class="text-slate-200">§1 Rodzaj i zakres usług</strong><br>
                      Usługodawca udostępnia bezpłatne narzędzie webowe do automatycznego porównania parametrów
                      liczbowych z dwóch plików PDF przy użyciu modeli Google AI.
                    </p>
                    <p>
                      <strong class="text-slate-200">§2 Wymogi techniczne i warunki korzystania</strong><br>
                      Do korzystania z usługi niezbędne są:<br>
                      • urządzenie z dostępem do Internetu<br>
                      • przeglądarka internetowa obsługująca JavaScript<br>
                      • posiadanie wyników badań w formacie cyfrowym (.pdf)
                    </p>
                    <p>
                      <strong class="text-slate-200">§3 Zakaz dostarczania treści bezprawnych</strong><br>
                      Użytkownik zobowiązuje się nie przesyłać treści o charakterze bezprawnym oraz naruszających
                      prawa osób trzecich.
                    </p>
                    <p>
                      <strong class="text-slate-200">§4 Zawarcie i rozwiązanie umowy o usługę elektroniczną</strong><br>
                      Umowa zostaje zawarta z chwilą rozpoczęcia sesji i przesłania plików do analizy.
                      Użytkownik może zakończyć usługę w dowolnym momencie przyciskiem „Zakończ sesję i usuń dane”.
                    </p>
                    <p>
                      <strong class="text-slate-200">§5 Reklamacje</strong><br>
                      Reklamacje dotyczące działania usługi można zgłaszać na adres: auto@vabank.pl.
                      Reklamacja powinna zawierać opis problemu i datę zdarzenia. Odpowiedź udzielana jest
                      nie później niż w terminie 14 dni.
                    </p>
                    <p>
                      <strong class="text-slate-200">§6 Odpowiedzialność</strong><br>
                      • Aplikacja nie jest wyrobem medycznym w rozumieniu Rozporządzenia (UE) 2017/745 (MDR).<br>
                      • Usługodawca nie ponosi odpowiedzialności za skutki decyzji zdrowotnych podjętych na podstawie raportu.<br>
                      • Model AI może generować błędne informacje (halucynacje).<br>
                      • Aplikacja nie zastępuje wizyty lekarskiej ani diagnostyki laboratoryjnej.<br>
                      • Wygenerowany raport ma charakter edukacyjny i nie stanowi diagnozy.
                    </p>
                    <p>
                      <strong class="text-slate-200">§7 Dane osobowe</strong><br>
                      Szczegółowe informacje o przetwarzaniu danych osobowych znajdują się w Klauzuli informacyjnej RODO.
                    </p>
                  </div>
                </details>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <button
                class="px-5 py-3 rounded-xl bg-glow-700 hover:bg-glow-500 text-white font-semibold disabled:opacity-40"
                :disabled="!canStart || loading"
                @click="startSession"
              >
                Rozpocznij bezpieczną sesję
              </button>
              <span v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</span>
            </div>
          </div>

          <div v-if="step === 2" class="mt-6 space-y-6">
            <div>
              <h2 class="text-xl font-display font-semibold">Upload badań</h2>
              <p class="text-sm text-slate-300 mt-2">
                Wgraj dwa pliki PDF: Badanie A (starsze) i Badanie B (nowsze). Połączenie jest szyfrowane.
                To narzędzie wspiera lekarza podczas oceny zmian międzypomiarowych; raport nie stanowi decyzji
                klinicznej.
              </p>
            </div>

            <div class="grid md:grid-cols-2 gap-4">
              <div class="border border-dashed border-slate-600 rounded-2xl p-4 bg-slate-900/40">
                <h3 class="font-semibold text-white">Badanie A</h3>
                <div
                  class="mt-3 flex flex-col items-center justify-center gap-2 text-sm text-slate-300 min-h-[140px]"
                  @dragover.prevent
                  @drop.prevent="onDrop($event, 'a')"
                >
                  <p>Przeciągnij PDF lub wybierz plik</p>
                  <input type="file" accept="application/pdf" @change="onSelect($event, 'a')" />
                  <p v-if="fileA" class="text-slate-100">{{ fileA.name }}</p>
                </div>
              </div>
              <div class="border border-dashed border-slate-600 rounded-2xl p-4 bg-slate-900/40">
                <h3 class="font-semibold text-white">Badanie B</h3>
                <div
                  class="mt-3 flex flex-col items-center justify-center gap-2 text-sm text-slate-300 min-h-[140px]"
                  @dragover.prevent
                  @drop.prevent="onDrop($event, 'b')"
                >
                  <p>Przeciągnij PDF lub wybierz plik</p>
                  <input type="file" accept="application/pdf" @change="onSelect($event, 'b')" />
                  <p v-if="fileB" class="text-slate-100">{{ fileB.name }}</p>
                </div>
              </div>
            </div>

            <div v-if="anonymizationLevel === 'medical'" class="space-y-4">
              <div class="bg-blue-500/10 border border-blue-400/40 rounded-xl p-4">
                <h3 class="font-semibold text-blue-200">Dane medyczne (opcjonalne)</h3>
                <p class="text-sm text-blue-100/80 mt-2">
                  Podanie poniższych danych pomoże w dokładniejszej analizie trendów.
                  Jeśli dane znajdują się w plikach PDF, zostaną automatycznie wyodrębnione.
                </p>
              </div>

              <div class="grid md:grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm text-slate-300 mb-2">Wiek (lat)</label>
                  <input
                    v-model.number="patientAge"
                    type="number"
                    min="0"
                    max="150"
                    class="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-white"
                    placeholder="np. 45"
                  />
                </div>
                <div>
                  <label class="block text-sm text-slate-300 mb-2">Płeć</label>
                  <select
                    v-model="patientGender"
                    class="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-white"
                  >
                    <option value="">Wybierz...</option>
                    <option value="M">Mężczyzna</option>
                    <option value="K">Kobieta</option>
                    <option value="Inna">Inna</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm text-slate-300 mb-2">Waga (kg) - opcjonalnie</label>
                  <input
                    v-model.number="patientWeight"
                    type="number"
                    min="0"
                    max="500"
                    step="0.1"
                    class="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-white"
                    placeholder="np. 70"
                  />
                </div>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <button
                class="px-5 py-3 rounded-xl bg-glow-700 hover:bg-glow-500 text-white font-semibold disabled:opacity-40"
                :disabled="!canAnalyze || loading"
                @click="runAnalysis"
              >
                Uruchom analizę trendów
              </button>
              <button
                class="px-5 py-3 rounded-xl border border-slate-600 text-slate-300"
                @click="step = 1"
              >
                Wróć do zgód
              </button>
              <span v-if="errorMessage" class="text-sm text-rose-300">{{ errorMessage }}</span>
            </div>
          </div>

          <div v-if="step === 3" class="mt-6 space-y-6">
            <div>
              <h2 class="text-xl font-display font-semibold">Przetwarzanie i anonimizacja</h2>
              <p class="text-sm text-slate-300 mt-2">
                Trwa usuwanie danych osobowych i analiza trendów przez AI.
              </p>
            </div>

            <div class="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
              <div class="flex items-center gap-4">
                <div class="h-3 w-full bg-slate-700 rounded-full overflow-hidden">
                  <div class="h-full bg-glow-500" :style="{ width: progress + '%' }"></div>
                </div>
                <span class="text-sm text-slate-200">{{ progress }}%</span>
              </div>
              <p class="text-sm text-slate-300 mt-3">{{ progressStage }}</p>
              <p class="text-xs text-slate-400 mt-4">Sesja jest przetwarzana jednorazowo w pamięci operacyjnej.</p>
            </div>
          </div>

          <div v-if="step === 4" class="mt-6 space-y-6">
            <div>
              <h2 class="text-xl font-display font-semibold">Raport trendów</h2>
              <p class="text-sm text-slate-300 mt-2">
                Poniżej znajduje się automatycznie wygenerowany raport porównawczy.
              </p>
              <p v-if="aiProvider || aiModel || aiModelRequested || aiRegion || aiCountry" class="text-xs text-slate-400 mt-2">
                Źródło AI: <strong>{{ aiProvider || "google-ai" }}</strong>
                <span> · model wykonania: <strong>{{ aiModel || "brak danych" }}</strong></span>
                <span v-if="aiModelRequested && aiModelRequested !== aiModel">
                  · model żądany: <strong>{{ aiModelRequested }}</strong>
                </span>
                <span> · region: <strong>{{ aiRegionDisplay }}</strong></span>
                <span> · kraj: <strong>{{ aiCountryDisplay }}</strong></span>
              </p>
            </div>

            <div class="bg-slate-900/80 border border-slate-700 rounded-2xl p-5 overflow-auto">
              <div class="prose prose-invert max-w-none" v-html="reportHtml"></div>
            </div>

            <div class="bg-rose-500/10 border border-rose-400/40 rounded-xl p-4 text-sm text-rose-100">
              Treść wygenerowana automatycznie. Skonsultuj interpretację z lekarzem, szczególnie gdy normy
              są zależne od wieku, płci, stanu klinicznego lub laboratorium referencyjnego.
            </div>

            <details v-if="promptSent" class="bg-slate-800/60 border border-slate-700 rounded-xl">
              <summary class="px-5 py-3 cursor-pointer text-sm text-slate-300 hover:text-white">
                📋 Pokaż pełny prompt wysłany do AI
              </summary>
              <div class="px-5 pb-4">
                <p class="text-xs text-slate-400 mb-2">
                  Poniżej znajduje się dokładna treść zapytania wysłanego do modelu AI (po anonimizacji danych).
                  Pole jest nieedytowalne.
                </p>
                <textarea
                  readonly
                  :value="promptSent"
                  class="w-full h-96 px-4 py-3 rounded-lg bg-slate-900 border border-slate-600 text-slate-300 text-xs font-mono resize-y cursor-default"
                ></textarea>
              </div>
            </details>

            <div class="flex flex-wrap gap-3">
              <button
                class="px-5 py-3 rounded-xl bg-emerald-500/90 hover:bg-emerald-400 text-slate-900 font-semibold"
                @click="finalizeSession"
              >
                Zakończ sesję i usuń dane
              </button>
              <button
                class="px-5 py-3 rounded-xl border border-slate-600 text-slate-300"
                @click="step = 2"
              >
                Wróć do uploadu
              </button>
            </div>
          </div>

          <div v-if="step === 5" class="mt-6 space-y-6">
            <div>
              <h2 class="text-xl font-display font-semibold">✅ Sesja zakończona bezpiecznie</h2>
              <p class="text-sm text-slate-300 mt-2">
                Twoje pliki i dane zostały trwale usunięte z serwera. Sesja została zamknięta.
              </p>
            </div>

            <div class="bg-emerald-500/10 border border-emerald-400/40 rounded-2xl p-6 space-y-4">
              <div class="space-y-2 text-sm text-emerald-100/90">
                <p class="font-semibold">Informacja techniczna o analizie AI:</p>
                <ul class="list-disc list-inside space-y-1 pl-2">
                  <li>Dostawca AI: {{ aiProvider || "google-ai" }}</li>
                  <li>Model wykonania: {{ aiModel || "brak danych" }}</li>
                  <li v-if="aiModelRequested && aiModelRequested !== aiModel">Model żądany: {{ aiModelRequested }}</li>
                  <li>Region przetwarzania: {{ aiRegionDisplay }}</li>
                  <li>Kraj przetwarzania: {{ aiCountryDisplay }}</li>
                </ul>
                <p class="text-xs text-emerald-100/70 mt-2">
                  Dla ścisłej rezydencji danych (RODO/GDPR) zalecana jest konfiguracja Vertex AI
                  z jawnie wskazanym regionem.
                </p>
              </div>

              <div>
                <p class="text-emerald-100 font-semibold text-lg">🔒 Privacy by Design</p>
                <p class="text-sm text-emerald-100/80 mt-2">
                  Realizujemy zasadę minimalizacji retencji danych zgodnie z Art. 5 ust. 1 lit. e RODO.
                </p>
              </div>

              <div class="space-y-2 text-sm text-emerald-100/90">
                <p class="font-semibold">Co zostało trwale usunięte:</p>
                <ul class="list-disc list-inside space-y-1 pl-2">
                  <li>Pliki PDF z wynikami badań (przetwarzane tylko w RAM)</li>
                  <li>Wygenerowany raport AI (treść markdown)</li>
                  <li>Dane medyczne (wiek, płeć, waga - jeśli podane)</li>
                  <li>Wszystkie teksty wyodrębnione z dokumentów</li>
                </ul>
              </div>

              <div class="space-y-2 text-sm text-emerald-100/90">
                <p class="font-semibold">Co zostało zachowane (tylko dla audytu compliance):</p>
                <ul class="list-disc list-inside space-y-1 pl-2">
                  <li>ID sesji (UUID - nie zawiera danych osobowych)</li>
                  <li>Timestamp utworzenia</li>
                  <li>Informacja o udzielonych zgodach (TAK/NIE)</li>
                  <li>Status sesji: "deleted"</li>
                  <li>Wybrany poziom anonimizacji</li>
                </ul>
              </div>

              <div class="pt-3 border-t border-emerald-400/20">
                <p class="text-xs text-emerald-100/70">
                  <strong>Dlaczego tak robimy?</strong> Minimalizujemy ryzyko wycieku danych zdrowotnych
                  przez natychmiastowe usunięcie wszystkich wrażliwych informacji. Nie tworzymy kopii zapasowych.
                  Nie wykorzystujemy Twoich danych do trenowania modeli AI.
                </p>
              </div>
            </div>

            <button
              class="px-5 py-3 rounded-xl bg-glow-700 hover:bg-glow-500 text-white font-semibold"
              @click="resetFlow"
            >
              Rozpocznij nową analizę
            </button>
          </div>

          <div v-if="step === 6" class="mt-6 space-y-6">
            <div>
              <h2 class="text-xl font-display font-semibold">🔒 Panel Administracyjny - Zgody</h2>
              <p class="text-sm text-slate-300 mt-2">
                Wyświetlanie wszystkich zgód użytkowników wymaga uwierzytelnienia.
              </p>
            </div>

            <div v-if="!adminAuthenticated" class="space-y-4">
              <div class="bg-amber-500/10 border border-amber-400/40 rounded-xl p-4">
                <p class="text-sm text-amber-100">
                  Ten panel jest chroniony hasłem administracyjnym.
                </p>
              </div>

              <div class="space-y-3">
                <label class="block">
                  <span class="text-sm text-slate-300">Hasło administracyjne:</span>
                  <input
                    v-model="adminPassword"
                    type="password"
                    class="mt-2 w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-white"
                    @keyup.enter="authenticateAdmin"
                    placeholder="Wprowadź hasło"
                  />
                </label>
                <button
                  class="px-5 py-3 rounded-xl bg-glow-700 hover:bg-glow-500 text-white font-semibold"
                  @click="authenticateAdmin"
                  :disabled="!adminPassword || adminLoading"
                >
                  Zaloguj
                </button>
                <span v-if="adminError" class="text-sm text-rose-300">{{ adminError }}</span>
              </div>

              <button
                class="px-5 py-3 rounded-xl border border-slate-600 text-slate-300"
                @click="step = 1"
              >
                Powrót
              </button>
            </div>

            <div v-else class="space-y-4">
              <div class="bg-emerald-500/10 border border-emerald-400/40 rounded-xl p-4">
                <p class="text-sm text-emerald-100">
                  ✓ Uwierzytelniono. Wyświetlanie {{ filteredConsents.length }} z {{ consentRecords.length }} rekordów.
                </p>
              </div>

              <div class="space-y-3">
                <label class="block">
                  <span class="text-sm text-slate-300">🔍 Filtr (szukaj po ID, statusie, anonimizacji, client_id):</span>
                  <input
                    v-model="consentFilter"
                    type="text"
                    class="mt-2 w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-600 text-white"
                    placeholder="Wpisz tekst do filtrowania..."
                  />
                </label>
              </div>

              <div class="bg-slate-900/80 border border-slate-700 rounded-2xl p-5 overflow-auto max-h-[600px]">
                <table class="w-full text-sm text-left">
                  <thead class="text-xs uppercase bg-slate-800 text-slate-300">
                    <tr>
                      <th class="px-4 py-3">ID Sesji</th>
                      <th class="px-4 py-3">Data utworzenia</th>
                      <th class="px-4 py-3">Status</th>
                      <th class="px-4 py-3">Anonimizacja</th>
                      <th class="px-4 py-3">Zgoda: Regulamin</th>
                      <th class="px-4 py-3">Zgoda: Dane zdrowotne</th>
                      <th class="px-4 py-3">Zgoda: AI</th>
                      <th class="px-4 py-3">Client ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="record in filteredConsents"
                      :key="record.id"
                      class="border-b border-slate-700 hover:bg-slate-800/50"
                    >
                      <td class="px-4 py-3 font-mono text-xs">{{ record.id }}</td>
                      <td class="px-4 py-3">{{ formatDate(record.created_at) }}</td>
                      <td class="px-4 py-3">
                        <span :class="statusClass(record.status)" class="px-2 py-1 rounded text-xs">
                          {{ record.status }}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-center">
                        <span :class="anonymizationClass(record.anonymization_level)" class="px-2 py-1 rounded text-xs">
                          {{ record.anonymization_level === 'full' ? 'Pełna' : 'Medyczna' }}
                        </span>
                      </td>
                      <td class="px-4 py-3 text-center">{{ record.consent_terms ? '✅' : '❌' }}</td>
                      <td class="px-4 py-3 text-center">{{ record.consent_health_data ? '✅' : '❌' }}</td>
                      <td class="px-4 py-3 text-center">{{ record.consent_ai ? '✅' : '❌' }}</td>
                      <td class="px-4 py-3">{{ record.client_id || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
                <p v-if="filteredConsents.length === 0" class="text-center text-slate-400 py-8">
                  Brak wyników dla podanego filtra.
                </p>
              </div>

              <div class="flex gap-3">
                <button
                  class="px-5 py-3 rounded-xl bg-rose-500/90 hover:bg-rose-400 text-white font-semibold"
                  @click="logoutAdmin"
                >
                  Wyloguj
                </button>
                <button
                  class="px-5 py-3 rounded-xl border border-slate-600 text-slate-300"
                  @click="step = 1"
                >
                  Powrót
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import axios from "axios";
import { marked } from "marked";
import DOMPurify from "dompurify";

const apiBase = import.meta.env.VITE_API_URL || "http://localhost:9000";
const http = axios.create({
  baseURL: apiBase,
  withCredentials: true,
});

const accessChecked = ref(false);
const accessPasswordInput = ref("");
const accessError = ref("");
const accessLoading = ref(false);
const isAccessGranted = ref(false);

const step = ref(1);
const consentTerms = ref(false);
const consentHealth = ref(false);
const consentAi = ref(false);
const anonymizationLevel = ref("full"); // "full" or "medical"
const fileA = ref(null);
const fileB = ref(null);
const sessionId = ref(null);
const report = ref("");
const promptSent = ref("");
const aiProvider = ref("");
const aiModel = ref("");
const aiModelRequested = ref("");
const aiRegion = ref("");
const aiCountry = ref("");
const errorMessage = ref("");
const loading = ref(false);
const progress = ref(0);
const progressStage = ref("Oczekiwanie na rozpoczęcie analizy...");

// Medical data (for "medical" anonymization level)
const patientAge = ref("");
const patientGender = ref("");
const patientWeight = ref("");

// Admin panel state
const adminPassword = ref("");
const adminAuthenticated = ref(false);
const adminError = ref("");
const adminLoading = ref(false);
const consentRecords = ref([]);
const consentFilter = ref("");

const canStart = computed(() => consentTerms.value && consentHealth.value && consentAi.value);
const canAnalyze = computed(() => !!fileA.value && !!fileB.value);
const aiRegionDisplay = computed(() => {
  if (aiRegion.value) return aiRegion.value;
  if (aiProvider.value === "gemini") return "global";
  return "brak danych";
});
const aiCountryDisplay = computed(() => {
  if (aiCountry.value) return aiCountry.value;
  if (aiProvider.value === "gemini") return "nieokreślony (Gemini API global)";
  return "brak danych";
});

const reportHtml = computed(() => DOMPurify.sanitize(marked.parse(report.value || "")));

const filteredConsents = computed(() => {
  if (!consentFilter.value) return consentRecords.value;
  const filter = consentFilter.value.toLowerCase();
  return consentRecords.value.filter((record) => {
    return (
      record.id.toLowerCase().includes(filter) ||
      formatDate(record.created_at).toLowerCase().includes(filter) ||
      record.status.toLowerCase().includes(filter) ||
      record.anonymization_level.toLowerCase().includes(filter) ||
      String(record.consent_terms).toLowerCase().includes(filter) ||
      String(record.consent_health_data).toLowerCase().includes(filter) ||
      String(record.consent_ai).toLowerCase().includes(filter) ||
      (record.client_id && record.client_id.toLowerCase().includes(filter))
    );
  });
});

const stepClass = (value) => {
  if (step.value === value) return "px-3 py-1 rounded-full bg-glow-500/20 text-glow-500";
  if (step.value > value) return "px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-200";
  return "px-3 py-1 rounded-full bg-slate-800 text-slate-400";
};

const checkAccess = async () => {
  accessError.value = "";
  try {
    const resp = await http.get("/api/access/status");
    isAccessGranted.value = Boolean(resp.data?.authenticated);
  } catch (err) {
    if (err?.response?.status === 401) {
      isAccessGranted.value = false;
    } else {
      isAccessGranted.value = false;
    }
  } finally {
    accessChecked.value = true;
  }
};

onMounted(() => {
  checkAccess();
});

const authenticateAccess = async () => {
  accessError.value = "";
  if (!accessPasswordInput.value.trim()) {
    accessError.value = "Wpisz hasło dostępu.";
    return;
  }

  accessLoading.value = true;
  try {
    await http.post("/api/access/login", { password: accessPasswordInput.value.trim() });
    isAccessGranted.value = true;
    accessError.value = "";
  } catch (err) {
    if (err?.response?.status === 401) {
      accessError.value = "Nieprawidłowe hasło.";
    } else {
      accessError.value = "Nie udało się zalogować do warstwy dostępu.";
    }
  } finally {
    accessLoading.value = false;
  }
};

const startSession = async () => {
  errorMessage.value = "";
  loading.value = true;
  try {
    const resp = await http.post("/api/sessions", {
      consent_terms: consentTerms.value,
      consent_health_data: consentHealth.value,
      consent_ai: consentAi.value,
      anonymization_level: anonymizationLevel.value,
      client_id: "web",
    });
    sessionId.value = resp.data.id;
    step.value = 2;
  } catch (err) {
    errorMessage.value = "Nie udało się utworzyć sesji. Sprawdź backend.";
  } finally {
    loading.value = false;
  }
};

const onSelect = (event, target) => {
  const file = event.target.files?.[0];
  if (!file) return;
  if (target === "a") fileA.value = file;
  if (target === "b") fileB.value = file;
};

const onDrop = (event, target) => {
  const file = event.dataTransfer.files?.[0];
  if (!file) return;
  if (target === "a") fileA.value = file;
  if (target === "b") fileB.value = file;
};

const fetchSessionProgress = async () => {
  if (!sessionId.value) return;
  try {
    const resp = await http.get(`/api/sessions/${sessionId.value}/progress`);
    if (typeof resp.data.progress === "number") {
      progress.value = Math.max(0, Math.min(100, resp.data.progress));
    }
    if (resp.data.stage) {
      progressStage.value = resp.data.stage;
    }
  } catch (_err) {
    // Ignore transient polling errors
  }
};

const runAnalysis = async () => {
  if (!sessionId.value) {
    errorMessage.value = "Brak aktywnej sesji.";
    return;
  }
  errorMessage.value = "";
  report.value = "";
  promptSent.value = "";
  aiProvider.value = "";
  aiModel.value = "";
  aiModelRequested.value = "";
  aiRegion.value = "";
  aiCountry.value = "";
  loading.value = true;
  step.value = 3;
  progress.value = 0;
  progressStage.value = "Inicjalizacja analizy...";
  await fetchSessionProgress();
  const pollTimer = setInterval(fetchSessionProgress, 700);

  try {
    const form = new FormData();
    form.append("file_a", fileA.value);
    form.append("file_b", fileB.value);

    // Add medical data if "medical" anonymization level is selected
    if (anonymizationLevel.value === "medical") {
      if (patientAge.value) form.append("patient_age", patientAge.value.toString());
      if (patientGender.value) form.append("patient_gender", patientGender.value);
      if (patientWeight.value) form.append("patient_weight", patientWeight.value.toString());
    }

    const resp = await http.post(`/api/sessions/${sessionId.value}/compare`, form);
    if (resp.data.status !== "completed" || !resp.data.report_markdown) {
      throw new Error(resp.data.error_message || "Model AI nie zwrócił raportu.");
    }

    report.value = resp.data.report_markdown || "";
    promptSent.value = resp.data.prompt_sent || "";
    aiProvider.value = resp.data.ai_provider || "";
    aiModel.value = resp.data.ai_model || "";
    aiModelRequested.value = resp.data.ai_model_requested || "";
    aiRegion.value = resp.data.ai_region || "";
    aiCountry.value = resp.data.ai_country || "";
    progress.value = 100;
    progressStage.value = "Analiza zakończona";
    step.value = 4;
  } catch (err) {
    const backendMsg = err?.response?.data?.error_message || err?.message || "";
    errorMessage.value = backendMsg
      ? `Nie udało się wykonać analizy: ${backendMsg}`
      : "Nie udało się wykonać analizy. Spróbuj ponownie.";
    progressStage.value = "Analiza nieudana";
    step.value = 2;
  } finally {
    clearInterval(pollTimer);
    loading.value = false;
  }
};

const finalizeSession = async () => {
  if (!sessionId.value) {
    step.value = 5;
    return;
  }
  try {
    await http.post(`/api/sessions/${sessionId.value}/finalize`);
  } catch (err) {
    // Ignore finalize errors in UI
  }
  step.value = 5;
};

const resetFlow = () => {
  step.value = 1;
  consentTerms.value = false;
  consentHealth.value = false;
  consentAi.value = false;
  anonymizationLevel.value = "full";
  fileA.value = null;
  fileB.value = null;
  sessionId.value = null;
  report.value = "";
  promptSent.value = "";
  aiProvider.value = "";
  aiModel.value = "";
  aiModelRequested.value = "";
  aiRegion.value = "";
  aiCountry.value = "";
  errorMessage.value = "";
  progress.value = 0;
  progressStage.value = "Oczekiwanie na rozpoczęcie analizy...";
  patientAge.value = "";
  patientGender.value = "";
  patientWeight.value = "";
};

const goToAdminPanel = () => {
  step.value = 6;
};

const authenticateAdmin = async () => {
  adminError.value = "";
  adminLoading.value = true;
  try {
    const resp = await http.post("/api/admin/consents", {
      password: adminPassword.value,
    });
    consentRecords.value = resp.data;
    adminAuthenticated.value = true;
  } catch (err) {
    adminError.value = "Nieprawidłowe hasło lub błąd serwera.";
    adminAuthenticated.value = false;
  } finally {
    adminLoading.value = false;
  }
};

const logoutAdmin = () => {
  adminAuthenticated.value = false;
  adminPassword.value = "";
  consentRecords.value = [];
  consentFilter.value = "";
  adminError.value = "";
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString("pl-PL", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

const statusClass = (status) => {
  const classes = {
    created: "bg-blue-500/20 text-blue-200",
    processing: "bg-yellow-500/20 text-yellow-200",
    completed: "bg-emerald-500/20 text-emerald-200",
    failed: "bg-rose-500/20 text-rose-200",
    deleted: "bg-slate-500/20 text-slate-400",
  };
  return classes[status] || "bg-slate-500/20 text-slate-400";
};

const anonymizationClass = (level) => {
  return level === "full" ? "bg-purple-500/20 text-purple-200" : "bg-cyan-500/20 text-cyan-200";
};
</script>
