clear all;

%% Daten laden
load('laufzeit_log_flur')

%% Haeufigkeiten ermitteln und Laufzeiten in ms umrechnen
[ h(:,2), h(:,1) ] = hist(laufzeit_log_flur, 1000);
h(:,1) = h(:,1)*1e3;

%% Logarithmischer Plot der Laufzeithaeufigkeiten
semilogx(h(:,1), h(:,2)); grid;
title('Histogramm der Signallaufzeiten, (Bluetooth-Echo)'); xlabel('Laufzeit / ms');
