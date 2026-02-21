/**
 * ClaimIQ — i18n translations (DE / EN)
 * German is primary. English is toggle option.
 */

export type Lang = 'de' | 'en'

export const translations = {
  de: {
    // App
    appName: 'ClaimIQ',
    appTagline: 'Vom Schaden zur Klarheit in Sekunden.',

    // Upload page
    uploadTitle: 'Schaden hochladen',
    uploadSubtitle: 'Kfz-Schadenformular hochladen — KI analysiert in Sekunden.',
    uploadDropzone: 'Datei hier ablegen oder klicken zum Auswählen',
    uploadDropzoneActive: 'Datei loslassen...',
    uploadFormats: 'PDF, JPG, PNG, TIFF — max. 10 MB',
    uploadButton: 'Schaden analysieren',
    uploadProcessing: 'Wird analysiert...',
    uploadHint: 'Kein Konto erforderlich. Ihre Daten werden nicht gespeichert.',

    // Processing
    processingTitle: 'Schaden wird analysiert...',
    processingStep1: 'Dokument wird eingelesen...',
    processingStep2: 'Texterkennung (OCR) läuft...',
    processingStep3: 'KI analysiert den Schaden...',
    processingStep4: 'Ergebnis wird erstellt...',

    // Results
    resultsTitle: 'Schadensanalyse',
    scoreLabel: 'Bearbeitungsreife',
    scoreSubtitle: 'Claim Readiness Score',
    summaryLabel: 'Zusammenfassung',
    extractedDataLabel: 'Extrahierte Daten',
    flagsLabel: 'Hinweise & Auffälligkeiten',
    checklistLabel: 'Aktionsliste für den Makler',
    suggestionLabel: 'Empfehlung',
    downloadPdf: 'Schadensübersicht herunterladen',
    newClaim: 'Neuen Schaden analysieren',
    feedbackButton: 'Etwas stimmt nicht?',

    // Score breakdown
    scoreCompleteness: 'Vollständigkeit',
    scoreConsistency: 'Konsistenz',
    scoreFraud: 'Betrugssignale',
    scoreDocs: 'Dokumentation',

    // Suggestions
    suggestionApprove: 'Annahme empfohlen',
    suggestionReview: 'Prüfung erforderlich',
    suggestionReject: 'Ablehnung empfohlen',

    // Fields
    fields: {
      schadennummer: 'Schadennummer',
      schadensdatum: 'Schadendatum',
      meldedatum: 'Meldedatum',
      kennzeichen: 'Kennzeichen',
      fahrzeugmarke: 'Fahrzeugmarke',
      fahrzeugmodell: 'Fahrzeugmodell',
      fahrgestellnummer: 'Fahrgestellnummer',
      versicherungsnehmer: 'Versicherungsnehmer',
      geschaedigter: 'Geschädigter',
      kennzeichen_unfallgegner: 'Kennzeichen Unfallgegner',
      schadenshoehe: 'Schadenshöhe',
      selbstbeteiligung: 'Selbstbeteiligung',
      versicherungsscheinnummer: 'Versicherungsscheinnummer',
      versicherungsgesellschaft: 'Versicherungsgesellschaft',
      unfallort: 'Unfallort',
      unfallhergang: 'Unfallhergang',
      polizeilich_aufgenommen: 'Polizeilich aufgenommen',
      polizeibericht_nummer: 'Polizeibericht-Nr.',
    },

    // Feedback modal
    feedbackTitle: 'Korrektur melden',
    feedbackField: 'Betroffenes Feld',
    feedbackOriginal: 'Extrahierter Wert',
    feedbackCorrected: 'Richtiger Wert',
    feedbackComment: 'Kommentar (optional)',
    feedbackSubmit: 'Absenden',
    feedbackCancel: 'Abbrechen',
    feedbackThanks: 'Vielen Dank für Ihr Feedback!',

    // Errors
    errorUpload: 'Fehler beim Hochladen. Bitte versuchen Sie es erneut.',
    errorProcessing: 'Fehler bei der Analyse. Bitte prüfen Sie die Bildqualität.',
    errorFiletype: 'Dateityp nicht unterstützt.',
    errorFilesize: 'Datei zu groß (max. 10 MB).',

    // Mock mode banner
    mockModeBanner: 'Demo-Modus aktiv — Beispieldaten werden angezeigt. Fügen Sie Ihren Gemini API-Key in .env ein, um echte Dokumente zu analysieren.',

    // OCR badge
    ocrTesseract: 'OCR: Tesseract',
    ocrVision: 'OCR: Google Vision',
  },

  en: {
    appName: 'ClaimIQ',
    appTagline: 'From claim to clarity in seconds.',

    uploadTitle: 'Upload Claim',
    uploadSubtitle: 'Upload a motor vehicle claim — AI analyses it in seconds.',
    uploadDropzone: 'Drop file here or click to select',
    uploadDropzoneActive: 'Release to upload...',
    uploadFormats: 'PDF, JPG, PNG, TIFF — max. 10 MB',
    uploadButton: 'Analyse Claim',
    uploadProcessing: 'Analysing...',
    uploadHint: 'No account required. Your data is not stored.',

    processingTitle: 'Analysing claim...',
    processingStep1: 'Reading document...',
    processingStep2: 'Running text recognition (OCR)...',
    processingStep3: 'AI is analysing the claim...',
    processingStep4: 'Building result...',

    resultsTitle: 'Claim Analysis',
    scoreLabel: 'Readiness',
    scoreSubtitle: 'Claim Readiness Score',
    summaryLabel: 'Summary',
    extractedDataLabel: 'Extracted Data',
    flagsLabel: 'Flags & Issues',
    checklistLabel: 'Broker Action List',
    suggestionLabel: 'Recommendation',
    downloadPdf: 'Download Claim Summary PDF',
    newClaim: 'Analyse New Claim',
    feedbackButton: 'Something looks wrong?',

    scoreCompleteness: 'Completeness',
    scoreConsistency: 'Consistency',
    scoreFraud: 'Fraud Signals',
    scoreDocs: 'Documentation',

    suggestionApprove: 'Approve recommended',
    suggestionReview: 'Review required',
    suggestionReject: 'Rejection recommended',

    fields: {
      schadennummer: 'Claim Number',
      schadensdatum: 'Incident Date',
      meldedatum: 'Report Date',
      kennzeichen: 'License Plate',
      fahrzeugmarke: 'Vehicle Make',
      fahrzeugmodell: 'Vehicle Model',
      fahrgestellnummer: 'VIN / Chassis No.',
      versicherungsnehmer: 'Policyholder',
      geschaedigter: 'Injured Party',
      kennzeichen_unfallgegner: 'Other Vehicle Plate',
      schadenshoehe: 'Claim Amount',
      selbstbeteiligung: 'Deductible',
      versicherungsscheinnummer: 'Policy Number',
      versicherungsgesellschaft: 'Insurance Company',
      unfallort: 'Location',
      unfallhergang: 'Incident Description',
      polizeilich_aufgenommen: 'Police Report Filed',
      polizeibericht_nummer: 'Police Report No.',
    },

    feedbackTitle: 'Report Correction',
    feedbackField: 'Affected Field',
    feedbackOriginal: 'Extracted Value',
    feedbackCorrected: 'Correct Value',
    feedbackComment: 'Comment (optional)',
    feedbackSubmit: 'Submit',
    feedbackCancel: 'Cancel',
    feedbackThanks: 'Thank you for your feedback!',

    errorUpload: 'Upload failed. Please try again.',
    errorProcessing: 'Analysis failed. Please check the document image quality.',
    errorFiletype: 'File type not supported.',
    errorFilesize: 'File too large (max. 10 MB).',

    mockModeBanner: 'Demo mode active — showing sample data. Add your Gemini API key to .env to analyse real documents.',

    ocrTesseract: 'OCR: Tesseract',
    ocrVision: 'OCR: Google Vision',
  },
} as const

export type TranslationKey = keyof typeof translations.de
