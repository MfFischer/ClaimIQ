"""
ClaimIQ — Kfz Prompt Templates (German)
Tuned for German Kfz-Schadensmeldung documents.
Two-call approach: extraction first, scoring second.
"""

KFZ_EXTRACTION_PROMPT = """
Du bist ein erfahrener Kfz-Schadensachverständiger bei einem deutschen Versicherungsmakler.
Analysiere das folgende Schadensformular und extrahiere alle relevanten Daten strukturiert.

WICHTIG:
- Antworte NUR mit gültigem JSON — kein Text davor oder danach, keine Markdown-Backticks
- Wenn ein Feld nicht vorhanden ist, setze null
- Beträge als String mit Währungszeichen: "1.250,00 €"
- Datumsangaben im Format TT.MM.JJJJ
- Kennzeichen normalisiert: z.B. "M-AB 1234"

DOKUMENT:
{ocr_text}

JSON-Schema (gib alle Felder zurück, auch wenn null):
{{
  "schadennummer": null,
  "schadensdatum": null,
  "meldedatum": null,
  "kennzeichen": null,
  "fahrzeugmarke": null,
  "fahrzeugmodell": null,
  "fahrgestellnummer": null,
  "versicherungsnehmer": null,
  "geschaedigter": null,
  "kennzeichen_unfallgegner": null,
  "schadenshoehe": null,
  "selbstbeteiligung": null,
  "versicherungsscheinnummer": null,
  "versicherungsgesellschaft": null,
  "unfallort": null,
  "unfallhergang": null,
  "polizeilich_aufgenommen": null,
  "polizeibericht_nummer": null,
  "zusammenfassung_de": null,
  "zusammenfassung_en": null
}}

Für "zusammenfassung_de": Ein präziser Satz auf Deutsch der den Schaden beschreibt.
Für "zusammenfassung_en": Derselbe Satz auf Englisch.
"""


KFZ_SCORING_PROMPT = """
Du bist ein erfahrener Kfz-Schadensregulierer bei einem deutschen Versicherungsmakler.
Bewerte diesen Schadensfall auf seine Bearbeitungsreife.

EXTRAHIERTE DATEN:
{structured_data}

ROHER DOKUMENTTEXT (zur Plausibilitätsprüfung):
{ocr_text}

Antworte NUR mit gültigem JSON — kein Text davor oder danach:
{{
  "score_vollstaendigkeit": 0,
  "score_konsistenz": 0,
  "score_betrugshinweise": 0,
  "score_dokumentation": 0,
  "gesamtscore": 0,
  "empfehlung": "pruefen",
  "flags": [
    {{
      "field": "feldname",
      "message_de": "Hinweis auf Deutsch",
      "message": "Note in English",
      "severity": "error"
    }}
  ],
  "aktionsliste": [
    {{
      "item_de": "Was der Makler tun muss",
      "item": "What the broker must do",
      "required": true
    }}
  ]
}}

SCORING-REGELN:

score_vollstaendigkeit (0-100):
- 100: Alle Pflichtfelder vorhanden (schadensdatum, kennzeichen, versicherungsscheinnummer, schadenshoehe, unfallhergang)
- 80: 1 Pflichtfeld fehlt
- 60: 2 Pflichtfelder fehlen
- 40: 3 Pflichtfelder fehlen
- 20 und darunter: 4+ Pflichtfelder fehlen

score_konsistenz (0-100):
- 100: Alle Angaben stimmig
- Abzug -20: Meldedatum liegt VOR Schadendatum (unmöglich)
- Abzug -15: Kennzeichen nicht im deutschen Format (XX-XX 1234)
- Abzug -10: Schadenshöhe fehlt bei vorhandenem Unfallgegner-Kennzeichen

score_betrugshinweise (0-100, 100 = keine Auffälligkeiten):
- Abzug -30: Schadendatum = Policenabschlussdatum (häufigstes Betrugsindiz in DE)
- Abzug -20: Schadenshöhe exakt rund (z.B. 5000.00€, 10000.00€) ohne Gutachten
- Abzug -20: Meldung > 30 Tage nach Schadensdatum ohne Begründung
- Abzug -15: Schadenshöhe > 10.000€ ohne Polizeibericht

score_dokumentation (0-100):
- 100: Polizeibericht-Nr. + Fotos erwähnt + Gutachten bei Schaden > 2.000€
- 80: Polizeibericht vorhanden, Fotos fehlen
- 60: Kein Polizeibericht, Fotos erwähnt
- 40: Kein Polizeibericht, keine Fotos
- 20: Zusätzlich kein Gutachten bei Schaden > 2.000€

empfehlung:
- "annehmen": gesamtscore >= 75 und keine error-flags
- "ablehnen": gesamtscore < 40 oder fraud score < 50
- "pruefen": alle anderen Fälle

Erstelle flags und aktionsliste entsprechend der gefundenen Probleme.
"""
