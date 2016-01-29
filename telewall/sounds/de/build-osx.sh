#!/bin/bash
cd $(dirname "$0")

# run this on osx with installed german voices

say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=announcement_osx_anna.wav \
  "Guten Tag! Ich wünsche keinerlei Werbe-, Beratungs- und Umfrageanrufe und fordere Sie auf, diese Nummer aus ihren Listen und Datenbanken zu löschen! Der Anruf wird jetzt beendet!"

say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=record-announcement-instruction.wav \
  "Sie können jetzt Ihre eigene Ansage erstellen. Legen Sie den Hörer auf wenn Sie fertig sind. Die Aufnahme beginnt in 3, 2, 1,"

say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=mainmenu.wav \
  "Sie sind in der Konfiguration für Telewol. Drücken Sie 1 um die aktuelle Ansage anzuhören, 2 um eine eigene Ansage zu erstellen, 3 um die Standard-Ansage wiederherzustellen.  :"


say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=reset-announcement-confirm.wav \
  "Wenn Sie die Standard-Ansage wirklich wiederherstellen wollen, drücken Sie die Taste eins. Ansonsten können Sie auflegen. "

say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=reset-announcement-done.wav \
  "Die Standard-Ansage wurde wiederhergestell. "


say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=block-done.wav \
  "Die eingegebene Rufnummer wurde gesperrt."

say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=unblock-done.wav \
  "Die eingegebene Rufnummer wurde entsperrt."

say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=phonenumber-invalid.wav \
  "Die eingegebene Rufnummer ist ungültig. Bitte versuchen Sie es nochmal."


#say --voice=Anna --file-format=WAVE --data-format=LEI16@8000 --output-file=keine-werbung.wav "Guten Tag! Der Teilnehmer akzeptiert keine Werbeanrufe und keine Anrufe mit unterdrückter Rufnummer!  Der Anruf wird jetzt beendet!;;;"

# Alternative Texte:
# Der angerufene Teilnehmer akzeptiert keine Werbeanrufe, telefonischen Umfragen oder Anrufer mit unterdrückter Nummer.
# Der Teilnehmer akzeptiert keine Werbeanrufe und keine Anrufe mit unterdrückter Rufnummer!  Der Anruf wird jetzt beendet!
