# Rezervarea de resurse:
[x] Server-ul gestioneaza o lista de resurse care pot fi alocate clientilor pentru un interval de timp;

[x] Clientul se autentifica prin nume si primeste lista resurselor impreuna cu lista rezervarilor pentru fiecare resursa;

[x] Un client poate solicita blocarea unei resurse pentru un interval de timp in vederea completarii unei rezervari;

[x] Server-ul notifica toti clientii autentificati in privinta blocarii resursei pentru rezervare, astfel incat un alt client sa nu mai poata solicita rezervarea aceleiasi resurse pentru acelasi interval de timp;

[x] Clientul care a initiat rezervarea poate anula solicitarea, caz in care server-ul notifica toti clientii ca resursa nu mai este blocata pe intervalul respectiv;

[ ] Clientul care a blocat resursa poate finaliza rezervarea, caz in care server-ul notifica toti clientii autentificati in privinta noii rezervari create;

[x] Un client poate actualiza datele de inceput si sfarsit pentru o rezervare facuta de el in prealabil, caz in care server-ul va notifica toti clientii autentificati in privinta schimbarii respective;

[x] Un client poate sterge o rezervare facuta de el in prealabil, caz in care server-ul va notifica toti clientii autentificati in privinta stergerii acesteia.
